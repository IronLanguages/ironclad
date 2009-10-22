
import sys
import unittest
import tests.utils.loadassemblies

from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes

from Ironclad import PythonMapper

class TrivialMapperSubclass(PythonMapper):
    pass


def _WithMapper(func, mapperCls):
    def patched(*args):
        mapper = mapperCls()
        deallocTypes = CreateTypes(mapper)
        deallocs = [mapper.Dispose, deallocTypes]
        newArgs = args + (mapper, deallocs.append)
        try:
            return func(*newArgs)
        finally:
            for dealloc in deallocs:
                dealloc()
    return patched

WithMapper = lambda f: _WithMapper(f, PythonMapper)
WithMapperSubclass = lambda f: _WithMapper(f, TrivialMapperSubclass)


class my_stderr(object):
    def __init__(self, calls):
        self.calls = calls
    def write(self, *args):
        self.calls.append(args)

def WithPatchedStdErr(func):
    def patched(*args):
        calls = []
        old = sys.stderr
        sys.stderr = my_stderr(calls)
        newArgs = args + (calls,)
        try:
            return func(*newArgs)
        finally:
            sys.stderr = old
    return patched
    


class TestCase(unittest.TestCase):
    
    def tearDown(self):
        gcwait()
        unittest.TestCase.tearDown(self)
        
        
    def assertMapperHasError(self, mapper, error):
        if error:
            self.assertEquals(isinstance(mapper.LastException, error), True, "wrong error set on mapper")
            mapper.LastException = None
        else:
            self.assertEquals(mapper.LastException, None)