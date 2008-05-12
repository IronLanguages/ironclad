
import unittest
from tests.utils.runtest import makesuite, run

from Ironclad import CPyMarshal, HGlobalAllocator


REASONABLE_SIZE = 8192

class HGlobalAllocatorTest(unittest.TestCase):
    
    def testAllocFree(self):
        allocator = HGlobalAllocator()
        ptr = allocator.Alloc(REASONABLE_SIZE)
        CPyMarshal.WriteInt(ptr, 123)
        
        allocator.Free(ptr)
        self.assertRaises(KeyError, allocator.Free, ptr)
    
    
    def testAllocFreeAll(self):
        allocator = HGlobalAllocator()
        ptr1 = allocator.Alloc(REASONABLE_SIZE)
        ptr2 = allocator.Alloc(REASONABLE_SIZE)
        ptr3 = allocator.Alloc(REASONABLE_SIZE)
        
        allocator.Free(ptr1)
        self.assertRaises(KeyError, allocator.Free, ptr1)
        
        allocator.FreeAll()
        self.assertRaises(KeyError, allocator.Free, ptr2)
        self.assertRaises(KeyError, allocator.Free, ptr3)
        
        
    def testRealloc(self):
        def DoTest(size):
            allocator = HGlobalAllocator()
            ptr1 = allocator.Alloc(REASONABLE_SIZE)
            ptr2 = allocator.Realloc(ptr1, REASONABLE_SIZE * (2 ** size))
            if (ptr1 == ptr2):
                return False
            
            self.assertRaises(KeyError, allocator.Free, ptr1)
            allocator.FreeAll()
            self.assertRaises(KeyError, allocator.Free, ptr2)
            return True
        
        i = 1
        while not DoTest(i):
            i = i + 1
            if i > 5:
                self.fail("failed to convince allocator to reallocate into a new block")
        
    

suite = makesuite(HGlobalAllocatorTest)

if __name__ == '__main__':
    run(suite)