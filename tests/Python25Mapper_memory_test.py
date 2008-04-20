
import sys

import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.memory import OffsetPtr, CreateTypes

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from IronPython.Hosting import PythonEngine

from Ironclad import CPyMarshal, PythonMapper, Python25Mapper
from Ironclad.Structs import PyObject



class Python25Mapper_PyMem_Malloc_Test(unittest.TestCase):
    
    def testPyMem_Malloc_NonZero(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        
        resultPtr = mapper.PyMem_Malloc(123)
        try:
            self.assertEquals(allocs, [(resultPtr, 123)], "bad alloc")
        finally:
            Marshal.FreeHGlobal(resultPtr)
    
    
    def testPyMem_Malloc_Zero(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        
        resultPtr = mapper.PyMem_Malloc(0)
        try:
            self.assertEquals(allocs, [(resultPtr, 1)], "bad alloc")
        finally:
            Marshal.FreeHGlobal(resultPtr)
    
    
    def testPyMem_Malloc_Failure(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        resultPtr = mapper.PyMem_Malloc(sys.maxint)
        self.assertEquals(resultPtr, IntPtr.Zero, "bad alloc")
        
        
class Python25Mapper_PyMem_Free_Test(unittest.TestCase):
    
    def testPyMem_Free_NonNull(self):
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], frees))
        
        ptr = mapper.PyMem_Malloc(123)
        mapper.PyMem_Free(ptr)
        
        self.assertEquals(frees, [ptr], "did not free")
    

    def testPyMem_Free_Null(self):
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], frees))
        
        mapper.PyMem_Free(IntPtr.Zero)
        
        self.assertEquals(frees, [], "freed inappropriately")
        


suite = makesuite(
    Python25Mapper_PyMem_Malloc_Test,
    Python25Mapper_PyMem_Free_Test,
)

if __name__ == '__main__':
    run(suite)