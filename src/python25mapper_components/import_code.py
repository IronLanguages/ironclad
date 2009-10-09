
# no code that is not executed on the first pass through this code 
# should depend on anything in this namespace; if you want to use it,
# make sure it's tacked onto an instance.

class Loader(object):

    def __init__(self, mapper, path):
        self.mapper = mapper
        self.path = path

    def load_module(self, name):
        import os, sys
        
        for m in sys.modules.values():
            if hasattr(m, '__file__'):
                if os.path.abspath(m.__file__) == os.path.abspath(self.path):
                    return m
        
        if name not in sys.modules:
            self.mapper.LoadModule(self.path, name)
            sys.modules[name] = self.mapper.GetModule(name)
        return sys.modules[name]


class MetaImporter(object):

    def __init__(self, loader, mapper):
        self.loader = loader
        self.mapper = mapper
        self.patched_for_h5py = False
        self.patched_numpy_testing = False
        self.patched_h5py__stub = False
        
    def find_module(self, fullname, path=None):
        matches = lambda partialname: fullname == partialname or fullname.startswith(partialname + '.')
        if matches('numpy'):
            self.mapper.PerpetrateNumpyFixes()
        elif matches('scipy'):
            self.mapper.PerpetrateScipyFixes()
        elif matches('h5py'):
            self.fix_h5py()
        elif matches('_ctypes'):
            # _ctypes.pyd will mask ipy _ctypes, I think
            return None
        
        self.late_fixes()
        
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
        print 'Detected h5py import'
        print '  patching out sys.getfilesystemencoding'
        
        def getutf8():
            return 'utf-8'
        import sys
        sys.getfilesystemencoding = getutf8

    def late_fixes(self):
        # hacka hacka hacka!
        # don't look at me like that.
        self.patch_numpy_testing()
        
    def patch_numpy_testing(self):
        if self.patched_numpy_testing:
            return
        
        import sys
        if 'numpy.testing' not in sys.modules:
            return
        
        print '  patching numpy.testing.NumpyTest, NumpyTestCase'
        self.patched_numpy_testing = True
        
        import unittest
        sys.modules['numpy.testing'].NumpyTest = object()
        sys.modules['numpy.testing'].NumpyTestCase = unittest.TestCase

class Lifetime(object):
    
    def __init__(self, loader, mapper):
        import sys
        self.meta_importer = MetaImporter(loader, mapper)
        sys.meta_path.append(self.meta_importer)
        sys.__displayhook__ = sys.displayhook

    def remove_sys_hacks(self):
        import sys
        sys.meta_path.remove(self.meta_importer)
        del sys.__displayhook__

remove_sys_hacks = Lifetime(Loader, _mapper).remove_sys_hacks
