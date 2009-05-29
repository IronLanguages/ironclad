import os
import sys
from tests.utils.schnoz import Schnoz


if sys.platform == 'cli':
    # we expect this to be run from project root
    sys.path.insert(0, "build")
    import ironclad
    ironclad.patch_native_filenos()


import h5py

if __name__ == "__main__":
    h5pytester = Schnoz(name="h5py", lib_path= r"C:\Python25\Lib\site-packages\h5py", data_dir=os.path.dirname(__file__))
    h5pytester.main([""], 2)
