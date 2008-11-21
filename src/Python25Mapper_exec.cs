using System;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyRun_StringFlags(string code, int mode, IntPtr globalsPtr, IntPtr localsPtr, IntPtr flagsPtr)
        {
            if (localsPtr != IntPtr.Zero || flagsPtr != IntPtr.Zero)
            {
                throw new NotImplementedException("PyRun_StringFlags: locals and flags are not currently handled");
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
                SourceUnit script = this.python.CreateSnippet(code, SourceCodeKind.Statements);
                IAttributesCollection globals = (IAttributesCollection)this.Retrieve(globalsPtr);
                script.Execute(new Scope(globals));
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
