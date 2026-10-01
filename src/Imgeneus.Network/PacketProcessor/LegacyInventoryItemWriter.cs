using System;
using System.Collections.Generic;

namespace Imgeneus.Network.PacketProcessor
{
    /// <summary>
    /// The 34-byte item record read by the Rebirth Evolution EP4.5 client.
    /// </summary>
    public static class LegacyInventoryItemWriter
    {
        public const int RecordSize = 34;

        public static void Write(ImgeneusPacket packet, byte bag, byte slot, byte type,
            byte typeId, ushort quality, IReadOnlyList<int> gems, byte count, string craftName)
        {
            // The client indexes six bags with 24 slots without bounds checking.
            if (bag >= 6 || slot >= 24)
                throw new ArgumentOutOfRangeException(nameof(slot), "EP4.5 inventory coordinates exceed client capacity.");
            if (gems.Count != 6)
                throw new ArgumentException("Exactly six gem identifiers are required.", nameof(gems));

            var gemBytes = new byte[6];
            for (var i = 0; i < gemBytes.Length; i++)
                gemBytes[i] = checked((byte)gems[i]);

            packet.Write(bag);
            packet.Write(slot);
            packet.Write(type);
            packet.Write(typeId);
            packet.Write(quality);
            packet.Write(gemBytes);
            packet.Write(count);
            packet.WriteString(craftName, 21);
        }
    }
}
