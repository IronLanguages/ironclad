
from System import IntPtr, Int32
from System.Runtime.InteropServices import Marshal

def OffsetPtr(ptr, offset):
    return IntPtr(ptr.ToInt64() + offset)