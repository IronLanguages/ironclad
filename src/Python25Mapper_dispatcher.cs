using System;
using System.Collections.Generic;
using System.Threading;

using Microsoft.Scripting.Hosting;

using IronPython.Runtime;
using IronPython.Runtime.Calls;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public PythonModule
        DispatcherModule
        {
            get
            {
                return this.dispatcherModule;
            }
        }
        
        public delegate void SingleObjectArgDgt(object obj);
        
        private void CreateDispatcherModule()
        {
            string id = "_ironclad_dispatcher";

            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["MonitorExit"] = new SingleObjectArgDgt(Monitor.Exit);
            globals["MonitorEnter"] = new SingleObjectArgDgt(Monitor.Enter);
            globals["NullReferenceException"] = typeof(NullReferenceException);

            this.dispatcherModule = this.GetPythonContext().CreateModule(
                id, id, globals, ModuleOptions.None);
            this.ExecInModule(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE, this.dispatcherModule);
            this.ExecInModule(CodeSnippets.DISPATCHER_MODULE_CODE, this.dispatcherModule);
            
            ScriptScope scope = this.GetModuleScriptScope(this.dispatcherModule);
            this.dispatcherClass = scope.GetVariable<object>("Dispatcher");
            this.dispatcherLock = Builtin.getattr(DefaultContext.Default, this.dispatcherClass, "_lock");
        }
        
        private void StopDispatchingDeletes()
        {
            Builtin.setattr(DefaultContext.Default, this.dispatcherClass, "delete",
                Builtin.getattr(DefaultContext.Default, this.dispatcherClass, "dontDelete"));
        }
    }
}
