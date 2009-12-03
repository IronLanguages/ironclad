
# remember -X:Frames
# expect 133 tests, 3 errors, 1 fail

import os, sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

from tests.utils.blacklists import BlacklistConfig
blacklist = r'tests\extra\h5py_test_blacklist'
config = BlacklistConfig(blacklist)

path = r'C:\Program Files\IronPython 2.6\lib\site-packages\h5py'
if len(sys.argv) > 1:
    path = os.path.join(path, *(sys.argv[1:]))
    sys.argv = sys.argv[:1]

import nose
nose.run(defaultTest=path, config=config)
