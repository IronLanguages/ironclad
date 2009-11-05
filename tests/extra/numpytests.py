
# note: I strongly recommend that you change core/tests/test_umath.py
# such that is_longdouble_finfo_bogus returns True -- otherwise it will
# take several minutes to import the file, and look as if it's wedged.

np_path = r'C:\Program Files\IronPython 2.6\lib\site-packages\numpy'
np_blacklist = r'tests\extra\numpy_test_blacklist'
np_excludes = r'distutils f2py'.split()

import re, sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

from tests.utils.blacklists import BlacklistConfig
config = BlacklistConfig(np_blacklist, np_excludes)

import nose
nose.run(defaultTest=np_path, config=config)
