from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import IAllocator

def GetAllocatingTestAllocator(allocsList, freesList):
    class TestAllocator(IAllocator):
        def Allocate(self, bytes):
            ptr = Marshal.AllocHGlobal(bytes)
            allocsList.append(ptr)
            return ptr
        def Free(self, ptr):
            freesList.append(ptr)
            Marshal.FreeHGlobal(ptr)
    return TestAllocator()

def GetDoNothingTestAllocator(freesList):
    class TestAllocator(IAllocator):
        def Allocate(self, _):
            return IntPtr.Zero
        def Free(self, ptr):
            freesList.append(ptr)
    return TestAllocator()