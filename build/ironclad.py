import os
_dirname = os.path.dirname(__file__)

import clr
from System.Reflection import Assembly
clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))
from Ironclad import Python25Mapper
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))

import imp
import ihooks

class _CextHooks(ihooks.Hooks):

    def get_suffixes(self):
        suffixes = [('.pyd', 'rb', imp.C_EXTENSION)]
        suffixes.extend(imp.get_suffixes())
        return suffixes

    def load_dynamic(self, name, filename, file):
        _mapper.LoadModule(filename)
        module = _mapper.GetModule(name)
        self.modules_dict()[name] = module
        return module


class _OddModuleImporter(ihooks.ModuleImporter):

    # copied from ihooks.py
    def determine_parent(self, globals):
        if not globals or not "__name__" in globals:
            return None
        pname = globals['__name__']
        if "__path__" in globals:
            parent = self.modules[pname]
            # 'assert globals is parent.__dict__' always fails --
            # I think an ipy module dict is some sort of funky 
            # wrapper around a Scope, so the underlying data store
            # actually is the same.
            assert globals == parent.__dict__
            return parent
        if '.' in pname:
            i = pname.rfind('.')
            pname = pname[:i]
            parent = self.modules[pname]
            assert parent.__name__ == pname
            return parent
        return None

_importer = _OddModuleImporter()
_importer.set_hooks(_CextHooks())
_importer.install()

def shutdown():
    _mapper.Dispose()