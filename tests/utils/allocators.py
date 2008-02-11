from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import IAllocator

def GetAllocatingTestAllocator(allocsList, freesList):
    class TestAllocator(IAllocator):
        def Alloc(self, bytes):
            ptr = Marshal.AllocHGlobal(bytes)
            allocsList.append((ptr, bytes))
            return ptr
        def Realloc(self, ptr, bytes):
            new = Marshal.ReAllocHGlobal(ptr, IntPtr(bytes))
            freesList.append(ptr)
            allocsList.append((new, bytes))
            return new
        def Free(self, ptr):
            freesList.append(ptr)
            Marshal.FreeHGlobal(ptr)
    return TestAllocator()

def GetDoNothingTestAllocator(freesList):
    class TestAllocator(IAllocator):
        def Alloc(self, _):
            return IntPtr.Zero
        def Free(self, ptr):
            freesList.append(ptr)
    return TestAllocator()