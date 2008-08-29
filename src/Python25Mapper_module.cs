using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {

        private void
        ExecInModule(string code, PythonModule module)
        {
            ScriptSource script = this.engine.CreateScriptSourceFromString(code, SourceCodeKind.Statements);
            ScriptScope scope = this.GetModuleScriptScope(module);
            script.Execute(scope);
        }

        private ScriptScope
        GetModuleScriptScope(PythonModule module)
        {
            return this.engine.CreateScope(module.Scope.Dict);
        }


        private PythonContext
        GetPythonContext()
        {
            return InappropriateReflection.PythonContextFromEngine(this.engine);
        }
        
        
        private void
        CreateScratchModule()
        {
            string id = "_ironclad_scratch";
            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["_mapper"] = this;
            this.scratchModule = this.GetPythonContext().CreateModule(
                id, id, globals, ModuleOptions.None);
            this.ExecInModule(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE, this.scratchModule);

            this.ExecInModule(CodeSnippets.TRIVIAL_OBJECT_SUBCLASS_CODE, this.scratchModule);
            ScriptScope moduleScope = this.GetModuleScriptScope(this.scratchModule);
            this.trivialObjectSubclass = moduleScope.GetVariable<object>("TrivialObjectSubclass");
        }
        
        
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            Dictionary<string, object> globals = new Dictionary<string, object>();
            PythonDictionary methodTable = new PythonDictionary();

            globals["__doc__"] = doc;
            globals["_dispatcher"] = PythonCalls.Call(this.dispatcherClass, new object[] { this, methodTable });

            // hack to help moduleCode run -- can't import from System for some reason
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["NullReferenceException"] = typeof(NullReferenceException);

            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE); // eww
            CallableBuilder.GenerateFunctions(moduleCode, methods, methodTable);

            if (this.importName != "")
            {
                name = this.importName;
            }
            
            PythonModule module = this.GetPythonContext().CreateModule(
                name, this.importPath, globals, ModuleOptions.PublishModule);
            this.ExecInModule(moduleCode.ToString(), module);
            return this.Store(this.GetModuleScope(name));
        }


        public override IntPtr
        PyModule_GetDict(IntPtr modulePtr)
        {
            Scope moduleScope = (Scope)this.Retrieve(modulePtr);
            return this.Store(ScopeOps.Get__dict__(moduleScope));
        }

        private int PyModule_Add(IntPtr modulePtr, string name, object value)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            Scope moduleScope = (Scope)this.Retrieve(modulePtr);
            ScopeOps.__setattr__(moduleScope, name, value);
            return 0;
        }
        
        public override int 
        PyModule_AddObject(IntPtr modulePtr, string name, IntPtr valuePtr)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            object value = this.Retrieve(valuePtr);
            this.DecRef(valuePtr);
            return this.PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddIntConstant(IntPtr modulePtr, string name, int value)
        {
            return this.PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddStringConstant(IntPtr modulePtr, string name, string value)
        {
            return this.PyModule_Add(modulePtr, name, value);
        }
    }
}
