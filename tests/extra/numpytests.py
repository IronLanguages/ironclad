
# remember -X:Frames
# numpy 1.3: expect 1702 tests, 144 errors, 17 failures
# numpy 1.4: expect 2148 tests, 202 errors, 49 failures

# note: I strongly recommend that you change core/tests/test_umath.py
# such that is_longdouble_finfo_bogus returns True -- otherwise it will
# take several minutes to import the file, and look as if it's wedged.

import os, sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

from tests.utils.blacklists import BlacklistConfig
blacklist = r'tests\extra\numpy_test_blacklist'
config = BlacklistConfig(blacklist)

path = r'C:\Program Files\IronPython 2.6\Lib\site-packages\numpy'
if len(sys.argv) > 1:
    path = os.path.join(path, *(sys.argv[1:]))
    sys.argv = sys.argv[:1]

import nose
nose.run(defaultTest=path, config=config)
