using System;
using System.Runtime.InteropServices;

namespace JumPy
{
	public class CPyMarshal
	{
		public const int PtrSize = 4;
		public const int IntSize = 4;

        public static IntPtr Offset(IntPtr start, Int32 offset)
        {
            return (IntPtr)(start.ToInt32() + offset);
        }

        public static IntPtr Offset(IntPtr start, IntPtr offset)
        {
            return (IntPtr)(start.ToInt32() + offset.ToInt32());
        }
		
		public static void WritePtr(IntPtr address, IntPtr value)
		{
			Marshal.WriteIntPtr(address, value);
		}
		
		public static IntPtr ReadPtr(IntPtr address)
		{
			return Marshal.ReadIntPtr(address);
		}
		
		public static void WriteInt(IntPtr address, int value)
		{
			Marshal.WriteInt32(address, value);
		}
		
		public static int ReadInt(IntPtr address)
		{
			return Marshal.ReadInt32(address);
		}
		
		public static void WriteUInt(IntPtr address, uint value)
		{
			Marshal.WriteInt32(address, (int)value);
		}
		
		public static uint ReadUInt(IntPtr address)
		{
			return (uint)Marshal.ReadInt32(address);
		}
		
		public static void WriteByte(IntPtr address, byte value)
		{
			Marshal.WriteByte(address, value);
		}
		
		public static byte ReadByte(IntPtr address)
		{
			return Marshal.ReadByte(address);
		}
	}
}
