from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import HGlobalAllocator, IAllocator

def GetAllocatingTestAllocator(allocsList, freesList):
    class TestAllocator(HGlobalAllocator):
        def Alloc(self, bytes):
            ptr = HGlobalAllocator.Alloc(self, bytes)
            allocsList.append((ptr, bytes))
            return ptr
        def Realloc(self, oldptr, bytes):
            newptr = HGlobalAllocator.Realloc(self, oldptr, bytes)
            freesList.append(oldptr)
            allocsList.append((newptr, bytes))
            return newptr
        def Free(self, ptr):
            freesList.append(ptr)
            HGlobalAllocator.Free(self, ptr)
    return TestAllocator()

def GetDoNothingTestAllocator(freesList):
    class TestAllocator(IAllocator):
        def Alloc(self, _):
            return IntPtr.Zero
        def Free(self, ptr):
            freesList.append(ptr)
        def FreeAll(self):
            pass
    return TestAllocator()