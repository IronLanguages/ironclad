using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using Ironclad.Structs;

using Microsoft.Scripting;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override IntPtr
        IC_PyString_Concat_Core(IntPtr str1Ptr, IntPtr str2Ptr)
        {
            try
            {
                // why read them, not retrieve them? can't cast string subtypes to string.
                string str1 = this.ReadPyString(str1Ptr);
                string str2 = this.ReadPyString(str2Ptr);
                return this.Store(str1 + str2);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override void
        PyString_Concat(IntPtr str1PtrPtr, IntPtr str2Ptr)
        {
            IntPtr str1Ptr = Marshal.ReadIntPtr(str1PtrPtr);
            if (str1Ptr == IntPtr.Zero)
            {
                return;
            }
            IntPtr str3Ptr = IntPtr.Zero;
            if (str2Ptr != IntPtr.Zero)
            {
                str3Ptr = this.IC_PyString_Concat_Core(str1Ptr, str2Ptr);
            }
            Marshal.WriteIntPtr(str1PtrPtr, str3Ptr);
            this.DecRef(str1Ptr);
        }

        public override void
        PyString_ConcatAndDel(IntPtr str1PtrPtr, IntPtr str2Ptr)
        {
            this.PyString_Concat(str1PtrPtr, str2Ptr);
            this.DecRef(str2Ptr);
        }


        public override IntPtr 
        PyString_FromString(IntPtr stringData)
        {
            IntPtr current = stringData;
            List<byte> bytesList = new List<byte>();
            while (CPyMarshal.ReadByte(current) != 0)
            {
                bytesList.Add(CPyMarshal.ReadByte(current));
                current = CPyMarshal.Offset(current, 1);
            }
            byte[] bytes = new byte[bytesList.Count];
            bytesList.CopyTo(bytes);
            // note: NOT Associate
            // couldn't figure out to test this directly
            // without this, h5py tests get horribly screwy in PHIL contextmanager
            return this.Store(this.StringFromBytes(bytes));
        }
        
        public override IntPtr
        PyString_FromStringAndSize(IntPtr stringData, uint length)
        {
            if (stringData == IntPtr.Zero)
            {
                IntPtr data = this.AllocPyString(length);
                this.incompleteObjects[data] = UnmanagedDataMarker.PyStringObject;
                return data;
            }
            else
            {
                byte[] bytes = new byte[length];
                Marshal.Copy(stringData, bytes, 0, (int)length);
                // note: NOT Associate
                // couldn't figure out to test this directly
                // without this, h5py tests get horribly screwy in PHIL contextmanager
                return this.Store(this.StringFromBytes(bytes));
            }
        }

        public override IntPtr
        PyString_InternFromString(IntPtr stringData)
        {
            IntPtr newStrPtr = PyString_FromString(stringData);
            IntPtr newStrPtrPtr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(IntPtr)));
            CPyMarshal.WritePtr(newStrPtrPtr, newStrPtr);
            this.PyString_InternInPlace(newStrPtrPtr);
            IntPtr newNewStrPtr = CPyMarshal.ReadPtr(newStrPtrPtr);
            this.allocator.Free(newStrPtrPtr);
            return newNewStrPtr;
        }

        public override void
        PyString_InternInPlace(IntPtr strPtrPtr)
        {
            IntPtr intStrPtr = IntPtr.Zero;
            IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
            string str = (string)this.Retrieve(strPtr);

            if (this.internedStrings.ContainsKey(str))
            {
                intStrPtr = this.internedStrings[str];
            }
            else
            {
                intStrPtr = strPtr;
                this.internedStrings[str] = intStrPtr;
                this.IncRef(intStrPtr);
            }
            this.IncRef(intStrPtr);
            this.DecRef(strPtr);
            CPyMarshal.WritePtr(strPtrPtr, intStrPtr);
        }
        
        public override IntPtr
        PyString_AsString(IntPtr strPtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(strPtr, typeof(PyObject), "ob_type") != this.PyString_Type)
                {
                    throw PythonOps.TypeError("PyString_AsString: not a string");
                }
                return CPyMarshal.Offset(strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override int
        PyString_AsStringAndSize(IntPtr strPtr, IntPtr dataPtrPtr, IntPtr sizePtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(strPtr, typeof(PyObject), "ob_type") != this.PyString_Type)
                {
                    throw PythonOps.TypeError("PyString_AsStringAndSize: not a string");
                }
                
                IntPtr dataPtr = CPyMarshal.GetField(strPtr, typeof(PyStringObject), "ob_sval");
                CPyMarshal.WritePtr(dataPtrPtr, dataPtr);
                
                uint length = CPyMarshal.ReadUIntField(strPtr, typeof(PyStringObject), "ob_size");
                if (sizePtr == IntPtr.Zero)
                {
                    for (uint i = 0; i < length; ++i)
                    {
                        if (CPyMarshal.ReadByte(CPyMarshal.Offset(dataPtr, i)) == 0)
                        {
                            throw PythonOps.TypeError("PyString_AsStringAndSize: string contains embedded 0s, but sizePtr is null");
                        }
                    }
                }
                else
                {
                    CPyMarshal.WriteUInt(sizePtr, length);
                }
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override IntPtr
        PyString_Repr(IntPtr ptr, int smartquotes)
        {
            // smartquotes ignored for now
            try
            {
                return this.Store(Builtin.repr(this.scratchContext, this.ReadPyString(ptr)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        private int
        IC__PyString_Resize_Grow(IntPtr strPtrPtr, uint newSize)
        {
            IntPtr oldStr = CPyMarshal.ReadPtr(strPtrPtr);
            IntPtr newStr = IntPtr.Zero;
            try
            {
                newStr = this.allocator.Realloc(oldStr, (uint)Marshal.SizeOf(typeof(PyStringObject)) + newSize);
            }
            catch (OutOfMemoryException e)
            {
                this.LastException = e;
                this.PyObject_Free(oldStr);
                return -1;
            }
            CPyMarshal.WritePtr(strPtrPtr, newStr);
            this.incompleteObjects.Remove(oldStr);
            this.incompleteObjects[newStr] = UnmanagedDataMarker.PyStringObject;
            return this.IC__PyString_Resize_NoGrow(newStr, newSize);
        }
        
        private int
        IC__PyString_Resize_NoGrow(IntPtr strPtr, uint newSize)
        {
            IntPtr ob_sizePtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
            CPyMarshal.WriteUInt(ob_sizePtr, newSize);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            IntPtr terminatorPtr = CPyMarshal.Offset(
                bufPtr, newSize);
            CPyMarshal.WriteByte(terminatorPtr, 0);
            return 0;
        }
        
        
        public override int
        _PyString_Resize(IntPtr strPtrPtr, uint newSize)
        {
            IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
            PyStringObject str = (PyStringObject)Marshal.PtrToStructure(strPtr, typeof(PyStringObject));
            if (str.ob_size < newSize)
            {
                return this.IC__PyString_Resize_Grow(strPtrPtr, newSize);
            }
            else
            {
                return this.IC__PyString_Resize_NoGrow(strPtr, newSize);
            }
        }
        
        public override uint
        PyString_Size(IntPtr strPtr)
        {
            return CPyMarshal.ReadUIntField(strPtr, typeof(PyStringObject), "ob_size");
        }
        
        private IntPtr 
        AllocPyString(uint length)
        {
            uint size = (uint)Marshal.SizeOf(typeof(PyStringObject)) + length;
            IntPtr data = this.allocator.Alloc(size);
            
            PyStringObject s = new PyStringObject();
            s.ob_refcnt = 1;
            s.ob_type = this.PyString_Type;
            s.ob_size = length;
            s.ob_shash = -1;
            s.ob_sstate = 0;
            Marshal.StructureToPtr(s, data, false);
            
            IntPtr terminator = CPyMarshal.Offset(data, size - 1);
            CPyMarshal.WriteByte(terminator, 0);
        
            return data;
        }
        
        private static char
        CharFromByte(byte b)
        {
            return (char)b;
        }
        
        private static byte
        ByteFromChar(char c)
        {
            return (byte)c;
        }
        
        private string
        StringFromBytes(byte[] bytes)
        {
            char[] chars = Array.ConvertAll<byte, char>(
                bytes, new Converter<byte, char>(CharFromByte));
            return new string(chars);
        }
        
        private IntPtr
        CreatePyStringWithBytes(byte[] bytes)
        {
            IntPtr strPtr = this.AllocPyString((uint)bytes.Length);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
            return strPtr;
        }
        
        private IntPtr
        StoreTyped(string str)
        {
            char[] chars = str.ToCharArray();
            byte[] bytes = Array.ConvertAll<char, byte>(
                chars, new Converter<char, byte>(ByteFromChar));
            IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
            this.map.Associate(strPtr, str);
            return strPtr;
        }

        private string
        ReadPyString(IntPtr ptr)
        {
            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
            if (PyType_IsSubtype(typePtr, this.PyString_Type) == 0)
            {
                throw new ArgumentTypeException("ReadPyString: Expected a str, or subclass thereof");
            }
            IntPtr buffer = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            int length = CPyMarshal.ReadIntField(ptr, typeof(PyStringObject), "ob_size");
            byte[] bytes = new byte[length];
            Marshal.Copy(buffer, bytes, 0, length);
            char[] chars = Array.ConvertAll<byte, char>(
                bytes, new Converter<byte, char>(CharFromByte));
            return new string(chars);
        }
        
        private void
        ActualiseString(IntPtr ptr)
        {
            string str = this.ReadPyString(ptr);
            this.incompleteObjects.Remove(ptr);
            this.map.Associate(ptr, str);
        }

        public override IntPtr
        IC_PyString_Str(IntPtr ptr)
        {
            try
            {
                return this.Store(this.ReadPyString(ptr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        
        public override uint
        IC_str_getreadbuffer(IntPtr strPtr, uint seg, IntPtr bufPtrPtr)
        {
            if (seg != 0)
            {
                this.LastException = PythonOps.SystemError("string buffers have only 1 segment");
                return UInt32.MaxValue; // -1
            }
            
            IntPtr bufPtr = CPyMarshal.GetField(strPtr, typeof(PyStringObject), "ob_sval");
            CPyMarshal.WritePtr(bufPtrPtr, bufPtr);
            
            return this.PyString_Size(strPtr);
        }
        
        
        public override uint
        IC_str_getwritebuffer(IntPtr strPtr, uint seg, IntPtr bufPtrPtr)
        {
            this.LastException = PythonOps.SystemError("string buffers are not writable");
            return UInt32.MaxValue; // -1
        }
        
        
        public override uint
        IC_str_getsegcount(IntPtr strPtr, IntPtr lenPtr)
        {
            if (lenPtr != IntPtr.Zero)
            {
                CPyMarshal.WriteUInt(lenPtr, this.PyString_Size(strPtr));
            }
            return 1;
        }
    }
}
