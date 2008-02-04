using System;
using System.Runtime.InteropServices;
using System.Text;

namespace JumPy
{
    public class ArgWriter
    {
        protected int startIndex;

        public ArgWriter(int startIndex)
        {
            this.startIndex = startIndex;
        }

        public static IntPtr Offset(IntPtr start, Int32 offset)
        {
            return (IntPtr)(start.ToInt32() + offset);
        }

        public virtual int PointersConsumed
        {
            get
            {
                Console.WriteLine("ArgWriter.PointersConsumed");
                throw new NotImplementedException();
            }
        }

        public int NextWriterStartIndex
        {
            get
            {
                return this.startIndex + this.PointersConsumed;
            }
        }
        
        public virtual void Write(IntPtr ptrTable, object value)
        {
            Console.WriteLine("ArgWriter.Write");
            throw new NotImplementedException();
        }
    }

    public class IntArgWriter : ArgWriter
    {
        public IntArgWriter(int startIndex) : base(startIndex)
        {
        }

        public override void Write(IntPtr ptrTable, object intValue)
        {
            int value = (int)intValue;
            IntPtr addressToRead = ArgWriter.Offset(ptrTable, this.startIndex * Marshal.SizeOf(typeof(IntPtr)));
            IntPtr addressToWrite = Marshal.ReadIntPtr(addressToRead);
            Marshal.WriteInt32(addressToWrite, value);
        }

        public override int PointersConsumed
        {
            get
            {
                return 1;
            }
        }
    }



    public class SizedStringArgWriter : ArgWriter
    {
        private Python25Mapper mapper;

        public SizedStringArgWriter(int startIndex, Python25Mapper mapper) : base(startIndex)
        {
            this.mapper = mapper;
        }

        public override void Write(IntPtr ptrTable, object strValue)
        {
            string value = (string)strValue;
            IntPtr addressToRead = ArgWriter.Offset(ptrTable, this.startIndex * Marshal.SizeOf(typeof(IntPtr)));
            IntPtr addressToWrite = Marshal.ReadIntPtr(addressToRead);
            
            byte[] bytes = Encoding.UTF8.GetBytes(value);
            int byteCount = Encoding.UTF8.GetByteCount(value);
            IntPtr storage = Marshal.AllocHGlobal(byteCount + 1);
            Marshal.WriteIntPtr(addressToWrite, storage);
            this.mapper.RememberTempPtr(storage);
            
            foreach (byte b in bytes)
            {
                Marshal.WriteByte(storage, b);
                storage = ArgWriter.Offset(storage, 1);
            }
            Marshal.WriteByte(storage, 0);

            addressToRead = ArgWriter.Offset(addressToRead, Marshal.SizeOf(typeof(IntPtr)));
            addressToWrite = Marshal.ReadIntPtr(addressToRead);
            Marshal.WriteInt32(addressToWrite, byteCount);
        }

        public override int PointersConsumed
        {
            get
            {
                return 2;
            }
        }
    }




}