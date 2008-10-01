using System;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;

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
                ScriptSource script = this.engine.CreateScriptSourceFromString(code, SourceCodeKind.Statements);
                script.Execute(this.Engine.CreateScope((IAttributesCollection)this.Retrieve(globalsPtr)));
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