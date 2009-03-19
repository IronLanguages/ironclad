import os.path
import sys
from tests.utils.schnoz import Schnoz


if sys.platform == 'cli':
    # we expect this to be run from project root
    sys.path.insert(0, "build")
    import ironclad

import numpy
def my_assert_raises(exc, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
    except exc:
        pass
    else:
        raise AssertionError("wrong exception, or no exception")
numpy.testing.assert_raises = my_assert_raises

numpy_path = r"C:\Python25\Lib\site-packages\numpy"
dirs = ['core', 'fft', 'lib', 'linalg', 'ma', 'oldnumeric', 'random']

if __name__ == "__main__":
    numpytester = Schnoz(name="numpy", lib_path=numpy_path, data_dir=os.path.dirname(__file__))
    numpytester.main(dirs)

