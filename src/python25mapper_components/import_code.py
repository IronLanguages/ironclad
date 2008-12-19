import sys
import os

def loader(path):
    class Loader(object):
        def load_module(self, name):
            if name not in sys.modules:
                _mapper.LoadModule(path, name)
                module = _mapper.GetModule(name)
                module.__file__ = path
                sys.modules[name] = module
                if '.' in name:
                    parent_name, child_name = name.rsplit('.', 1)
                    setattr(sys.modules[parent_name], child_name, module)
            return sys.modules[name]
    return Loader()

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
                return loader(pyd)

        return None


sys.meta_path = [MetaImporter()]


