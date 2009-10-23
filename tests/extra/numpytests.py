
np_path = r'C:\Program Files\IronPython 2.6\lib\site-packages\numpy'
np_blacklist = r'tests\extra\numpy_test_blacklist'


import sys
sys.path.append('build')

import ironclad
ironclad.patch_native_filenos()

import nose
config = nose.config.Config()
config.verbosity = 3

import re
config.exclude = (re.compile('distutils'), re.compile('f2py'))

from tests.utils.blacklists import BlacklistPlugins
config.plugins = BlacklistPlugins(np_blacklist)

nose.run(defaultTest=np_path, config=config)