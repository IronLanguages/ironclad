import os.path
import sys
from tests.utils.schnoz import Schnoz


if sys.platform == 'cli':
    # we expect this to be run from project root
    sys.path.insert(0, "build")
    import ironclad


class Bunch(object):
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

from numpy._import_tools import PackageLoader

real__init__ = PackageLoader.__init__
def fake__init__(self):
    import scipy
    original = sys._getframe
    sys._getframe = lambda *_: Bunch(f_locals={}, f_globals=scipy.__dict__)
    real__init__(self)
    sys._getframe = original
PackageLoader.__init__ = fake__init__


import scipy
numpy_path = r"C:\Python25\Lib\site-packages\scipy"
dirs = ['fftpack', 'ndimage', 'special']

if __name__ == "__main__":
    numpytester = Schnoz(name="scipy", lib_path=numpy_path, data_dir=os.path.dirname(__file__))
    numpytester.main(dirs)

