
import os
import sys

class Loader(object):

    def __init__(self, path):
        self.path = path
        
    def load_module(self, name):
        if name not in sys.modules:
            _mapper.LoadModule(self.path, name)
            module = _mapper.GetModule(name)
            module.__file__ = self.path
            sys.modules[name] = module
            if '.' in name:
                parent_name, child_name = name.rsplit('.', 1)
                setattr(sys.modules[parent_name], child_name, module)
        return sys.modules[name]

class MetaImporter(object):

    def find_module(self, fullname, path=None):
        if fullname == 'numpy' or fullname.startswith('numpy.'):
            _mapper.PerpetrateNumpyFixes()
        if fullname == 'ctypes':
            raise ImportError('%s is not available in ironclad yet' % fullname)

        lastname = fullname.rsplit('.', 1)[-1]
        for d in (path or sys.path):
            pyd = os.path.join(d, lastname + '.pyd')
            if os.path.exists(pyd):
                return Loader(pyd)

        return None

# this should ensure that remove_sys_hacks is
# independent of what happens in this scope
class Lifetime(object):
    
    def __init__(self):
        self.meta_importer = MetaImporter()
        sys.meta_path.append(self.meta_importer)
        sys.__displayhook__ = sys.displayhook

    def remove_sys_hacks(self):
        sys.meta_path.remove(self.meta_importer)
        del sys.__displayhook__

remove_sys_hacks = Lifetime().remove_sys_hacks
