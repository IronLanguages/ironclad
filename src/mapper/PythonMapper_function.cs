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
            int size = Marshal.SizeOf<PyFunctionObject>();
            IntPtr ptr = this.allocator.Alloc(size);
            CPyMarshal.Zero(ptr, size);
            CPyMarshal.WritePtrField(ptr, typeof(PyFunctionObject), nameof(PyFunctionObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyFunctionObject), nameof(PyFunctionObject.ob_type), this.PyFunction_Type);
            this.map.Associate(ptr, func);
            return ptr;
        }
    }
}
