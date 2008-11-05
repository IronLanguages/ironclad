using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

using Microsoft.Scripting.Hosting;

using IronPython.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public ScriptScope
        DispatcherModule
        {
            get
            {
                return this.dispatcherModule;
            }
        }
        
        public delegate void VoidVoidDgt();
        
        private void CreateDispatcherModule()
        {   
            PythonDictionary globals = new PythonDictionary();
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["EnsureGIL"] = new VoidVoidDgt(this.EnsureGIL);
            globals["ReleaseGIL"] = new VoidVoidDgt(this.ReleaseGIL);
            globals["NullReferenceException"] = typeof(NullReferenceException);
            this.dispatcherModule = this.engine.CreateScope(globals);
            
            this.ExecInModule(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE, this.dispatcherModule);
            this.ExecInModule(CodeSnippets.DISPATCHER_MODULE_CODE, this.dispatcherModule);
            
            this.dispatcherClass = this.dispatcherModule.GetVariable<object>("Dispatcher");
        }
        
        private void StopDispatchingDeletes()
        {
            Builtin.setattr(this.scratchContext, this.dispatcherClass, "delete",
                Builtin.getattr(this.scratchContext, this.dispatcherClass, "dontDelete"));
        }
    }
}
