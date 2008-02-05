
from System import IntPtr, Int32
from System.Runtime.InteropServices import Marshal

ptrSize = Marshal.SizeOf(IntPtr)
intSize = Marshal.SizeOf(Int32)

def OffsetPtr(ptr, offset):
    return IntPtr(ptr.ToInt32() + offset)