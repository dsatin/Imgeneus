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
