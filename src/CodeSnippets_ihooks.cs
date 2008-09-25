namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string INSTALL_IMPORT_HOOK_CODE = @"
import ihooks
import imp

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
