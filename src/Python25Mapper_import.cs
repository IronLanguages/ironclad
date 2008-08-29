using System;
using System.Reflection;
using System.Collections.Generic;

using IronPython.Runtime;
using IronPython.Runtime.Calls;

using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public void 
        LoadModule(string path, string name)
        {
            this.importName = name;
            this.importPath = path;
            this.importer.Load(path);
            this.importName = "";
            this.importPath = null;
        }

        public object 
        GetModuleScope(string name)
        {
            return this.GetPythonContext().SystemStateModules[name];
        }

        private void
        MessWithSys()
        {
            // have not worked out how to test this -- cannot induce the mising 
            // executable, except during numpy import (er, before any of numpy
            // is executed...), but it definitely happens and is very upsetting.
            object sys = this.GetModuleScope("sys");
            Builtin.setattr(DefaultContext.Default, sys, "executable",
                Assembly.GetEntryAssembly().Location);
        }

        public object
        Import(string name)
        {
            this.MessWithSys();
            if (this.GetPythonContext().SystemStateModules.ContainsKey(name))
            {
                return this.GetModuleScope(name);
            }
            
            if (name == "numpy")
            {
                Console.WriteLine(@"Detected numpy import; faking out modules:
  parser
  mmap
  urllib2
  ctypes
  numpy.ma");
                this.CreateModule("parser");
                this.CreateModule("mmap");
                
                PythonModule urllib2 = this.CreateModule("urllib2");
                ScriptScope scope = this.GetModuleScriptScope(urllib2);
                scope.SetVariable("urlopen", new Object());
                scope.SetVariable("URLError", new Object());
                
                // ctypeslib specifically handles ctypes being None
                this.GetPythonContext().SystemStateModules["ctypes"] = null;
                
                this.CreateModule("numpy.ma");
                
            }
            
            this.importName = name;
            this.ExecInModule(String.Format("import {0}", name), this.scratchModule);
            this.importName = "";
            
            return this.GetModuleScope(name);
        }
        
        public override IntPtr
        PyImport_ImportModule(string name)
        {
            return this.Store(this.Import(name));
        }

        public override IntPtr
        PyImport_Import(IntPtr namePtr)
        {
            string name = (string)this.Retrieve(namePtr);
            return this.Store(this.Import(name));
        }

        private PythonModule
        CreateModule(string name)
        {
            PythonContext ctx = this.GetPythonContext();
            if (!ctx.SystemStateModules.ContainsKey(name))
            {
                return ctx.CreateModule(name, name, new Dictionary<string, object>(), ModuleOptions.PublishModule);
            }
            return null;
        }

        private void
        CreateModulesContaining(string name)
        {
            this.CreateModule(name);
            object innerScope = this.GetModuleScope(name);

            int lastDot = name.LastIndexOf('.');
            if (lastDot != -1)
            {
                this.CreateModulesContaining(name.Substring(0, lastDot));
                Scope outerScope = (Scope)this.GetModuleScope(name.Substring(0, lastDot));
                ScriptScope outerScriptScope = this.engine.CreateScope(outerScope.Dict);
                outerScriptScope.SetVariable(name.Substring(lastDot + 1), innerScope);
            }
        }

        public override IntPtr
        PyImport_AddModule(string name)
        {
            this.CreateModulesContaining(name);
            return this.Store(this.GetModuleScope(name));
        }
        
        public void 
        AddToPath(string path)
        {
            this.GetPythonContext().AddToPath(path);
        }
    }
}