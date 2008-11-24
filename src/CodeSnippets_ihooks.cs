namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string INSTALL_IMPORT_HOOK_CODE = @"
import ihooks
import imp

CLR_MODULE = object()

class _IroncladHooks(ihooks.Hooks):

    def get_suffixes(self):
        suffixes = [('.pyd', 'rb', imp.C_EXTENSION)]
        suffixes.extend(imp.get_suffixes())
        return suffixes

    def load_dynamic(self, name, filename, file):
        _mapper.LoadModule(filename, name)
        module = _mapper.GetModule(name)
        self.modules_dict()[name] = module
        return module


class _IroncladModuleLoader(ihooks.ModuleLoader):
    
    def find_module(self, name, path=None):
        if name == 'numpy' or name.startswith('numpy.'):
            _mapper.PerpetrateNumpyFixes()
        if _mapper.IsClrModule(name):
            return None, None, CLR_MODULE
        return ihooks.ModuleLoader.find_module(self, name, path)


    def load_module(self, name, stuff):
        file, filename, info = stuff
        if info is CLR_MODULE:
            return _mapper.LoadClrModule(name)
        return ihooks.ModuleLoader.load_module(self, name, stuff)
        

class _IroncladModuleImporter(ihooks.ModuleImporter):

    # copied from ihooks.py
    def determine_parent(self, globals):
        if not globals or not '__name__' in globals:
            return None
        pname = globals['__name__']
        if '__path__' in globals:
            parent = self.modules[pname]
            # 'assert globals is parent.__dict__' always fails --
            # but the underlying data store is actually the same
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

_importer = _IroncladModuleImporter(_IroncladModuleLoader())
_importer.set_hooks(_IroncladHooks())
_importer.install()
";
    }
}
