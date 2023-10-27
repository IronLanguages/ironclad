using System;
using System.Runtime.InteropServices;

namespace Ironclad.Structs
{
    // TODO: can we generate this?
    [StructLayout(LayoutKind.Sequential)]
    public struct PyHeapTypeObject {
        PyTypeObject ht_type;
        PyNumberMethods as_number;
        PyMappingMethods as_mapping;
        PySequenceMethods as_sequence;
        PyBufferProcs as_buffer;
        IntPtr ht_name;
        IntPtr ht_slots;
        IntPtr ht_qualname;
        IntPtr ht_cached_keys;
    }    
}
