using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Hosting;

using Ironclad.Structs;

namespace Ironclad
{
    public interface IAllocator
    {
        IntPtr Alloc(int bytes);
        IntPtr Realloc(IntPtr old, int bytes);
        void Free(IntPtr address);
    }
    
    public class HGlobalAllocator : IAllocator
    {
        public IntPtr 
        Alloc(int bytes)
        {
            return Marshal.AllocHGlobal(bytes);
        }
        public IntPtr
        Realloc(IntPtr old, int bytes)
        {
            return Marshal.ReAllocHGlobal(old, (IntPtr)bytes);
        }
        public void 
        Free(IntPtr address)
        {
            Marshal.FreeHGlobal(address);
        }
    }

    public enum UnmanagedDataMarker
    {
        PyStringObject,
    }


    public partial class Python25Mapper : PythonMapper
    {
        private PythonEngine engine;
        private Dictionary<IntPtr, object> ptrmap;
        private List<IntPtr> tempPtrs;
        private List<IntPtr> tempObjects;
        private IAllocator allocator;
        private Exception _lastException;
        
        public Python25Mapper(PythonEngine eng): this(eng, new HGlobalAllocator())
        {            
        }
        
        public Python25Mapper(PythonEngine eng, IAllocator alloc)
        {
            this.engine = eng;
            this.allocator = alloc;
            this.ptrmap = new Dictionary<IntPtr, object>();
            this.tempPtrs = new List<IntPtr>();
            this.tempObjects = new List<IntPtr>();
            this._lastException = null;
        }
        
        public IntPtr 
        Store(object obj)
        {
            IntPtr ptr = this.allocator.Alloc(CPyMarshal.IntSize);
            CPyMarshal.WriteInt(ptr, 1);
            this.ptrmap[ptr] = obj;
            return ptr;
        }
        
        public void
        StoreUnmanagedData(IntPtr ptr, object obj)
        {
            this.ptrmap[ptr] = obj;
        }
        
        private static char
        CharFromByte(byte b)
        {
            return (char)b;
        }
        
        public object 
        Retrieve(IntPtr ptr)
        {
            object possibleMarker = this.ptrmap[ptr];
            if (possibleMarker.GetType() == typeof(UnmanagedDataMarker))
            {
                UnmanagedDataMarker marker = (UnmanagedDataMarker)possibleMarker;
                switch (marker)
                {
                    case UnmanagedDataMarker.PyStringObject:
                        IntPtr buffer = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
                        IntPtr lengthPtr = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
                        int length = CPyMarshal.ReadInt(lengthPtr);
                        
                        byte[] bytes = new byte[length];
                        Marshal.Copy(buffer, bytes, 0, length);
                        char[] chars = Array.ConvertAll<byte, char>(
                            bytes, new Converter<byte, char>(CharFromByte));
                        this.ptrmap[ptr] = new string(chars);
                        break;
                    
                    default:
                        throw new Exception("Found impossible data in pointer map");
                }
            }
            return this.ptrmap[ptr];
        }
        
        public int 
        RefCount(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                return CPyMarshal.ReadInt(ptr);
            }
            else
            {
                return 0;
            }
        }
        
        public void 
        IncRef(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                int count = CPyMarshal.ReadInt(ptr);
                CPyMarshal.WriteInt(ptr, count + 1);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void 
        DecRef(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                int count = CPyMarshal.ReadInt(ptr);
                if (count == 1)
                {
                    this.Delete(ptr);
                }
                else
                {
                    CPyMarshal.WriteInt(ptr, count - 1);
                }
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void 
        Delete(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                this.ptrmap.Remove(ptr);
                this.allocator.Free(ptr);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }

        public void RememberTempPtr(IntPtr ptr)
        {
            this.tempPtrs.Add(ptr);
        }

        public void RememberTempObject(IntPtr ptr)
        {
            this.tempObjects.Add(ptr);
        }

        public void FreeTemps()
        {
            foreach (IntPtr ptr in this.tempPtrs)
            {
                this.allocator.Free(ptr);
            }
            foreach (IntPtr ptr in this.tempObjects)
            {
                this.DecRef(ptr);
            }
            this.tempObjects.Clear();
            this.tempPtrs.Clear();
        }
        
        public Exception LastException
        {
            get
            {
                return this._lastException;
            }
            set
            {
                this._lastException = value;
            }
        }
        
        public override void
        PyErr_SetString(IntPtr excType, string message)
        {
            this._lastException = new Exception(message);
        }
    }

}
