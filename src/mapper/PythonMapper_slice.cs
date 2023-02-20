using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        private IntPtr
        StoreTyped(Slice slice)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf<PySliceObject>());
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), nameof(PySliceObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), nameof(PySliceObject.ob_type), this.PySlice_Type);
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), nameof(PySliceObject.start), this.Store(slice.start));
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), nameof(PySliceObject.stop), this.Store(slice.stop));
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), nameof(PySliceObject.step), this.Store(slice.step));
            this.map.Associate(ptr, slice);
            return ptr;
        }

        public override void
        IC_PySlice_Dealloc(IntPtr slicePtr)
        {
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), nameof(PySliceObject.start)));
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), nameof(PySliceObject.stop)));
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), nameof(PySliceObject.step)));

            dgt_void_ptr freeDgt = CPyMarshal.ReadFunctionPtrField<dgt_void_ptr>(this.PySlice_Type, typeof(PyTypeObject), nameof(PyTypeObject.tp_free));
            freeDgt(slicePtr);
        }

        public override IntPtr
        PySlice_New(IntPtr startPtr, IntPtr stopPtr, IntPtr stepPtr)
        {
            object start = null;
            if (startPtr != IntPtr.Zero)
            {
                start = this.Retrieve(startPtr);
            }
            object stop = null;
            if (stopPtr != IntPtr.Zero)
            {
                stop = this.Retrieve(stopPtr);
            }
            object step = null;
            if (stepPtr != IntPtr.Zero)
            {
                step = this.Retrieve(stepPtr);
            }
            return this.Store(new Slice(start, stop, step));
        }
    }
}
