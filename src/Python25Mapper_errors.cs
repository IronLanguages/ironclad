using System;

using Microsoft.Scripting.Runtime;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {


        public object LastException
        {
            get
            {
                return this._lastException;
            }
            set
            {
                this._lastException = value;
            }
        }

        public override void
        PyErr_SetString(IntPtr excTypePtr, string message)
        {
            if (excTypePtr == IntPtr.Zero)
            {
                this._lastException = new Exception(message);
            }
            else
            {
                object excType = this.Retrieve(excTypePtr);
                this._lastException = PythonCalls.Call(excType, new object[1] { message });
            }
        }

        public override IntPtr
        PyErr_Occurred()
        {
            if (this.LastException == null)
            {
                return IntPtr.Zero;
            }
            IntPtr errorPtr = this.Store(this.LastException);
            this.RememberTempObject(errorPtr);
            return errorPtr;
        }

        public override void
        PyErr_Clear()
        {
            this.LastException = null;
        }

        public override void
        PyErr_Print()
        {
            if (this.LastException == null)
            {
                throw new Exception("Fatal error: called PyErr_Print without an actual error to print.");
            }
            object stderr = Builtin.getattr(DefaultContext.Default, this.GetPythonContext().SystemStateModules["sys"], "__stderr__");
            PythonOps.PrintWithDest(DefaultContext.Default, stderr, this.LastException);
            this.LastException = null;
        }
    }
}