
# no code that is not executed on the first pass through this code 
# should depend on anything in this namespace; if you want to use it,
# make sure it's tacked onto an instance.

class Loader(object):

    def __init__(self, mapper, path):
        self.mapper = mapper
        self.path = path

    def load_module(self, name):
        import sys
        if name not in sys.modules:
            self.mapper.LoadModule(self.path, name)
            sys.modules[name] = self.mapper.GetModule(name)
        return sys.modules[name]


class MetaImporter(object):

    def __init__(self, loader, mapper):
        self.loader = loader
        self.mapper = mapper
        self.patched_for_matplotlib = False

    def fix_matplotlib(self):
        # much easier to do this in Python than in C#
        if self.patched_for_matplotlib:
            return
        
        self.patched_for_matplotlib = True
        print 'Detected matplotlib import'
        print '  patching out csv, math.log10'
        
        import sys
        sys.modules['csv'] = object()
        
        import math
        true_log10 = math.log10
        def my_log10(arg):
            if isinstance(arg, float):
                arg = float(arg)
            return true_log10(arg)
        math.log10 = my_log10

    def find_module(self, fullname, path=None):
        matches = lambda partialname: fullname == partialname or fullname.startswith(partialname + '.')
        if matches('numpy'):
            self.mapper.PerpetrateNumpyFixes()
        elif matches('scipy'):
            self.mapper.PerpetrateScipyFixes()
        elif matches('matplotlib'):
            self.fix_matplotlib()
        elif matches('ctypes'):
            raise ImportError('%s is not available in ironclad yet' % fullname)

        import os
        import sys
        lastname = fullname.rsplit('.', 1)[-1]
        for d in (path or sys.path):
            pyd = os.path.join(d, lastname + '.pyd')
            if os.path.exists(pyd):
                return self.loader(self.mapper, pyd)

        return None


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
