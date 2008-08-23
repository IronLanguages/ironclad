using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private IntPtr
        Store(Slice slice)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PySliceObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PySliceObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "ob_type", this.PySlice_Type);
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "start", this.Store(slice.start));
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "stop", this.Store(slice.stop));
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "step", this.Store(slice.step));
            this.map.Associate(ptr, slice);
            return ptr;
        }


        public void
        PySlice_Dealloc(IntPtr slicePtr)
        {
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), "start"));
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), "stop"));
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), "step"));

            PyObject_Free_Delegate freeDgt = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(
                    this.PySlice_Type, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            freeDgt(slicePtr);
        }
        
    }
}