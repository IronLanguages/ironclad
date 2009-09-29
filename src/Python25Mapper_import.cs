using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;

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
            IntPtr modulesPtr = this.Store(this.python.SystemState.__dict__["modules"]);
            this.RememberTempObject(modulesPtr);
            return modulesPtr;
        }

        public void 
        LoadModule(string path, string name)
        {
            this.EnsureGIL();
            this.importNames.Push(name);
            this.importFiles.Push(path);
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
                this.importNames.Pop();
                this.importFiles.Pop();
                this.ReleaseGIL();
            }
        }
    
        private string
        FixImportName(string name)
        {
            string importName = this.importNames.Peek();
            if (importName == "")
            {
                return name;
            }
            if (importName.Contains(name))
            {
                // WTF!? Contains!? Yes.
                // By rights, that should be EndsWith, but pysvn is evil.
                return importName;
            }
            return name;
        }

        private PythonModule
        Import(string name)
        {
            PythonModule module = this.GetModule(name);
            if (module != null)
            {
                return module;
            }
            
            this.importNames.Push(name);
            try
            {
                // TODO: yes, on inspection, I'm sure this is a stupid way to do it
                this.ExecInModule(String.Format("import {0}", name), this.scratchModule);
            }
            finally
            {
                this.importNames.Pop();
            }
    
            return this.GetModule(name);
        }
        
        private PythonModule
        CreateModule(string name)
        {
            PythonModule module = this.GetModule(name);
            if (module == null)
            {
                module = new PythonModule();
                module.__dict__["__name__"] = name;
                this.AddModule(name, module);
            }
            return module;
        }

        private void
        CreateModulesContaining(string name)
        {
            PythonModule inner = this.CreateModule(name);
            int lastDot = name.LastIndexOf('.');
            if (lastDot != -1)
            {
                this.CreateModulesContaining(name.Substring(0, lastDot));
                PythonModule outer = this.GetModule(name.Substring(0, lastDot));
                outer.__dict__[name.Substring(lastDot + 1)] = inner;
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
            Console.WriteLine("  faking out modules: nosetester, parser");

            PythonModule nosetester = this.CreateModule("numpy.testing.nosetester");
            nosetester.__setattr__("import_nose", new Object());
            nosetester.__setattr__("run_module_suite", new Object());
            nosetester.__setattr__("get_package_name", new Object());

            PythonDictionary __dict__ = new PythonDictionary();
            __dict__["bench"] = __dict__["test"] = "This has been patched and broken by ironclad";
            PythonType NoseTester = new PythonType(this.scratchContext, "NoseTester", new PythonTuple(), __dict__);
            nosetester.__setattr__("NoseTester", NoseTester);
            
            this.CreateModule("parser");
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
