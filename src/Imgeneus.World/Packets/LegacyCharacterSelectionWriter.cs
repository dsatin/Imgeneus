using Imgeneus.Database.Entities;
using Imgeneus.Network.PacketProcessor;
using System.Linq;

namespace Imgeneus.World.Packets
{
    public static class LegacyCharacterSelectionWriter
    {
        // EP4.5 game.exe: 0x57C790 reads eight equipment types/IDs,
        // followed by a 19-byte name and the delete/rename flags.
        public static void Write(ImgeneusPacket packet, DbCharacter character)
        {
            packet.Write(character.Id);
            packet.Write(0); // Creation date, unused by this server.
            packet.Write(character.Level);
            packet.Write((byte)character.Race);
            packet.Write((byte)character.Mode);
            packet.Write(character.Hair);
            packet.Write(character.Face);
            packet.Write(character.Height);
            packet.Write((byte)character.Class);
            packet.Write((byte)character.Gender);
            packet.Write(character.Map);
            packet.Write(character.Strength);
            packet.Write(character.Dexterity);
            packet.Write(character.Rec);
            packet.Write(character.Intelligence);
            packet.Write(character.Wisdom);
            packet.Write(character.Luck);
            packet.Write((ushort)character.HealthPoints);
            packet.Write((ushort)character.ManaPoints);
            packet.Write((ushort)character.StaminaPoints);

            var types = new byte[8];
            var ids = new byte[8];
            foreach (var item in character.Items.Where(item => item.Bag == 0 && item.Slot < 8))
            {
                types[item.Slot] = item.Type;
                ids[item.Slot] = item.TypeId;
            }
            packet.Write(types);
            packet.Write(ids);
            packet.WriteString(character.Name, 19);
            packet.Write(character.IsDelete);
            packet.Write(character.IsRename);
            if (types[7] != 0)
                packet.Write(new byte[6]); // Cloak customization.
        }
    }
}
