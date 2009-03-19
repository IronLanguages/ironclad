import os.path
import sys
from tests.utils.schnoz import Schnoz


if sys.platform == 'cli':
    # we expect this to be run from project root
    sys.path.insert(0, "build")
    import ironclad


import h5py
if __name__ == "__main__":
    numpytester = Schnoz(name="h5py", lib_path= r"C:\Python25\Lib\site-packages\h5py", data_dir=os.path.dirname(__file__))
    numpytester.main([""])
