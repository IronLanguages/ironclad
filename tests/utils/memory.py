
from System import IntPtr
from System.Runtime.InteropServices import Marshal

def OffsetPtr(ptr, offset):
    if type(offset) == IntPtr:
        offset = offset.ToInt32()
    return IntPtr(ptr.ToInt32() + offset)