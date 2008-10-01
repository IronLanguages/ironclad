using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using Ironclad.Structs;

using Microsoft.Scripting;

using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
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
            IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
            this.map.Associate(strPtr, this.StringFromBytes(bytes));
            return strPtr;
        }
        
        public override IntPtr
        PyString_FromStringAndSize(IntPtr stringData, int length)
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
                Marshal.Copy(stringData, bytes, 0, length);
                IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
                this.map.Associate(strPtr, this.StringFromBytes(bytes));
                return strPtr;
            }
        }

        public override IntPtr
        PyString_InternFromString(IntPtr stringData)
        {
            IntPtr newStrPtr = PyString_FromString(stringData);
            IntPtr newStrPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(IntPtr)));
            CPyMarshal.WritePtr(newStrPtrPtr, newStrPtr);
            this.PyString_InternInPlace(newStrPtrPtr);
            return CPyMarshal.ReadPtr(newStrPtrPtr);
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
                string s = (string)this.Retrieve(strPtr);
                return CPyMarshal.Offset(strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        private int
        _PyString_Resize_Grow(IntPtr strPtrPtr, int newSize)
        {
            IntPtr oldStr = CPyMarshal.ReadPtr(strPtrPtr);
            IntPtr newStr = IntPtr.Zero;
            try
            {
                newStr = this.allocator.Realloc(
                    oldStr, Marshal.SizeOf(typeof(PyStringObject)) + newSize);
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
            return this._PyString_Resize_NoGrow(newStr, newSize);
        }
        
        private int
        _PyString_Resize_NoGrow(IntPtr strPtr, int newSize)
        {
            IntPtr ob_sizePtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
            CPyMarshal.WriteInt(ob_sizePtr, newSize);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            IntPtr terminatorPtr = CPyMarshal.Offset(
                bufPtr, newSize);
            CPyMarshal.WriteByte(terminatorPtr, 0);
            return 0;
        }
        
        
        public override int
        _PyString_Resize(IntPtr strPtrPtr, int newSize)
        {
            IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
            PyStringObject str = (PyStringObject)Marshal.PtrToStructure(strPtr, typeof(PyStringObject));
            if (str.ob_size < newSize)
            {
                return this._PyString_Resize_Grow(strPtrPtr, newSize);
            }
            else
            {
                return this._PyString_Resize_NoGrow(strPtr, newSize);
            }
        }
        
        public override int
        PyString_Size(IntPtr strPtr)
        {
            PyStringObject str = (PyStringObject)Marshal.PtrToStructure(strPtr, typeof(PyStringObject));
            return (int)str.ob_size;
        }
        
        private IntPtr 
        AllocPyString(int length)
        {
            int size = Marshal.SizeOf(typeof(PyStringObject)) + length;
            IntPtr data = this.allocator.Alloc(size);
            
            PyStringObject s = new PyStringObject();
            s.ob_refcnt = 1;
            s.ob_type = this.PyString_Type;
            s.ob_size = (uint)length;
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
            IntPtr strPtr = this.AllocPyString(bytes.Length);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
            return strPtr;
        }
        
        private IntPtr
        Store(string str)
        {
            char[] chars = str.ToCharArray();
            byte[] bytes = Array.ConvertAll<char, byte>(
                chars, new Converter<char, byte>(ByteFromChar));
            IntPtr strPtr = this.CreatePyStringWithBytes(bytes);
            this.map.Associate(strPtr, str);
            return strPtr;
        }
        
        private void
        ActualiseString(IntPtr ptr)
        {
            IntPtr buffer = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            IntPtr lengthPtr = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
            int length = CPyMarshal.ReadInt(lengthPtr);

            byte[] bytes = new byte[length];
            Marshal.Copy(buffer, bytes, 0, length);
            char[] chars = Array.ConvertAll<byte, char>(
                bytes, new Converter<byte, char>(CharFromByte));
            this.incompleteObjects.Remove(ptr);
            this.map.Associate(ptr, new string(chars));
        }
    }
}