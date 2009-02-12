
import unittest
import tests.utils.loadassemblies

from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes

from Ironclad import Python25Mapper

class TrivialP25MSubclass(Python25Mapper):
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

WithMapper = lambda f: _WithMapper(f, Python25Mapper)
WithMapperSubclass = lambda f: _WithMapper(f, TrivialP25MSubclass)

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