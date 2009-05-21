using System;

using Microsoft.Scripting.Runtime;

using IronPython.Hosting;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
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
            object stderr = ScopeOps.__getattribute__(this.python.SystemState, "stderr");
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
    }
}
