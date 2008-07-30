
import sys

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.allocators import GetAllocatingTestAllocator

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import Python25Mapper



class Python25Mapper_PyMem_Malloc_Test(TestCase):
    
    def testPyMem_Malloc_NonZero(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        
        resultPtr = mapper.PyMem_Malloc(123)
        self.assertEquals(allocs, [(resultPtr, 123)], "bad alloc")
        mapper.Dispose()
    
    
    def testPyMem_Malloc_Zero(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        
        resultPtr = mapper.PyMem_Malloc(0)
        self.assertEquals(allocs, [(resultPtr, 1)], "bad alloc")
        mapper.Dispose()
    
    
    def testPyMem_Malloc_Failure(self):
        mapper = Python25Mapper()
        resultPtr = mapper.PyMem_Malloc(sys.maxint)
        self.assertEquals(resultPtr, IntPtr.Zero, "bad alloc")
        mapper.Dispose()
        
        
class Python25Mapper_PyMem_Free_Test(TestCase):
    
    def testPyMem_Free_NonNull(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        ptr = mapper.PyMem_Malloc(123)
        mapper.PyMem_Free(ptr)
        self.assertEquals(frees, [ptr], "did not free")
        mapper.Dispose()
    

    def testPyMem_Free_Null(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        mapper.PyMem_Free(IntPtr.Zero)
        self.assertEquals(frees, [], "freed inappropriately")
        mapper.Dispose()
        


suite = makesuite(
    Python25Mapper_PyMem_Malloc_Test,
    Python25Mapper_PyMem_Free_Test,
)

if __name__ == '__main__':
    run(suite)