using System;
using System.Collections.Generic;
using System.Linq;
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
        IC_PyBytes_Concat_Core(IntPtr str1Ptr, IntPtr str2Ptr)
        {
            try
            {
                Bytes str1 = (Bytes)this.Retrieve(str1Ptr);
                Bytes str2 = (Bytes)this.Retrieve(str2Ptr);
                return this.Store(str1 + str2);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override void
        PyBytes_Concat(IntPtr str1PtrPtr, IntPtr str2Ptr)
        {
            IntPtr str1Ptr = Marshal.ReadIntPtr(str1PtrPtr);
            if (str1Ptr == IntPtr.Zero)
            {
                return;
            }
            IntPtr str3Ptr = IntPtr.Zero;
            if (str2Ptr != IntPtr.Zero)
            {
                str3Ptr = this.IC_PyBytes_Concat_Core(str1Ptr, str2Ptr);
            }
            Marshal.WriteIntPtr(str1PtrPtr, str3Ptr);
            this.DecRef(str1Ptr);
        }

        public override void
        PyBytes_ConcatAndDel(IntPtr str1PtrPtr, IntPtr str2Ptr)
        {
            this.PyBytes_Concat(str1PtrPtr, str2Ptr);
            this.DecRef(str2Ptr);
        }


        public override IntPtr 
        PyBytes_FromString(IntPtr stringData)
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
            // TODO: do we still need this?
            // note: NOT Associate
            // couldn't figure out to test this directly
            // without this, h5py tests get horribly screwy in PHIL contextmanager
            return this.Store(this.BytesFromBytes(bytes));
        }
        
        public override IntPtr
        PyBytes_FromStringAndSize(IntPtr stringData, nint length)
        {
            if (stringData == IntPtr.Zero)
            {
                IntPtr data = this.AllocPyBytes(checked((int)length));
                this.incompleteObjects[data] = UnmanagedDataMarker.PyBytesObject;
                return data;
            }
            else
            {
                byte[] bytes = new byte[checked((int)length)];
                Marshal.Copy(stringData, bytes, 0, bytes.Length);
                // note: NOT Associate
                // couldn't figure out to test this directly
                // without this, h5py tests get horribly screwy in PHIL contextmanager
                return this.Store(this.BytesFromBytes(bytes));
            }
        }

        public override IntPtr
        PyBytes_AsString(IntPtr strPtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(strPtr, typeof(PyObject), nameof(PyObject.ob_type)) != this.PyBytes_Type)
                {
                    throw PythonOps.TypeError("PyBytes_AsString: not bytes");
                }
                return CPyMarshal.Offset(strPtr, Marshal.OffsetOf(typeof(PyBytesObject), nameof(PyBytesObject.ob_sval)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override int
        PyBytes_AsStringAndSize(IntPtr strPtr, IntPtr dataPtrPtr, IntPtr sizePtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(strPtr, typeof(PyObject), nameof(PyObject.ob_type)) != this.PyBytes_Type)
                {
                    throw PythonOps.TypeError("PyBytes_AsStringAndSize: not bytes");
                }
                
                IntPtr dataPtr = CPyMarshal.GetField(strPtr, typeof(PyBytesObject), nameof(PyBytesObject.ob_sval));
                CPyMarshal.WritePtr(dataPtrPtr, dataPtr);
                
                nint length = CPyMarshal.ReadPtrField(strPtr, typeof(PyBytesObject), nameof(PyBytesObject.ob_size));
                if (sizePtr == IntPtr.Zero)
                {
                    for (nint i = 0; i < length; ++i)
                    {
                        if (CPyMarshal.ReadByte(CPyMarshal.Offset(dataPtr, i)) == 0)
                        {
                            throw PythonOps.TypeError("PyBytes_AsStringAndSize: bytes contains embedded 0s, but sizePtr is null");
                        }
                    }
                }
                else
                {
                    CPyMarshal.WritePtr(sizePtr, length);
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
        PyBytes_Repr(IntPtr ptr, int smartquotes)
        {
            // smartquotes ignored for now
            try
            {
                return this.Store(Builtin.repr(this.scratchContext, this.ReadPyBytes(ptr)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        private int
        IC__PyBytes_Resize_Grow(IntPtr strPtrPtr, nint newSize)
        {
            IntPtr oldStr = CPyMarshal.ReadPtr(strPtrPtr);
            IntPtr newStr = IntPtr.Zero;
            try
            {
                newStr = this.allocator.Realloc(oldStr, Marshal.SizeOf<PyBytesObject>() + newSize);
            }
            catch (OutOfMemoryException e)
            {
                this.LastException = e;
                this.PyObject_Free(oldStr);
                return -1;
            }
            CPyMarshal.WritePtr(strPtrPtr, newStr);
            this.incompleteObjects.Remove(oldStr);
            this.incompleteObjects[newStr] = UnmanagedDataMarker.PyBytesObject;
            return this.IC__PyBytes_Resize_NoGrow(newStr, newSize);
        }
        
        private int
        IC__PyBytes_Resize_NoGrow(IntPtr strPtr, nint newSize)
        {
            CPyMarshal.WritePtrField(strPtr, typeof(PyBytesObject), nameof(PyBytesObject.ob_size), newSize);
            IntPtr bufPtr = CPyMarshal.Offset(
                strPtr, Marshal.OffsetOf(typeof(PyBytesObject), nameof(PyBytesObject.ob_sval)));
            IntPtr terminatorPtr = CPyMarshal.Offset(
                bufPtr, newSize);
            CPyMarshal.WriteByte(terminatorPtr, 0);
            return 0;
        }
        
        
        public override int
        _PyBytes_Resize(IntPtr strPtrPtr, nint newSize)
        {
            IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
            nint size = CPyMarshal.ReadPtrField(strPtr, typeof(PyBytesObject), nameof(PyBytesObject.ob_size));
            if (size < newSize)
            {
                return this.IC__PyBytes_Resize_Grow(strPtrPtr, newSize);
            }
            else
            {
                return this.IC__PyBytes_Resize_NoGrow(strPtr, newSize);
            }
        }
        
        public override nint
        PyBytes_Size(IntPtr strPtr)
        {
            return CPyMarshal.ReadPtrField(strPtr, typeof(PyBytesObject), nameof(PyBytesObject.ob_size));
        }
        
        private IntPtr 
        AllocPyBytes(int length)
        {
            int size = Marshal.SizeOf<PyBytesObject>() + length; // TODO: because of struct padding, this is more than we actually need...
            IntPtr data = this.allocator.Alloc(size);
            
            PyBytesObject s = new PyBytesObject();
            s.ob_refcnt = 1;
            s.ob_type = this.PyBytes_Type;
            s.ob_size = length;
            s.ob_shash = -1;
            Marshal.StructureToPtr(s, data, false);
            
            nint terminator_offset = Marshal.OffsetOf<PyBytesObject>(nameof(PyBytesObject.ob_sval)) + length;
            CPyMarshal.Zero(data + terminator_offset, 1);
        
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
        
        private Bytes
        BytesFromBytes(byte[] bytes)
        {
            return new Bytes(bytes);
        }
        
        private IntPtr
        CreatePyBytesWithBytes(byte[] bytes)
        {
            IntPtr bytesPtr = this.AllocPyBytes(bytes.Length);
            IntPtr bufPtr = CPyMarshal.Offset(bytesPtr, Marshal.OffsetOf(typeof(PyBytesObject), nameof(PyBytesObject.ob_sval)));
            Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
            return bytesPtr;
        }
        
        private IntPtr
        StoreTyped(Bytes bytes)
        {
            IntPtr bytesPtr = this.CreatePyBytesWithBytes(bytes.ToArray());
            this.map.Associate(bytesPtr, bytes);
            return bytesPtr;
        }

        private Bytes
        ReadPyBytes(IntPtr ptr)
        {
            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), nameof(PyObject.ob_type));
            if (PyType_IsSubtype(typePtr, this.PyBytes_Type) == 0)
            {
                throw new ArgumentTypeException("ReadPyBytes: Expected bytes, or subclass thereof");
            }
            IntPtr buffer = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyBytesObject), nameof(PyBytesObject.ob_sval)));
            nint length = CPyMarshal.ReadPtrField(ptr, typeof(PyBytesObject), nameof(PyBytesObject.ob_size));
            byte[] bytes = new byte[checked((int)length)];
            Marshal.Copy(buffer, bytes, 0, bytes.Length);
            return new Bytes(bytes);
        }
        
        private void
        ActualiseBytes(IntPtr ptr)
        {
            Bytes str = this.ReadPyBytes(ptr);
            this.incompleteObjects.Remove(ptr);
            this.map.Associate(ptr, str);
        }

        public override IntPtr
        IC_PyBytes_Str(IntPtr ptr)
        {
            try
            {
                return this.Store(this.ReadPyBytes(ptr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override int
        IC_bytes_getbuffer(IntPtr objPtr, IntPtr viewPtr, int flags)
        {
            throw new NotImplementedException(); // https://github.com/IronLanguages/ironclad/issues/15
        }

        public override void
        IC_bytes_releasebuffer(IntPtr objPtr, IntPtr viewPtr)
        {
            throw new NotImplementedException(); // https://github.com/IronLanguages/ironclad/issues/15
        }
    }
}
