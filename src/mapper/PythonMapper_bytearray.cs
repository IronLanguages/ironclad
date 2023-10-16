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
        private IntPtr 
        AllocPyByteArrayObject(int size)
        {
            int objectSize = Marshal.SizeOf<PyByteArrayObject>();
            int alloc = size;
            if (size != 0) alloc += 1; // extra space for tailing null byte
            IntPtr data = this.allocator.Alloc(objectSize + alloc);
            
            var s = new PyByteArrayObject();
            s.ob_refcnt = 1;
            s.ob_type = this.PyByteArray_Type;
            s.ob_size = size;

            if (size == 0) {
                s.ob_bytes = IntPtr.Zero;
            }
            else {
                s.ob_bytes = data + objectSize;
                CPyMarshal.Zero(s.ob_bytes + alloc, 1);
            }
            s.ob_alloc = alloc;
            s.ob_start = s.ob_bytes;
            s.ob_exports = 0;

            Marshal.StructureToPtr(s, data, false);
            
            return data;
        }
        
        private IntPtr
        CreatePyByteArrayWithBytes(byte[] bytes)
        {
            IntPtr ptr = this.AllocPyByteArrayObject(bytes.Length);
            IntPtr bufPtr = ptr + Marshal.SizeOf<PyByteArrayObject>();
            Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
            return ptr;
        }

        private IntPtr
        StoreTyped(ByteArray bytearray)
        {
            IntPtr ptr = this.CreatePyBytesWithBytes(bytearray.ToArray());
            this.map.Associate(ptr, bytearray);
            return ptr;
        }
    }
}
