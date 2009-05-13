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

        public override IntPtr
        PyErr_NewException(string name, IntPtr basePtr, IntPtr dictPtr)
        {
            object _base = PythonExceptions.Exception;
            if (basePtr != IntPtr.Zero)
            {
                _base = this.Retrieve(basePtr);
            }
            
            PythonTuple bases = new PythonTuple(new object[]{_base});

            string __name__ = null;
            string __module__ = null;
            CallableBuilder.ExtractNameModule(name, ref __name__, ref __module__);
            
            PythonDictionary classDict = new PythonDictionary();
            classDict["__name__"] = __name__;
            classDict["__module__"] = __module__;
            
            if (dictPtr != IntPtr.Zero)
            {
                PythonDictionary dict = (PythonDictionary)this.Retrieve(dictPtr);
                classDict.update(this.scratchContext, dict);
            }
            
            return this.Store(new PythonType(this.scratchContext, __name__, bases, classDict));
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
