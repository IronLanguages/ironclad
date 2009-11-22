
from tools.utils.io import read_lines

import re

import nose
from nose.config import Config
from nose.selector import Selector
from nose.plugins import Plugin
from nose.plugins.manager import DefaultPluginManager

trim = slice(len('<unbound method '), -1)
def extract_ubm_names(ubm):
    r = repr(ubm)[trim]
    return r.split('.')

def if_wanted(f):
    basemeth = getattr(Selector, f.__name__)
    def g(self, x):
        if basemeth(self, x):
            return f(self, x)
    return g

class BlacklistSelector(Selector):

    def __init__(self, config, test_blacklist, file_blacklist):
        Selector.__init__(self, config)
        self.test_blacklist = test_blacklist
        self.file_blacklist = file_blacklist
        self.mod = None
        
    @if_wanted
    def wantFile(self, f):
        for f_end in self.file_blacklist:
            if f.endswith(f_end):
                return False
        return True

    def _want(self, *args):
        return args not in self.test_blacklist
        
    @if_wanted
    def wantModule(self, m):
        self.mod = m.__name__.split('.')[-1]
        return self._want(self.mod)
        
    @if_wanted
    def wantFunction(self, f):
        return self._want(self.mod, f.__name__)

    @if_wanted
    def wantClass(self, c):
        return self._want(self.mod, c.__name__)

    @if_wanted
    def wantMethod(self, m):
        cls, meth = extract_ubm_names(m)
        return self._want(self.mod, cls, meth)


def _read_blacklist(f):
    tests, files = set(), set()
    if f:
        for line in read_lines(f):
            if line.endswith('.py'):
                files.add(line)
            else:
                tests.add(tuple(line.split('.')))
    return tests, files


def BlacklistPlugins(blacklist_file):
    tests, files = _read_blacklist(blacklist_file)
    class BlacklistPlugin(Plugin):
        enabled = True
        def configure(self, _, __):
            pass
        def prepareTestLoader(self, loader):
            loader.selector = BlacklistSelector(loader.config, tests, files)
    
    class BlacklistPluginManager(DefaultPluginManager):
        def loadPlugins(self):
            self.addPlugin(BlacklistPlugin())

    return BlacklistPluginManager()


def BlacklistConfig(blacklist_file, excludes=()):
    config = Config()
    config.verbosity = 3
    config.plugins = BlacklistPlugins(blacklist_file)
    if excludes: config.exclude = map(re.compile, excludes)
    return config


