
sp_path = r'C:\Program Files\IronPython 2.6\lib\site-packages\scipy\sparse\tests\test_base.py'
sp_blacklist = r'tests\extra\scipy_test_blacklist'

import re, sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

from tests.utils.blacklists import BlacklistConfig
config = BlacklistConfig(sp_blacklist)

import nose
nose.run(defaultTest=sp_path, config=config)


# interpolate: cannot import factorial
# io: cannot import zlib
# lib: 176 tests, 39 errors
# linalg: 402 tests, 51 errors
# misc: needs PIL
# signal: cannot import factorial
# sparse: 418 tests, 19 errors
# stats: (wedged after many passes and some errors)
# weave: cannot import zlib