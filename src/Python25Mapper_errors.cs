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
        public override IntPtr
        Make_PyExc_BaseException()
        {
            // all the others autogenerate nicely
            return this.Store(Builtin.BaseException);
        }
        
        public override IntPtr
        PyErr_Occurred()
        {
            if (this.LastException == null)
            {
                return IntPtr.Zero;
            }
            object errorType = PythonCalls.Call(Builtin.type, new object[] { this.LastException });
            IntPtr errorPtr = this.Store(errorType);
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
            if (typePtr != IntPtr.Zero)
            {
                object[] args = new object[0];
                if (valuePtr != IntPtr.Zero)
                {
                    args = new object[] { this.Retrieve(valuePtr) };
                    this.DecRef(valuePtr);
                }
                
                this.LastException = PythonCalls.Call(this.Retrieve(typePtr), args);
                this.DecRef(typePtr);
            }
            else
            {
                this.LastException = null;
            }
        }

        private void
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
            object newExc = ScopeOps.__getattribute__(this.scratchModule, __name__);
            return this.Store(newExc);
        }
        
        public override int
        PyErr_GivenExceptionMatches(IntPtr givenPtr, IntPtr matchPtr)
        {
            try
            {
                // this could probably be implemented in C, if we had other parts of the API defined
                if (matchPtr == givenPtr)
                {
                    return 1;
                }
                object given = this.Retrieve(givenPtr);
                if (Builtin.isinstance(given, Builtin.BaseException))
                {
                    given = PythonCalls.Call(Builtin.type, new object[] {given});
                }
                // TODO if given is an OldClass, cast will fail and 0 will 
                // be returned, even if it would have been a match
                if (Builtin.issubclass((PythonType)given, this.Retrieve(matchPtr)))
                {
                    return 1;
                }
            }
            catch
            {
                this.PrintToStdErr("PyErr_GivenExceptionMatches: something went wrong. Assuming exception does not match.");
                // something bad happened. let's say it... <coin toss> wasn't a match.
            }
            return 0;
        }
    }
}
