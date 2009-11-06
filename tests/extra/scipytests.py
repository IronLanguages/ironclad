
# remember -X:FullFrames

# I strongly recommend you change line 2 of scipy/interpolate/polyint.py
# to import factorial from scipy.misc (not just scipy). Not sure the true
# source of the problem, but doing this allows you run lots more tests.

import os, sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

from tests.utils.blacklists import BlacklistConfig
blacklist = r'tests\extra\scipy_test_blacklist'
config = BlacklistConfig(blacklist)

path = r'C:\Program Files\IronPython 2.6\lib\site-packages\scipy'
if len(sys.argv) > 1:
    path = os.path.join(path, *(sys.argv[1:]))
    sys.argv = sys.argv[:1]

import nose
nose.run(defaultTest=path, config=config)

# last full run had 2681 tests, 143 errors, 17 failures
# blacklist has had some slow tests added since then

# cluster: 159 tests ok
# fftpack: 45 tests, 16 failures
# integrate: 17 tests, 1 failure
# interpolate: with factorial import from misc in polyint.py: 125 tests, 16 errors
# io: 36 tests, 4(?) errors
# lib: 176 tests, 39 errors
# linalg: 402 tests, 51 errors
# maxentropy: 2 tests ok
# misc: tests need PIL, which doesn't work in ipy ATM
# ndimage: 414 tests ok
# odr: 4 tests ok
# optimize: 33 tests, 4 errors
# signal: with factorial import from misc in polyint.py: 40 tests ok
# sparse: 418 tests, 19 errors
# spatial: 229 tests ok (some pretty slow though)
# special: 368 tests ok
# stats: 215 tests ok
# weave: needs signal (I believe this is signal, not scipy.signal)