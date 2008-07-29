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
        
        private const string INSTALL_IMPORT_HOOK_CODE = @"
import ihooks
import imp

class _IroncladHooks(ihooks.Hooks):

    def get_suffixes(self):
        suffixes = [('.pyd', 'rb', imp.C_EXTENSION)]
        suffixes.extend(imp.get_suffixes())
        return suffixes

    def load_dynamic(self, name, filename, file):
        _mapper.LoadModule(filename, name)
        module = _mapper.GetModuleScope(name)
        self.modules_dict()[name] = module
        return module


class _IroncladModuleImporter(ihooks.ModuleImporter):

    # copied from ihooks.py
    def determine_parent(self, globals):
        if not globals or not '__name__' in globals:
            return None
        pname = globals['__name__']
        if '__path__' in globals:
            parent = self.modules[pname]
            # 'assert globals is parent.__dict__' always fails --
            # I think an ipy module dict is some sort of funky 
            # wrapper around a Scope, so the underlying data store
            # actually is the same.
            assert len(globals) == len(parent.__dict__)
            for (k, v) in globals.iteritems():
                assert parent.__dict__[k] is v
            return parent
        if '.' in pname:
            i = pname.rfind('.')
            pname = pname[:i]
            parent = self.modules[pname]
            assert parent.__name__ == pname
            return parent
        return None

_importer = _IroncladModuleImporter()
_importer.set_hooks(_IroncladHooks())
_importer.install()
";
    }
}