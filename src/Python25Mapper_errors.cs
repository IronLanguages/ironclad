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
        PyErr_Fetch(IntPtr typePtrPtr, IntPtr valuePtrPtr, IntPtr tbPtrPtr)
        {
            CPyMarshal.Zero(typePtrPtr, CPyMarshal.PtrSize);
            CPyMarshal.Zero(valuePtrPtr, CPyMarshal.PtrSize);
            CPyMarshal.Zero(tbPtrPtr, CPyMarshal.PtrSize);
            
            if (this.LastException != null)
            {
                object excType = PythonCalls.Call(Builtin.type, new object[] { this.LastException });
                CPyMarshal.WritePtr(typePtrPtr, this.Store(excType));
                CPyMarshal.WritePtr(valuePtrPtr, this.Store(this.LastException.ToString()));
            }
            this.LastException = null;
        }
        
        public override void
        PyErr_Restore(IntPtr typePtr, IntPtr valuePtr, IntPtr tbPtr)
        {
            if (typePtr != IntPtr.Zero && valuePtr != IntPtr.Zero)
            {
                this.LastException = PythonCalls.Call(this.Retrieve(typePtr), new object[] { this.Retrieve(valuePtr) });
                this.DecRef(typePtr);
                this.DecRef(valuePtr);
            }
        }

        private void
        PrintToStdErr(object obj)
        {
            object stderr = Builtin.getattr(DefaultContext.Default, this.GetPythonContext().SystemStateModules["sys"], "__stderr__");
            PythonOps.PrintWithDest(DefaultContext.Default, stderr, obj);
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

        public override IntPtr
        PyErr_NewException(string name, IntPtr _base, IntPtr dict)
        {
            if (_base != IntPtr.Zero || dict != IntPtr.Zero)
            {
                throw new NotImplementedException("PyErr_NewException called with non-null base or dict");
            }
            string __name__ = null;
            string __module__ = null;
            CallableBuilder.ExtractNameModule(name, ref __name__, ref __module__);

            string excCode = String.Format(CodeSnippets.NEW_EXCEPTION, __name__, __module__);
            this.ExecInModule(excCode, this.scratchModule);
            object newExc = this.GetModuleScriptScope(this.scratchModule).GetVariable<object>(__name__);
            IntPtr newExcPtr = this.Store(newExc);
            this.IncRef(newExcPtr);
            return newExcPtr;
        }
    }
}