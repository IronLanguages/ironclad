using System;
using System.Collections.Generic;

using IronPython.Runtime;
using Microsoft.Scripting.Hosting;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public PythonModule
        DispatcherModule
        {
            get
            {
                return this.dispatcherModule;
            }
        }

        private void CreateDispatcher()
        {
            string id = "_ironclad_dispatcher";

            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["nullPtr"] = IntPtr.Zero;
            globals["NullReferenceException"] = typeof(NullReferenceException);
            globals["GC"] = typeof(GC);

            this.dispatcherModule = this.GetPythonContext().CreateModule(
                id, id, globals, ModuleOptions.None);
            this.ExecInModule(DISPATCHER_MODULE_CODE, this.dispatcherModule);
            
            ScriptScope scope = this.GetModuleScriptScope(this.dispatcherModule);
            this.dispatcherClass = scope.GetVariable<object>("Dispatcher");
        }
    }
}
