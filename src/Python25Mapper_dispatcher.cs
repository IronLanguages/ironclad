using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using IronPython.Runtime;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public Scope
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
            globals["EnsureGIL"] = new VoidVoidDgt(this.EnsureGIL);
            globals["ReleaseGIL"] = new VoidVoidDgt(this.ReleaseGIL);
            
            this.dispatcherModule = new Scope(globals);
            this.ExecInModule(CodeSnippets.USEFUL_IMPORTS, this.dispatcherModule);
            this.ExecInModule(CodeSnippets.DISPATCHER_MODULE_CODE, this.dispatcherModule);
            this.dispatcherClass = ScopeOps.__getattribute__(this.dispatcherModule, "Dispatcher");
        }
        
        private void StopDispatchingDeletes()
        {
            Builtin.setattr(this.scratchContext, this.dispatcherClass, "delete",
                Builtin.getattr(this.scratchContext, this.dispatcherClass, "dontDelete"));
        }
    }
}
