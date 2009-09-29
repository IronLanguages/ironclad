using System;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using IronPython.Runtime;
using IronPython.Runtime.Operations;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyRun_StringFlags(string code, int mode, IntPtr globalsPtr, IntPtr localsPtr, IntPtr flagsPtr)
        {
            if (flagsPtr != IntPtr.Zero)
            {
                throw new NotImplementedException("PyRun_StringFlags: flags are not currently handled");
            }
            if (globalsPtr == IntPtr.Zero)
            {
                throw new NotImplementedException("PyRun_StringFlags: globals are currently required");
            }
            if ((EvalToken)mode != EvalToken.Py_file_input)
            {
                throw new NotImplementedException("PyRun_StringFlags: only Py_file_input mode is currently supported");
            }
            
            try
            {
                PythonDictionary globals = (PythonDictionary)this.Retrieve(globalsPtr);
                object locals = null;
                if (localsPtr != IntPtr.Zero)
                {
                    locals = this.Retrieve(localsPtr);
                }
                PythonOps.QualifiedExec(this.scratchContext, code, globals, locals);
                this.IncRef(this._Py_NoneStruct);
                return this._Py_NoneStruct;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
