
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator

from System.Runtime.InteropServices import Marshal

from Ironclad import Python25Mapper
from Ironclad.Structs import PyObject
from IronPython.Hosting import PythonEngine




class Python25MapperDictTest(unittest.TestCase):

    def testPyDict_New(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        
        dictPtr = mapper.PyDict_New()
        self.assertEquals(mapper.RefCount(dictPtr), 1, "bad refcount")
        self.assertEquals(allocs, [(dictPtr, Marshal.SizeOf(PyObject))], "did not allocate as expected")
        
        dictObj = mapper.Retrieve(dictPtr)
        self.assertEquals(dictObj, {}, "retrieved unexpected value")
        
        mapper.DecRef(dictPtr)
        self.assertEquals(mapper.RefCount(dictPtr), 0, "did not dump reference")
        self.assertEquals(frees, [dictPtr], "did not release memory")


suite = makesuite(
    Python25MapperDictTest,
)

if __name__ == '__main__':
    run(suite)