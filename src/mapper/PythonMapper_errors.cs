using System;
using System.Runtime.InteropServices;

using Microsoft.Scripting.Runtime;

using IronPython.Hosting;
using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override void
         Fill_PyExc_BaseException(IntPtr addr)
        {
            // all the others autogenerate nicely
            IntPtr value = this.Store(Builtin.BaseException);
            CPyMarshal.WritePtr(addr, value);
        }

        internal void
        PrintToStdErr(object obj)
        {
            object stderr = this.python.SystemState.Get__dict__()["stderr"];
            PythonOps.PrintWithDest(this.scratchContext, stderr, obj);
        }


        public override void
        PyErr_Print()
        {
            if (this.LastException == null)
            {
                throw new Exception("Fatal error: called PyErr_Print without an actual error to print.");
            }
            this.PrintToStdErr(this.LastException);
            this.LastException = null;
        }

        private IntPtr
        StoreTyped(PythonExceptions.BaseException exc)
        {
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            object type_ = PythonCalls.Call(Builtin.type, new object[] { exc });
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.Store(type_));
            this.map.Associate(ptr, exc);
            return ptr;
        }
    }
}
