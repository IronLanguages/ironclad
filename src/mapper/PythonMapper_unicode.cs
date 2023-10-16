using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using Microsoft.Scripting;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        private IntPtr
        StoreTyped(string value)
        {
            // TODO: support other representations... maybe we can use PyUnicode_FromWideChar after bootstrapping is done?
            var bytes = Encoding.ASCII.GetBytes(value);

            int size = Marshal.SizeOf<PyASCIIObject>();
            IntPtr ptr = this.allocator.Alloc(size + bytes.Length + 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), nameof(PyObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), nameof(PyObject.ob_type), this.PyUnicode_Type);
            CPyMarshal.WritePtrField(ptr, typeof(PyASCIIObject), nameof(PyASCIIObject.length), bytes.Length);
            CPyMarshal.WritePtrField(ptr, typeof(PyASCIIObject), nameof(PyASCIIObject.hash), -1);
            CPyMarshal.WriteIntField(ptr, typeof(PyASCIIObject), nameof(PyASCIIObject.state), 0b111_001_00);
            CPyMarshal.WritePtrField(ptr, typeof(PyASCIIObject), nameof(PyASCIIObject.wstr), IntPtr.Zero);
            IntPtr dataPtr = ptr + size;
            Marshal.Copy(bytes, 0, dataPtr, bytes.Length);
            Marshal.WriteByte(dataPtr, bytes.Length, 0);

            this.map.Associate(ptr, value);
            return ptr;
        }
    }
}
