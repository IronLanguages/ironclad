
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from System import IntPtr

from Ironclad import CPyMarshal, HGlobalAllocator


REASONABLE_SIZE = 8192

class HGlobalAllocatorTest(TestCase):
    
    def testAllocFree(self):
        allocator = HGlobalAllocator()
        ptr = allocator.Alloc(IntPtr(REASONABLE_SIZE))
        self.assertEqual(allocator.Contains(ptr), True)
        CPyMarshal.WriteInt(ptr, 123)
        
        allocator.Free(ptr)
        self.assertEqual(allocator.Contains(ptr), False)
        self.assertRaises(KeyError, allocator.Free, ptr)
    
    
    def testAllocFreeAll(self):
        allocator = HGlobalAllocator()
        ptr1 = allocator.Alloc(IntPtr(REASONABLE_SIZE))
        self.assertEqual(allocator.Contains(ptr1), True)
        ptr2 = allocator.Alloc(IntPtr(REASONABLE_SIZE))
        self.assertEqual(allocator.Contains(ptr2), True)
        ptr3 = allocator.Alloc(IntPtr(REASONABLE_SIZE))
        self.assertEqual(allocator.Contains(ptr3), True)
        
        allocator.Free(ptr1)
        self.assertEqual(allocator.Contains(ptr1), False)
        self.assertRaises(KeyError, allocator.Free, ptr1)
        
        allocator.FreeAll()
        self.assertEqual(allocator.Contains(ptr2), False)
        self.assertEqual(allocator.Contains(ptr3), False)
        self.assertRaises(KeyError, allocator.Free, ptr2)
        self.assertRaises(KeyError, allocator.Free, ptr3)
        
        
    def testRealloc(self):
        def DoTest(size):
            allocator = HGlobalAllocator()
            ptr1 = allocator.Alloc(IntPtr(REASONABLE_SIZE))
            ptr2 = allocator.Realloc(ptr1, IntPtr(REASONABLE_SIZE * (2 ** size)))
            if (ptr1 == ptr2):
                return False
            
            self.assertEqual(allocator.Contains(ptr1), False)
            self.assertEqual(allocator.Contains(ptr2), True)
            self.assertRaises(KeyError, allocator.Free, ptr1)
            allocator.FreeAll()
            self.assertEqual(allocator.Contains(ptr2), False)
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
