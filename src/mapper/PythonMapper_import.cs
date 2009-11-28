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
    public partial class PythonMapper : PythonApi
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
            IntPtr modulesPtr = this.Store(this.python.SystemState.Get__dict__()["modules"]);
            this.DecRefLater(modulesPtr);
            return modulesPtr;
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
                // TODO: there must be a better way to do this
                return (PythonModule)this.CreateFromSnippet(
                    String.Format(CodeSnippets.IMPORT_TEMPLATE, name), "_ironclad_module");
            }
            finally
            {
                this.importNames.Pop();
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
    }
}
