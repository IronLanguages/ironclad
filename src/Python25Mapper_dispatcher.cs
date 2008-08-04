using System;
using System.Collections.Generic;

using IronPython.Runtime;
using Microsoft.Scripting.Hosting;

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

        private void CreateDispatcherModule()
        {
            string id = "_ironclad_dispatcher";

            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["NullReferenceException"] = typeof(NullReferenceException);

            this.dispatcherModule = this.GetPythonContext().CreateModule(
                id, id, globals, ModuleOptions.None);
            this.ExecInModule(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE, this.dispatcherModule);
            this.ExecInModule(CodeSnippets.DISPATCHER_MODULE_CODE, this.dispatcherModule);
            
            ScriptScope scope = this.GetModuleScriptScope(this.dispatcherModule);
            this.dispatcherClass = scope.GetVariable<object>("Dispatcher");
        }
    }
}
