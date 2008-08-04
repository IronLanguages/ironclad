using System;


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
        
        public void 
        AddToPath(string path)
        {
            this.GetPythonContext().AddToPath(path);
        }
    }
}