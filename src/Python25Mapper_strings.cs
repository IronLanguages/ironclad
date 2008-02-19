using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using JumPy.Structs;

namespace JumPy
{
    public partial class Python25Mapper : PythonMapper
    {
        private IntPtr 
        AllocPyString(int length)
        {
            int size = Marshal.SizeOf(typeof(PyStringObject)) + length;
            IntPtr data = this.allocator.Alloc(size);
            
            PyStringObject s = new PyStringObject();
            s.ob_refcnt = 1;
            s.ob_type = IntPtr.Zero;
            s.ob_size = (uint)length;
            s.ob_shash = -1;
            s.ob_sstate = 0;
            Marshal.StructureToPtr(s, data, false);
            
            IntPtr terminator = CPyMarshal.Offset(data, size - 1);
            CPyMarshal.WriteByte(terminator, 0);
        
            return data;
        }
        
        
        private IntPtr
        CreatePyStringWithBytes(byte[] bytes)
        {
            IntPtr strPtr = this.AllocPyString(bytes.Length);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
            Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
            
            char[] chars = Array.ConvertAll<byte, char>(
                bytes, new Converter<byte, char>(CharFromByte));
            this.ptrmap[strPtr] = new string(chars);
            return strPtr;
        }
        
        
        public override IntPtr PyString_FromString(IntPtr stringData)
        {
            // maybe I should just DllImport memcpy... :/
            IntPtr current = stringData;
            List<byte> bytesList = new List<byte>();
            while (CPyMarshal.ReadByte(current) != 0)
            {
                bytesList.Add(CPyMarshal.ReadByte(current));
                current = CPyMarshal.Offset(current, 1);
            }
            byte[] bytes = new byte[bytesList.Count];
            bytesList.CopyTo(bytes);
            return this.CreatePyStringWithBytes(bytes);
        }
        
        
        public override IntPtr
        PyString_FromStringAndSize(IntPtr stringData, int length)
        {
            if (stringData == IntPtr.Zero)
            {
                IntPtr data = this.AllocPyString(length);
                this.StoreUnmanagedData(data, UnmanagedDataMarker.PyStringObject);
                return data;
            }
            else
            {
                byte[] bytes = new byte[length];
                Marshal.Copy(stringData, bytes, 0, length);
                return this.CreatePyStringWithBytes(bytes);
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
                this._lastException = e;
                this.Delete(oldStr);
                return -1;
            }
            this.ptrmap.Remove(oldStr);
            CPyMarshal.WritePtr(strPtrPtr, newStr);
            this.StoreUnmanagedData(newStr, UnmanagedDataMarker.PyStringObject);
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
    }
}