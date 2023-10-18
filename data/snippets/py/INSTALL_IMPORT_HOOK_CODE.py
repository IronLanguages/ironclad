
# no code that is not executed on the first pass through this code 
# should depend on anything in this namespace; if you want to use it,
# make sure it's tacked onto an instance.

class Loader(object):

    def __init__(self, mapper, path):
        self.mapper = mapper
        self.path = path

    def load_module(self, name):
        import os, sys
        
        abspath = os.path.abspath(self.path)
        for m in sys.modules.values():
            if type(m).__name__ != 'namespace#' and hasattr(m, '__file__'):
                if os.path.abspath(m.__file__) == abspath:
                    return m
        
        if name not in sys.modules:
            self.mapper.LoadModule(self.path, name)
            sys.modules[name] = self.mapper.GetModule(name)
        return sys.modules[name]


class PydImporter(object):

    def __init__(self, loader, mapper):
        self.loader = loader
        self.mapper = mapper
        self.patched_for_h5py = False
        
    # TODO: Python 3.4: find_module is obsolete; replace with find_spec
    def find_module(self, fullname, path=None):
        matches = lambda partialname: fullname == partialname or fullname.startswith(partialname + '.')
        if matches('h5py'):
            self.fix_h5py()
        elif matches('_ctypes'):
            # _ctypes.pyd will mask ipy _ctypes, I think
            return None
        
        import os
        import sys
        lastname = fullname.rsplit('.', 1)[-1]
        for d in (path or sys.path):
            pyd = os.path.join(d, lastname + '.pyd')
            if os.path.isfile(pyd):
                return self.loader(self.mapper, pyd)

        return None

    def fix_h5py(self):
        if self.patched_for_h5py:
            return
        
        self.patched_for_h5py = True
        print('ironclad: detected h5py, patching out sys.getfilesystemencoding')
        
        def getutf8():
            return 'utf-8'
        import sys
        sys.getfilesystemencoding = getutf8

class Lifetime(object):
    
    def __init__(self, loader, mapper):
        import sys
        self.meta_importer = PydImporter(loader, mapper)
        sys.meta_path.append(self.meta_importer)

    def remove_sys_hacks(self):
        import sys
        sys.meta_path.remove(self.meta_importer)

remove_sys_hacks = Lifetime(Loader, _mapper).remove_sys_hacks
