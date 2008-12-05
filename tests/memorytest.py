
import sys

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from tests.utils.allocators import GetAllocatingTestAllocator

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import Python25Mapper



class PyMem_Malloc_Test(TestCase):
    
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
    
    
    @WithMapper
    def testPyMem_Malloc_Failure(self, mapper, _):
        resultPtr = mapper.PyMem_Malloc(sys.maxint)
        self.assertEquals(resultPtr, IntPtr.Zero, "bad alloc")
        self.assertMapperHasError(mapper, None)


class PyObject_Malloc_Test(TestCase):
    
    def testPyObject_Malloc_NonZero(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        
        resultPtr = mapper.PyObject_Malloc(123)
        self.assertEquals(allocs, [(resultPtr, 123)], "bad alloc")
        mapper.Dispose()
    
    
    def testPyObject_Malloc_Zero(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        
        resultPtr = mapper.PyObject_Malloc(0)
        self.assertEquals(allocs, [(resultPtr, 1)], "bad alloc")
        mapper.Dispose()
    
    
    @WithMapper
    def testPyObject_Malloc_Failure(self, mapper, _):
        resultPtr = mapper.PyObject_Malloc(sys.maxint)
        self.assertEquals(resultPtr, IntPtr.Zero, "bad alloc")
        self.assertMapperHasError(mapper, None)


class PyMem_Free_Test(TestCase):
    
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
        

class PyMem_Realloc_Test(TestCase):

    def testNullPtr(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        
        mem = mapper.PyMem_Realloc(IntPtr.Zero, 4)
        self.assertEquals(frees, [])
        self.assertEquals(allocs, [(mem, 4)])
        mapper.Dispose()
        
        
    def testZeroBytes(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        
        mem1 = mapper.PyMem_Malloc(4)
        del allocs[:]
        mem2 = mapper.PyMem_Realloc(mem1, 0)
        
        self.assertEquals(frees, [mem1])
        self.assertEquals(allocs, [(mem2, 1)])
        mapper.Dispose()
        
        
    def testTooBig(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        
        mem1 = mapper.PyMem_Malloc(4)
        del allocs[:]
        self.assertEquals(mapper.PyMem_Realloc(mem1, sys.maxint), IntPtr.Zero)
        self.assertMapperHasError(mapper, None)
        
        self.assertEquals(frees, [])
        self.assertEquals(allocs, [])
        mapper.Dispose()
        
        
    def testEasy(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        
        mem1 = mapper.PyMem_Malloc(4)
        del allocs[:]
        mem2 = mapper.PyMem_Realloc(mem1, 8)
        
        self.assertEquals(frees, [mem1])
        self.assertEquals(allocs, [(mem2, 8)])
        mapper.Dispose()


suite = makesuite(
    PyMem_Malloc_Test,
    PyObject_Malloc_Test,
    PyMem_Free_Test,
    PyMem_Realloc_Test,
)

if __name__ == '__main__':
    run(suite)
