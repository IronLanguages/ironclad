using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;

using IronPython.Hosting;
using IronPython.Runtime;
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
        PyImport_ImportModule(string name)
        {
            try
            {
                return this.Store(this.Import(name));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyImport_Import(IntPtr namePtr)
        {
            try
            {
                string name = (string)this.Retrieve(namePtr);
                return this.Store(this.Import(name));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyImport_AddModule(string name)
        {
            name = this.FixImportName(name);
            this.CreateModulesContaining(name);
            return this.Store(this.GetModule(name));
        }

        public override IntPtr
        PyImport_GetModuleDict()
        {
            Scope sys = this.python.SystemState;
            IntPtr modulesPtr = this.Store(ScopeOps.__getattribute__(sys, "modules"));
            this.RememberTempObject(modulesPtr);
            return modulesPtr;
        }

        public void 
        LoadModule(string path, string name)
        {
            this.importName = name;
            string dir = Path.GetDirectoryName(path);
            string library = Path.GetFileName(path);
            string previousDir = Environment.CurrentDirectory;
            Environment.CurrentDirectory = dir;
            try
            {
                this.importer.Load(library);
            }
            finally
            {
                Environment.CurrentDirectory = previousDir;
                this.importName = "";
            }
        }
    
        private string
        FixImportName(string name)
        {
            if (this.importName == "")
            {
                return name;
            }
            if (this.importName.Contains(name))
            {
                // WTF!? Contains!? Yes.
                // By rights, that should be EndsWith, but pysvn is evil.
                return this.importName;
            }
            return name;
        }

        private object
        Import(string name)
        {
            object module = this.GetModule(name);
            if (module != null)
            {
                return module;
            }
            
            this.importName = name;
            try
            {
                this.ExecInModule(String.Format("import {0}", name), this.scratchModule);
            }
            finally
            {
                this.importName = "";
            }
    
            return this.GetModule(name);
        }
        
        private Scope
        CreateModule(string name)
        {
            if (this.GetModule(name) == null)
            {
                PythonDictionary __dict__ = new PythonDictionary();
                __dict__["__name__"] = name;
                Scope module = new Scope(__dict__);
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
                Scope outerScope = (Scope)this.GetModule(name.Substring(0, lastDot));
                ScopeOps.__setattr__(outerScope, name.Substring(lastDot + 1), innerScope);
            }
        }
        
        public void
        PerpetrateNumpyFixes()
        {
            if (this.appliedNumpyHack)
            {
                return;
            }
            this.appliedNumpyHack = true;
            
            Console.WriteLine("Detected numpy import");
            Console.WriteLine("  faking out modules: mmap, nosetester, parser");
            this.CreateModule("parser");
            this.CreateModule("mmap");
            
            Scope nosetester = this.CreateModule("numpy.testing.nosetester");
            PythonDictionary NoseTesterDict = new PythonDictionary();
            NoseTesterDict["bench"] = NoseTesterDict["test"] = "This has been patched and broken by ironclad";
            PythonType NoseTesterClass = new PythonType(this.scratchContext, "NoseTester", new PythonTuple(), NoseTesterDict);
            ScopeOps.__setattr__(nosetester, "NoseTester", NoseTesterClass);
            ScopeOps.__setattr__(nosetester, "import_nose", new Object());
            ScopeOps.__setattr__(nosetester, "run_module_suite", new Object());
            ScopeOps.__setattr__(nosetester, "get_package_name", new Object());
        }

        public void
        PerpetrateScipyFixes()
        {
            if (this.appliedScipyHack)
            {
                return;
            }
            this.appliedScipyHack = true;
            Console.WriteLine("Detected scipy import");
            Console.WriteLine("  faking out numpy._import_tools.PackageLoader");
            this.ExecInModule(CodeSnippets.SCIPY_FIXES, this.scratchModule);
        }
    }
}
