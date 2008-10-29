
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject


class MappingTest(TestCase):

    @WithMapper
    def testPyMapping_Check(self, mapper, _):
        class Mapping(object):
            def __getitem__(self, _):
                return True
        
        # I'm interpreting this to mean "has __getitem__, and isn't a type"
        mappings = ([], (), {}, "", Mapping())
        for mapping in mappings:
            ptr = mapper.Store(mapping)
            self.assertEquals(mapper.PyMapping_Check(ptr), 1)
            mapper.DecRef(ptr)
        
        
        notmappings = (12, object(), slice(1, 2, 3), Mapping)
        for notmapping in notmappings:
            ptr = mapper.Store(notmapping)
            self.assertEquals(mapper.PyMapping_Check(ptr), 0)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)


suite = makesuite(
    MappingTest,
)

if __name__ == '__main__':
    run(suite)
