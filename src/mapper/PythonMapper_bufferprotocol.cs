using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;

using Ironclad.Structs;

using Microsoft.Scripting;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override int PyObject_GetBuffer(IntPtr objPtr, IntPtr view, int flags)
        {
            var typePtr = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type));
            var pb = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_buffer));
            if (pb == IntPtr.Zero) return TypeError();
            var getBufferProc = CPyMarshal.ReadFunctionPtrField<dgt_int_ptrptrint>(pb, typeof(PyBufferProcs), nameof(PyBufferProcs.bf_getbuffer));
            if (getBufferProc is null) return TypeError();

            return getBufferProc(objPtr, view, flags);

            int TypeError()
            {
                // TODO: type name!
                this.LastException = PythonOps.TypeError("does not support the buffer interface");
                return -1;
            }
        }

        public override void PyBuffer_Release(IntPtr view)
        {
            var obj = CPyMarshal.ReadPtrField(view, typeof(Py_buffer), nameof(Py_buffer.obj));
            if (obj == IntPtr.Zero) return;
            try
            {
                var typePtr = CPyMarshal.ReadPtrField(obj, typeof(PyObject), nameof(PyObject.ob_type));
                var pb = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_buffer));
                if (pb == IntPtr.Zero) return;
                var releaseBufferPtr = CPyMarshal.ReadPtrField(pb, typeof(PyBufferProcs), nameof(PyBufferProcs.bf_releasebuffer));
                if (releaseBufferPtr == IntPtr.Zero) return;
                var releaseBufferProc = Marshal.GetDelegateForFunctionPointer<dgt_void_ptrptr>(releaseBufferPtr);
                releaseBufferProc(obj, view);
            }
            finally
            {
                CPyMarshal.WritePtrField(view, typeof(Py_buffer), nameof(Py_buffer.obj), IntPtr.Zero);
                this.DecRef(obj);
            }
        }

        private Dictionary<IntPtr, Tuple<IPythonBuffer, MemoryHandle>> buffers = new Dictionary<IntPtr, Tuple<IPythonBuffer, MemoryHandle>>();

        public override int IC_getbuffer(IntPtr objPtr, IntPtr view, int flags)
        {
            var obj = (IBufferProtocol)Retrieve(objPtr);
            var buffer = obj.GetBuffer((BufferFlags)flags);
            var handle = buffer.Pin();
            buffers[view] = Tuple.Create(buffer, handle);

            return PyBuffer_FillInfoHelper(view, objPtr, buffer, handle, flags);
        }

        public override void IC_releasebuffer(IntPtr objPtr, IntPtr view)
        {
            if (buffers.TryGetValue(view, out var buffer))
            {
                buffers.Remove(view);
                buffer.Item1.Dispose();
                buffer.Item2.Dispose();
            }
        }

        delegate int PyBuffer_FillInfoDelegate(IntPtr view, IntPtr obj, IntPtr buf, nint len, int @readonly, int flags);

        private int PyBuffer_FillInfoHelper(IntPtr view, IntPtr obj, IPythonBuffer buffer, MemoryHandle handle, int flags)
        {
            var del = Marshal.GetDelegateForFunctionPointer<PyBuffer_FillInfoDelegate>(PyBuffer_FillInfo);
            unsafe {
                return del(view, obj, (IntPtr)handle.Pointer, buffer.ItemCount, buffer.IsReadOnly ? 1 : 0, flags);
            }
        }
    }
}