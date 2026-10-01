using System.Buffers.Binary;
using System.Net.Sockets;
using System.Numerics;
using Imgeneus.Network.PacketProcessor;
using Imgeneus.Network.Packets;
using Imgeneus.Network.Packets.Login;
using Imgeneus.Network.Server.Crypto;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Sylver.HandlerInvoker;
using Sylver.HandlerInvoker.Attributes;
using Sylver.HandlerInvoker.Exceptions;

if (args.Length == 3 && args[0] == "--login")
{
    await CheckLoginAsync(args[1], int.Parse(args[2]));
    return;
}

using var host = new HostBuilder().ConfigureServices(services =>
{
    services.AddScoped<ScopeProbe>();
    services.AddHandlers();
}).Build().AddHandlerParameterTransformer<RawPacket, IParsedPacket>((raw, parsed) =>
{
    parsed.Value = raw.Value;
    return parsed;
});
var invoker = host.Services.GetRequiredService<IHandlerInvoker>();
using var firstScope = host.Services.CreateScope();
using var secondScope = host.Services.CreateScope();
var first = firstScope.ServiceProvider.GetRequiredService<ScopeProbe>();
var second = secondScope.ServiceProvider.GetRequiredService<ScopeProbe>();

await invoker.InvokeAsync(firstScope, Operation.Sync, new RawPacket(42));
Check(first.Value == 49 && first.Released == 1, "Sync dispatch, transformation and optional parameter");
Check(second.Value == 0 && second.Released == 0, "Client scopes remain isolated");

var pending = invoker.InvokeAsync(secondScope, Operation.Async, new RawPacket(12));
Check(!pending.IsCompleted && second.Released == 0, "Async handler remains alive while awaiting");
second.Gate.SetResult();
await pending;
Check(second.Value == 12 && second.Released == 1, "Task<T> completes before disposal");

try
{
    await invoker.InvokeAsync(firstScope, Operation.Failure);
    throw new Exception("Expected async failure was swallowed");
}
catch (InvalidOperationException ex) when (ex.Message == "Expected handler failure") { }
Check(first.Released == 2, "Async failure propagates and releases the handler");

try
{
    await invoker.InvokeAsync(firstScope, "missing-action");
    throw new Exception("Expected missing handler failure");
}
catch (HandlerActionNotFoundException) { }
await invoker.InvokeAsync(Operation.Sync, new RawPacket(1));
Console.WriteLine("PASS: scoped sync/async dispatch, packet transformation, lifetime and exceptions");
CheckLegacyInventory();
CheckLegacySelection();
using (var disconnected = new DisconnectedClient(host.Services))
{
    using var packet = new ImgeneusPacket(PacketType.QUIT_GAME);
    disconnected.Send(packet);
    var closedSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
    disconnected.AttachSocket(closedSocket);
    closedSocket.Dispose();
    disconnected.Send(packet);
    disconnected.Dispose();
    disconnected.Send(packet);
}
Console.WriteLine("PASS: packets are skipped before connection and after socket/sender disposal");

static void CheckLegacySelection()
{
    var character = new Imgeneus.Database.Entities.DbCharacter
    {
        Id = 42, Name = "TestEP45", Level = 7, IsRename = true,
        Items = new List<Imgeneus.Database.Entities.DbCharacterItems>()
    };
    using var packet = new ImgeneusPacket(PacketType.CHARACTER_LIST);
    packet.Write((byte)2);
    Imgeneus.World.Packets.LegacyCharacterSelectionWriter.Write(packet, character);
    var bytes = packet.Buffer;
    Check(bytes.Length == 79, "EP4.5 character selection frame length");
    Check(bytes[4] == 2 && BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(5)) == 42,
        "EP4.5 character slot and identifier");
    Check(System.Text.Encoding.UTF8.GetString(bytes, 58, 8) == "TestEP45",
        "EP4.5 character name offset");
    Check(bytes[77] == 0 && bytes[78] == 1, "EP4.5 delete/rename flag offsets");
    Console.WriteLine("PASS: EP4.5 character selection wire format");
}

static void CheckLegacyInventory()
{
    using var packet = new ImgeneusPacket(PacketType.CHARACTER_ITEMS);
    packet.Write((byte)1);
    LegacyInventoryItemWriter.Write(packet, 2, 23, 13, 54, 513,
        new[] { 1, 2, 3, 4, 5, 6 }, 9, "01020304050607080910");
    var frame = packet.Buffer;
    Check(frame.Length == 39 && BinaryPrimitives.ReadUInt16LittleEndian(frame) == 39,
        "EP4.5 frame consists of header, opcode, count and one 34-byte record");
    Check(frame[5..18].SequenceEqual(Convert.FromHexString("02170D36010201020304050609")),
        "EP4.5 item order, little-endian quality, byte gems and count");
    Check(System.Text.Encoding.ASCII.GetString(frame[18..38]) == "01020304050607080910" && frame[38] == 0,
        "EP4.5 craft name is 21 bytes including its terminator");

    using var invalid = new ImgeneusPacket(PacketType.CHARACTER_ITEMS);
    try
    {
        LegacyInventoryItemWriter.Write(invalid, 6, 0, 1, 1, 0, new int[6], 1, "");
        throw new Exception("Invalid bag was accepted");
    }
    catch (ArgumentOutOfRangeException) { }
    Check(invalid.Length == 4, "Invalid inventory coordinates are rejected before writing");
    try
    {
        LegacyInventoryItemWriter.Write(invalid, 0, 0, 1, 1, 0, new[] { 256, 0, 0, 0, 0, 0 }, 1, "");
        throw new Exception("Unrepresentable gem was accepted");
    }
    catch (OverflowException) { }
    Check(invalid.Length == 4, "Oversized gem identifiers cannot shift or corrupt item records");
    Console.WriteLine("PASS: EP4.5 inventory wire format and client array bounds");
}

static void Check(bool condition, string message)
{
    if (!condition) throw new Exception("FAIL: " + message);
}

static async Task CheckLoginAsync(string hostname, int port)
{
    using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(15));
    using var socket = new TcpClient();
    await socket.ConnectAsync(hostname, port, timeout.Token);
    using var stream = socket.GetStream();
    var greeting = await ReadFrameAsync(stream, timeout.Token);
    Check(BinaryPrimitives.ReadUInt16LittleEndian(greeting) == (ushort)PacketType.LOGIN_HANDSHAKE,
        "Server greeting opcode");

    // RSA(1) is 1 for the advertised key; this initializes a deterministic test session.
    using var handshake = new ImgeneusPacket(PacketType.LOGIN_HANDSHAKE);
    handshake.Write((byte)128);
    var encryptedNumber = new byte[128];
    encryptedNumber[0] = 1;
    handshake.Write(encryptedNumber);
    await stream.WriteAsync(handshake.Buffer, timeout.Token);

    var crypto = new CryptoManager();
    crypto.GenerateAES(BigInteger.One);
    using var request = new ImgeneusPacket(PacketType.LOGIN_REQUEST);
    request.WriteString("_probe_missing_", 19);
    request.WriteString("", 13);
    request.WriteString("irrelevant", 16);
    var bytes = request.Buffer;
    crypto.Encrypt(bytes[2..]).CopyTo(bytes, 2);
    await stream.WriteAsync(bytes, timeout.Token);

    var response = crypto.Decrypt(await ReadFrameAsync(stream, timeout.Token));
    Check(BinaryPrimitives.ReadUInt16LittleEndian(response) == (ushort)PacketType.LOGIN_REQUEST,
        "Encrypted login response opcode");
    Check(response[2] == (byte)AuthenticationResult.ACCOUNT_DONT_EXIST,
        "Expected nonexistent-account response without creating or updating accounts");
    Console.WriteLine("PASS: TCP -> RSA handshake -> AES -> scoped authentication -> encrypted response");
}

static async Task<byte[]> ReadFrameAsync(NetworkStream stream, CancellationToken cancellation)
{
    var header = new byte[2];
    await stream.ReadExactlyAsync(header, cancellation);
    var length = BinaryPrimitives.ReadUInt16LittleEndian(header);
    Check(length >= 4 && length <= 4096, "Valid frame size");
    var content = new byte[length - 2];
    await stream.ReadExactlyAsync(content, cancellation);
    return content;
}

public enum Operation { Sync, Async, Failure }

public sealed class DisconnectedClient : Imgeneus.Network.Client.ImgeneusClient
{
    private bool _scopeReleased;
    public DisconnectedClient(IServiceProvider services) : base(
        Microsoft.Extensions.Logging.Abstractions.NullLogger<Imgeneus.Network.Client.ImgeneusClient>.Instance,
        new CryptoManager(), services) { }
    public override PacketType[] ExcludedPackets => Array.Empty<PacketType>();
    public override Task InvokePacketAsync(PacketType type, LiteNetwork.Protocol.Abstractions.ILitePacketStream packet)
        => Task.CompletedTask;
    public void AttachSocket(Socket socket) => typeof(LiteNetwork.Server.LiteServerUser)
        .GetProperty(nameof(Socket))!.SetValue(this, socket);
    public override void Dispose()
    {
        base.Dispose();
        if (!_scopeReleased)
        {
            _scope.Dispose();
            _scopeReleased = true;
        }
    }
}
public record RawPacket(int Value);
public interface IParsedPacket { int Value { get; set; } }
public class ParsedPacket : IParsedPacket { public int Value { get; set; } }
public sealed class ScopeProbe
{
    public int Value;
    public int Released;
    public TaskCompletionSource Gate = new(TaskCreationOptions.RunContinuationsAsynchronously);
}

[Handler]
public sealed class TestHandler : IDisposable
{
    private readonly ScopeProbe _probe;
    public TestHandler(ScopeProbe probe) => _probe = probe;

    [HandlerAction(Operation.Sync)]
    public void Sync(ParsedPacket packet, int extra = 7) => _probe.Value = packet.Value + extra;

    [HandlerAction(Operation.Async)]
    public async Task<int> Async(ParsedPacket packet)
    {
        await _probe.Gate.Task;
        if (_probe.Released != 0) throw new Exception("Handler was disposed before await completed");
        _probe.Value = packet.Value;
        return packet.Value;
    }

    [HandlerAction(Operation.Failure)]
    public async Task Failure()
    {
        await Task.Yield();
        throw new InvalidOperationException("Expected handler failure");
    }

    public void Dispose() => _probe.Released++;
}
