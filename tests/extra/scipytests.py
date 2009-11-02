
sp_path = r'C:\Program Files\IronPython 2.6\lib\site-packages\scipy'
sp_blacklist = r'tests\extra\scipy_test_blacklist'

import re, sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

from tests.utils.blacklists import BlacklistConfig
config = BlacklistConfig(sp_blacklist)

import nose
nose.run(defaultTest=sp_path, config=config)


# cluster: 152 tests ok
# fftpack: 25 tests ok
# integrate: 16 tests ok
# interpolate: cannot import factorial
# io: 33 tests, 1 error (import gzip)
# lib: 176 tests, 39 errors
# linalg: 402 tests, 51 errors
# maxentropy: 2 tests ok
# misc: needs PIL, which doesn't work in ipy ATM
# ndimage: 414 tests ok
# odr: 4 tests ok
# optimize: 29 tests ok
# signal: cannot import factorial
# sparse: 418 tests, 19 errors
# spatial: 229 tests ok (some pretty slow though)
# special: 368 tests ok
# stats: 215 tests ok
# weave: needs signal module