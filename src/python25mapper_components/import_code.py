import sys
import os

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
        if fullname in ('_hashlib', 'ctypes'):
            raise ImportError('%s is not available in ironclad yet' % fullname)

        lastname = fullname.rsplit('.', 1)[-1]
        for d in (path or sys.path):
            pyd = os.path.join(d, lastname + '.pyd')
            if os.path.exists(pyd):
                return Loader(pyd)

        return None

meta_importer = MetaImporter()
sys.meta_path.append(meta_importer)

def remove_meta_importer():
    sys.meta_path.remove(meta_importer)
