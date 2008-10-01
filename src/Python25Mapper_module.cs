using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Hosting.Providers;
using Microsoft.Scripting.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            if (this.importName != "")
            {
                name = this.importName;
            }
            
            PythonDictionary methodTable = new PythonDictionary();
            PythonDictionary globals = new PythonDictionary();
            object moduleDispatcher = PythonCalls.Call(this.dispatcherClass, new object[] { this, methodTable });

            globals["__doc__"] = doc;
            globals["__name__"] = name;
            globals["_dispatcher"] = moduleDispatcher;
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["NullReferenceException"] = typeof(NullReferenceException);

            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE); // eww
            CallableBuilder.GenerateFunctions(moduleCode, methods, methodTable);

            ScriptScope module = this.engine.CreateScope(globals);
            this.ExecInModule(moduleCode.ToString(), module);
            this.AddModule(name, module);
            return this.Store(this.GetModule(name));
        }
        
        public override IntPtr
        PyEval_GetBuiltins()
        {
            Scope __builtin__ = (Scope)this.GetModule("__builtin__");
            return this.Store(__builtin__.Dict);
        }

        public override IntPtr
        PyModule_GetDict(IntPtr modulePtr)
        {
            Scope module = (Scope)this.Retrieve(modulePtr);
            return this.Store(ScopeOps.Get__dict__(module));
        }

        private int PyModule_Add(IntPtr modulePtr, string name, object value)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            ScriptScope moduleScope = this.GetModuleScriptScope((Scope)this.Retrieve(modulePtr));
            moduleScope.SetVariable(name, value);
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

        private void
        ExecInModule(string code, ScriptScope module)
        {
            ScriptSource script = this.engine.CreateScriptSourceFromString(code, SourceCodeKind.Statements);
            script.Execute(module);
        }
        
        public void
        AddModule(string name, ScriptScope module)
        {
            ScriptScope sys = Python.GetSysModule(this.Engine);
            PythonDictionary modules = (PythonDictionary)sys.GetVariable("modules");
            modules[name] = HostingHelpers.GetScope(module);
        }

        public object 
        GetModule(string name)
        {
            ScriptScope sys = Python.GetSysModule(this.Engine);
            PythonDictionary modules = (PythonDictionary)sys.GetVariable("modules");
            if (modules.has_key(name))
            {
                return modules[name];
            }
            return null;
        }

        public ScriptScope 
        GetModuleScriptScope(Scope module)
        {
            return this.Engine.CreateScope(module.Dict);
        }
        
        private void
        CreateScratchModule()
        {
            PythonDictionary globals = new PythonDictionary();
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["_mapper"] = this;
            this.scratchModule = this.engine.CreateScope(globals);
            this.ExecInModule(CodeSnippets.FIX_CPyMarshal_RuntimeType_CODE, this.scratchModule);
            
            Scope scratchScope = HostingHelpers.GetScope(this.scratchModule);
            this.scratchContext = new CodeContext(scratchScope, HostingHelpers.GetLanguageContext(this.engine));
        }
    }
}
