
from tools.utils import read_interesting_lines

import nose
from nose.selector import Selector
from nose.plugins import Plugin
from nose.plugins.manager import DefaultPluginManager

trim = (len('<unbound method '), -1)
def extract_ubm_names(ubm):
    r = repr(ubm)[slice(*trim)]
    return r.split('.')

def if_wanted(f):
    basemeth = getattr(Selector, f.__name__)
    def g(self, x):
        if basemeth(self, x):
            return f(self, x)
    return g

class BlacklistSelector(Selector):

    def __init__(self, config, blacklist):
        Selector.__init__(self, config)
        self.blacklist = blacklist
        self.mod = None

    def _want(self, *args):
        return args not in self.blacklist
        
    @if_wanted
    def wantModule(self, m):
        self.mod = m.__name__
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



def BlacklistPlugins(blacklist_file):
    blacklist_contents = read_interesting_lines(blacklist_file)
    blacklist = set(map(tuple, [l.split('.') for l in blacklist_contents]))
    
    class BlacklistPlugin(Plugin):
        enabled = True
        def configure(self, _, __):
            pass
        def prepareTestLoader(self, loader):
            loader.selector = BlacklistSelector(loader.config, blacklist)
    
    class BlacklistPluginManager(DefaultPluginManager):
        def loadPlugins(self):
            self.addPlugin(BlacklistPlugin())

    return BlacklistPluginManager()