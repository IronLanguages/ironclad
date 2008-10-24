using System;
using System.Reflection;
using System.Collections.Generic;

using IronPython.Hosting;
using IronPython.Runtime;

using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Hosting.Providers;
using Microsoft.Scripting.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
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

        public override IntPtr
        PyImport_AddModule(string name)
        {
            this.CreateModulesContaining(name);
            return this.Store(this.GetModule(name));
        }

        public void 
        LoadModule(string path, string name)
        {
            this.importName = name;
            this.importer.Load(path);
            this.importName = "";
        }

        public object
        Import(string name)
        {
            object module = this.GetModule(name);
            if (module != null)
            {
                return module;
            }
            
            if (name == "numpy")
            {
                this.PerpetrateNumpyFixes();
            }
            
            this.importName = name;
            this.ExecInModule(String.Format("import {0}", name), this.scratchModule);
            this.importName = "";
    
            return this.GetModule(name);
        }
        
        private ScriptScope
        CreateModule(string name)
        {
            if (this.GetModule(name) == null)
            {
                PythonDictionary __dict__ = new PythonDictionary();
                __dict__["__name__"] = name;
                ScriptScope module = this.engine.CreateScope(__dict__);
                this.AddModule(name, module);
                return module;
            }
            return null;
        }

        private void
        CreateModulesContaining(string name)
        {
            this.CreateModule(name);
            object innerScope = this.GetModule(name);

            int lastDot = name.LastIndexOf('.');
            if (lastDot != -1)
            {
                this.CreateModulesContaining(name.Substring(0, lastDot));
                ScriptScope outerScope = this.GetModuleScriptScope((Scope)this.GetModule(name.Substring(0, lastDot)));
                outerScope.SetVariable(name.Substring(lastDot + 1), innerScope);
            }
        }

        private void
        PerpetrateNumpyFixes()
        {
            Console.WriteLine("Detected numpy import");
            Console.WriteLine("  faking out modules: parser, mmap, urllib2, ctypes, numpy.testing");
            this.CreateModule("parser");
            this.CreateModule("mmap");

            ScriptScope urllib2 = this.CreateModule("urllib2");
            urllib2.SetVariable("urlopen", new Object());
            urllib2.SetVariable("URLError", new Object());

            // ctypeslib specifically handles ctypes being None
            ScriptScope sys = Python.GetSysModule(this.Engine);
            PythonDictionary modules = (PythonDictionary)sys.GetVariable("modules");
            modules["ctypes"] = null;

            ScriptScope testing = this.CreateModule("numpy.testing");
            this.ExecInModule(CodeSnippets.FAKE_numpy_testing_CODE, testing);
        }
    }
}
