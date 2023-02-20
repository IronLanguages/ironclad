
import sys

from tests.utils.runtest import makesuite, run
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from tests.utils.allocators import GetAllocatingTestAllocator

from System import IntPtr, UIntPtr, UInt64

from Ironclad import PythonMapper

MAXSIZE = UInt64((1 << (IntPtr.Size * 8 - 1)) - 1) # bug in IronPython 2, cannot convert to UIntPtr from BigInteger

def GetMallocTest(MALLOC_NAME):
    class MallocTest(TestCase):
        __name__ = MALLOC_NAME + '_Test'
        
        def testNonZero(self):
            allocs = []
            mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
            
            resultPtr = getattr(mapper, MALLOC_NAME)(UIntPtr(123))
            self.assertEqual(allocs, [(resultPtr, 123)], "bad alloc")
            mapper.Dispose()
            
        def testZero(self):
            allocs = []
            mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
            
            resultPtr = getattr(mapper, MALLOC_NAME)(UIntPtr(0))
            self.assertEqual(allocs, [(resultPtr, 1)], "bad alloc")
            mapper.Dispose()

        @WithMapper
        def testFailure(self, mapper, _):
            resultPtr = getattr(mapper, MALLOC_NAME)(UIntPtr(MAXSIZE))
            self.assertEqual(resultPtr, IntPtr.Zero, "bad alloc")
            self.assertMapperHasError(mapper, None)

    return MallocTest


def GetReallocTest(MALLOC_NAME, REALLOC_NAME):
    class ReallocTest(TestCase):
        __name__ = REALLOC_NAME + '_Test'

        def testNullPtr(self):
            allocs = []
            frees = []
            mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
            
            mem = getattr(mapper, REALLOC_NAME)(IntPtr.Zero, UIntPtr(4))
            self.assertEqual(frees, [])
            self.assertEqual(allocs, [(mem, 4)])
            mapper.Dispose()
            
            
        def testZeroBytes(self):
            allocs = []
            frees = []
            mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
            
            mem1 = getattr(mapper, MALLOC_NAME)(UIntPtr(4))
            del allocs[:]
            mem2 = getattr(mapper, REALLOC_NAME)(mem1, UIntPtr(0))
            
            self.assertEqual(frees, [mem1])
            self.assertEqual(allocs, [(mem2, 1)])
            mapper.Dispose()
            
            
        def testTooBig(self):
            allocs = []
            frees = []
            mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
            
            deallocTypes = CreateTypes(mapper)
            mapper.EnsureGIL()
            mapper.ReleaseGIL()
            
            mem1 = getattr(mapper, MALLOC_NAME)(UIntPtr(4))
            del allocs[:]
            self.assertEqual(getattr(mapper, REALLOC_NAME)(mem1, UIntPtr(MAXSIZE)), IntPtr.Zero)
            self.assertMapperHasError(mapper, None)
            
            self.assertEqual(frees, [])
            self.assertEqual(allocs, [])
            mapper.Dispose()
            deallocTypes()
            
            
        def testEasy(self):
            allocs = []
            frees = []
            mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
            
            mem1 = getattr(mapper, MALLOC_NAME)(UIntPtr(4))
            del allocs[:]
            mem2 = getattr(mapper, REALLOC_NAME)(mem1, UIntPtr(8))
            
            self.assertEqual(frees, [mem1])
            self.assertEqual(allocs, [(mem2, 8)])
            mapper.Dispose()
    return ReallocTest


class PyMem_Free_Test(TestCase):
    
    def testPyMem_Free_NonNull(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        
        ptr = mapper.PyMem_Malloc(UIntPtr(123))
        mapper.PyMem_Free(ptr)
        self.assertEqual(frees, [ptr], "did not free")
        mapper.Dispose()
    

    def testPyMem_Free_Null(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        
        mapper.PyMem_Free(IntPtr.Zero)
        self.assertEqual(frees, [], "freed inappropriately")
        mapper.Dispose()


suite = makesuite(
    GetMallocTest('PyMem_Malloc'),
    GetMallocTest('PyObject_Malloc'),
    GetReallocTest('PyMem_Malloc', 'PyMem_Realloc'),
    GetReallocTest('PyObject_Malloc', 'PyObject_Realloc'),
    PyMem_Free_Test, # PyObject_Free is a different matter
)

if __name__ == '__main__':
    run(suite)
