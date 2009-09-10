using System;
using System.Collections.Generic;
using System.IO;
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
        Py_InitModule4(string name, IntPtr methodsPtr, string doc, IntPtr self, int apiver)
        {
            name = this.FixImportName(name);
            
            PythonDictionary methodTable = new PythonDictionary();
            PythonDictionary globals = new PythonDictionary();
            Scope module = new Scope(globals);
            
            this.AddModule(name, module);
            this.CreateModulesContaining(name);

            globals["__doc__"] = doc;
            globals["__name__"] = name;
            globals["__file__"] = this.importFiles.Peek();
            List __path__ = new List();
            
            string importFile = this.importFiles.Peek();
            if (importFile != null)
            {
                __path__.append(Path.GetDirectoryName(importFile));
            }
            globals["__path__"] = __path__;
            Dispatcher moduleDispatcher = new Dispatcher(this, methodTable, self);
            globals["_dispatcher"] = moduleDispatcher;

            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(CodeSnippets.USEFUL_IMPORTS);
            CallableBuilder.GenerateFunctions(moduleCode, methodsPtr, methodTable);
            this.ExecInModule(moduleCode.ToString(), module);
            
            return this.Store(module);
        }
        
        public override IntPtr
        PyEval_GetBuiltins()
        {
            Scope __builtin__ = (Scope)this.GetModule("__builtin__");
            return this.Store(__builtin__.Dict);
        }
        
        public override IntPtr
        PySys_GetObject(string name)
        {
            try
            {
                Scope sys = this.python.SystemState;
                return this.Store(ScopeOps.__getattribute__(sys, name));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyModule_New(string name)
        {
            Scope module = new Scope();
            ScopeOps.__setattr__(module, "__name__", name);
            ScopeOps.__setattr__(module, "__doc__", "");
            return this.Store(module);
        }

        public override IntPtr
        PyModule_GetDict(IntPtr modulePtr)
        {
            Scope module = (Scope)this.Retrieve(modulePtr);
            return this.Store(ScopeOps.Get__dict__(module));
        }

        private int 
        IC_PyModule_Add(IntPtr modulePtr, string name, object value)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            Scope module = (Scope)this.Retrieve(modulePtr);
            ScopeOps.__setattr__(module, name, value);
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
            return this.IC_PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddIntConstant(IntPtr modulePtr, string name, int value)
        {
            return this.IC_PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddStringConstant(IntPtr modulePtr, string name, string value)
        {
            return this.IC_PyModule_Add(modulePtr, name, value);
        }

        private void
        ExecInModule(string code, Scope module)
        {
            SourceUnit script = this.python.CreateSnippet(code, SourceCodeKind.Statements);
            script.Execute(module);
        }
        
        public void
        AddModule(string name, Scope module)
        {
            Scope sys = this.python.SystemState;
            PythonDictionary modules = (PythonDictionary)ScopeOps.__getattribute__(sys, "modules");
            modules[name] = module;
        }

        public object 
        GetModule(string name)
        {
            Scope sys = this.python.SystemState;
            PythonDictionary modules = (PythonDictionary)ScopeOps.__getattribute__(sys, "modules");
            if (modules.has_key(name))
            {
                return modules[name];
            }
            return null;
        }
        
        private void
        CreateScratchModule()
        {
            PythonDictionary globals = new PythonDictionary();
            globals["_mapper"] = this;
            
            this.scratchModule = new Scope(globals);
            this.ExecInModule(CodeSnippets.USEFUL_IMPORTS, this.scratchModule);
            this.scratchContext = new CodeContext(this.scratchModule, this.python);
        }
    }
}
