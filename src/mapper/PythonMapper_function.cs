using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        private IntPtr
        StoreTyped(PythonFunction func)
        {
            uint size = (uint)Marshal.SizeOf(typeof(PyFunctionObject));
            IntPtr ptr = this.allocator.Alloc(size);
            CPyMarshal.Zero(ptr, size);
            CPyMarshal.WriteIntField(ptr, typeof(PyIntObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyIntObject), "ob_type", this.PyFunction_Type);
            this.map.Associate(ptr, func);
            return ptr;
        }
    }
}