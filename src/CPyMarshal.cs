using System;
using System.Runtime.InteropServices;

namespace Ironclad
{
    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    public struct DoubleStruct
    {
        public double value;

        public DoubleStruct(double inValue)
        {
            this.value = inValue;
        }
    }

    public class CPyMarshal
    {
        public const int PtrSize = 4;
        public const int IntSize = 4;
        public const int DoubleSize = 8;

        public static void Zero(IntPtr start, Int32 bytes)
        {
            for (int i = 0; i < bytes/CPyMarshal.IntSize; i++)
            {
                CPyMarshal.WriteInt(start, 0);
                start = CPyMarshal.Offset(start, CPyMarshal.IntSize);
            }
        }

        private static IntPtr GetField(IntPtr addr, Type type, string field)
        {
            return CPyMarshal.Offset(addr, Marshal.OffsetOf(type, field));
        }

        public static void WritePtrField(IntPtr addr, Type type, string field, IntPtr data)
        {
            IntPtr writeAddr = CPyMarshal.GetField(addr, type, field);
            CPyMarshal.WritePtr(writeAddr, data);
        }

        public static IntPtr ReadPtrField(IntPtr addr, Type type, string field)
        {
            IntPtr readAddr = CPyMarshal.GetField(addr, type, field);
            return CPyMarshal.ReadPtr(readAddr);
        }

        public static void WriteIntField(IntPtr addr, Type type, string field, int data)
        {
            IntPtr writeAddr = CPyMarshal.GetField(addr, type, field);
            CPyMarshal.WriteInt(writeAddr, data);
        }

        public static int ReadIntField(IntPtr addr, Type type, string field)
        {
            IntPtr readAddr = CPyMarshal.GetField(addr, type, field);
            return CPyMarshal.ReadInt(readAddr);
        }

        public static void WriteDoubleField(IntPtr addr, Type type, string field, double data)
        {
            IntPtr writeAddr = CPyMarshal.GetField(addr, type, field);
            CPyMarshal.WriteDouble(writeAddr, data);
        }

        public static double ReadDoubleField(IntPtr addr, Type type, string field)
        {
            IntPtr readAddr = CPyMarshal.GetField(addr, type, field);
            return CPyMarshal.ReadDouble(readAddr);
        }
        
        public static string ReadCStringField(IntPtr addr, Type type, string field)
        {
            IntPtr strPtrAddr = CPyMarshal.GetField(addr, type, field);
            IntPtr readAddr = CPyMarshal.ReadPtr(strPtrAddr);
            if (readAddr != IntPtr.Zero)
            {
                return Marshal.PtrToStringAnsi(readAddr);
            }
            return "";
        }
        
        public static void WriteFunctionPtrField(IntPtr addr, Type type, string field, Delegate dgt)
        {
            IntPtr writeAddr = CPyMarshal.GetField(addr, type, field);
            CPyMarshal.WritePtr(writeAddr, Marshal.GetFunctionPointerForDelegate(dgt));
        }


        public static Delegate ReadFunctionPtrField(IntPtr addr, Type type, string field, Type dgtType)
        {
            IntPtr readAddr = CPyMarshal.GetField(addr, type, field);
            IntPtr funcPtr = CPyMarshal.ReadPtr(readAddr);
            return Marshal.GetDelegateForFunctionPointer(funcPtr, dgtType);
        }


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

        public static void WriteDouble(IntPtr address, double value)
        {
            DoubleStruct ds = new DoubleStruct(value);
            Marshal.StructureToPtr(ds, address, false);
        }

        public static double ReadDouble(IntPtr address)
        {
            DoubleStruct ds = (DoubleStruct)Marshal.PtrToStructure(address, typeof(DoubleStruct));
            return ds.value;
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
