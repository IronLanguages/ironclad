
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, PythonMapper
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

    
    @WithMapper
    def testPyMapping_GetItemString(self, mapper, _):
        data = {'foo': 'bar'}
        class Mapping(object):
            def __getitem__(self, key):
                return data[key]
        
        mptr = mapper.Store(Mapping())
        fooresult = mapper.PyMapping_GetItemString(mptr, 'foo')
        self.assertEquals(mapper.Retrieve(fooresult), 'bar')
        
        self.assertEquals(mapper.PyMapping_GetItemString(mptr, 'baz'), IntPtr.Zero)
        self.assertMapperHasError(mapper, KeyError)
        
        


suite = makesuite(
    MappingTest,
)

if __name__ == '__main__':
    run(suite)
