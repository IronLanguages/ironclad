using System;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Runtime.Exceptions;

namespace Ironclad
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


    public class ObjectArgWriter : ArgWriter
    {
        private Python25Mapper mapper;

        public ObjectArgWriter(int startIndex, Python25Mapper mapper) : base(startIndex)
        {
            this.mapper = mapper;
        }

        public override void Write(IntPtr ptrTable, object objValue)
        {
            IntPtr objPtr = this.mapper.Store(objValue);
            this.mapper.RememberTempObject(objPtr);
            IntPtr addressToRead = CPyMarshal.Offset(ptrTable, this.startIndex * CPyMarshal.PtrSize);
            IntPtr addressToWrite = CPyMarshal.ReadPtr(addressToRead);
            CPyMarshal.WritePtr(addressToWrite, objPtr);
        }

        public override int PointersConsumed
        {
            get
            {
                return 1;
            }
        }
    }


    public class StringArgWriter : ArgWriter
    {
        protected Python25Mapper mapper;
        
        protected StringArgWriter(int startIndex, Python25Mapper mapper) : base(startIndex)
        {
            this.mapper = mapper;
        }
    
        protected IntPtr SetupStringPtr(IntPtr ptrTable, string value)
        {
            IntPtr addressToRead = CPyMarshal.Offset(ptrTable, this.startIndex * CPyMarshal.PtrSize);
            IntPtr addressToWrite = CPyMarshal.ReadPtr(addressToRead);
            
            IntPtr storage = Marshal.AllocHGlobal(value.Length + 1);
            CPyMarshal.WritePtr(addressToWrite, storage);
            this.mapper.RememberTempPtr(storage);
            return storage;
        }
    }


    public class CStringArgWriter : StringArgWriter
    {
        public CStringArgWriter(int startIndex, Python25Mapper mapper) : base(startIndex, mapper)
        {
        }

        public override void Write(IntPtr ptrTable, object strValue)
        {
            string value = (string)strValue;
            IntPtr storage = this.SetupStringPtr(ptrTable, value);
            
            foreach (char c in value)
            {
                byte b = (byte)c;
                if ((char)b != c)
                {
                    throw new PythonUnicodeErrorException("Failed to convert string");
                }
                if (b == 0)
                {
                    throw new ArgumentTypeException("Failed to convert string: embedded NULL");
                }
                CPyMarshal.WriteByte(storage, b);
                storage = CPyMarshal.Offset(storage, 1);
            }
            CPyMarshal.WriteByte(storage, 0);
        }

        public override int PointersConsumed
        {
            get
            {
                return 1;
            }
        }
    }


    public class SizedStringArgWriter : StringArgWriter
    {
        private int sizeIndex;
        public SizedStringArgWriter(int startIndex, Python25Mapper mapper) : base(startIndex, mapper)
        {
            this.sizeIndex = startIndex + 1;
        }

        public override void Write(IntPtr ptrTable, object strValue)
        {
            string value = (string)strValue;
            IntPtr storage = this.SetupStringPtr(ptrTable, value);
            
            foreach (char c in value)
            {
                byte b = (byte)c;
                if ((char)b != c)
                {
                    throw new PythonUnicodeErrorException("Failed to convert string");
                }
                CPyMarshal.WriteByte(storage, b);
                storage = CPyMarshal.Offset(storage, 1);
            }
            CPyMarshal.WriteByte(storage, 0);

            IntPtr addressToRead = CPyMarshal.Offset(ptrTable, this.sizeIndex * CPyMarshal.PtrSize);
            IntPtr addressToWrite = CPyMarshal.ReadPtr(addressToRead);
            CPyMarshal.WriteInt(addressToWrite, value.Length);
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