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
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PySliceObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PySliceObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "ob_type", this.PySlice_Type);
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "start", this.Store(slice.start));
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "stop", this.Store(slice.stop));
            CPyMarshal.WritePtrField(ptr, typeof(PySliceObject), "step", this.Store(slice.step));
            this.map.Associate(ptr, slice);
            return ptr;
        }

        public override void
        IC_PySlice_Dealloc(IntPtr slicePtr)
        {
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), "start"));
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), "stop"));
            this.DecRef(CPyMarshal.ReadPtrField(slicePtr, typeof(PySliceObject), "step"));

            dgt_void_ptr freeDgt = (dgt_void_ptr)
                CPyMarshal.ReadFunctionPtrField(
                    this.PySlice_Type, typeof(PyTypeObject), "tp_free", typeof(dgt_void_ptr));
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