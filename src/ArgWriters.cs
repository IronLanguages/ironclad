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
            IntPtr addressToRead = CPyMarshal.Offset(ptrTable, this.startIndex * CPyMarshal.PtrSize);
            IntPtr addressToWrite = CPyMarshal.ReadPtr(addressToRead);
            CPyMarshal.WriteInt(addressToWrite, value);
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
            IntPtr addressToRead = CPyMarshal.Offset(ptrTable, this.startIndex * CPyMarshal.PtrSize);
            IntPtr addressToWrite = CPyMarshal.ReadPtr(addressToRead);
            
            int byteCount = value.Length;
            IntPtr storage = Marshal.AllocHGlobal(byteCount + 1);
            CPyMarshal.WritePtr(addressToWrite, storage);
            this.mapper.RememberTempPtr(storage);
            
            foreach (char c in value)
            {
                CPyMarshal.WriteByte(storage, (byte)c);
                storage = CPyMarshal.Offset(storage, 1);
            }
            CPyMarshal.WriteByte(storage, 0);

            addressToRead = CPyMarshal.Offset(addressToRead, CPyMarshal.PtrSize);
            addressToWrite = CPyMarshal.ReadPtr(addressToRead);
            CPyMarshal.WriteInt(addressToWrite, byteCount);
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