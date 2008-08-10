using System;
using System.Collections.Generic;

using IronPython.Runtime;

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
        
        public object
        Import(string name)
        {
            if (this.GetPythonContext().SystemStateModules.ContainsKey(name))
            {
                return this.GetModuleScope(name);
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

        private void
        CreateModulesContaining(string name)
        {
            PythonContext ctx = this.GetPythonContext();
            if (!ctx.SystemStateModules.ContainsKey(name))
            {
                ctx.CreateModule(name, name, new Dictionary<string, object>(), ModuleOptions.PublishModule);
            }
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