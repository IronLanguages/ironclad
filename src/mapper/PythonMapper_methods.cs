using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override IntPtr
        PyMethod_New(IntPtr funcPtr, IntPtr selfPtr, IntPtr klassPtr)
        {
            object func = null;
            if (funcPtr != IntPtr.Zero)
            {
                func = this.Retrieve(funcPtr);
            }
            object self = null;
            if (selfPtr != IntPtr.Zero)
            {
                self = this.Retrieve(selfPtr);
            }

            return this.Store(new Method(func, self));
        }
        
        private IntPtr
        StoreTyped(Method meth)
        {
            int size = Marshal.SizeOf<PyMethodObject>();
            IntPtr methPtr = this.allocator.Alloc(size);
            CPyMarshal.Zero(methPtr, size);
            
            CPyMarshal.WritePtrField(methPtr, typeof(PyMethodObject), nameof(PyMethodObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(methPtr, typeof(PyMethodObject), nameof(PyMethodObject.ob_type), this.PyMethod_Type);
            CPyMarshal.WritePtrField(methPtr, typeof(PyMethodObject), nameof(PyMethodObject.im_func), this.Store(meth.__func__));
            CPyMarshal.WritePtrField(methPtr, typeof(PyMethodObject), nameof(PyMethodObject.im_self), this.Store(meth.__self__));
            
            this.map.Associate(methPtr, meth);
            return methPtr;
        }
        
        public override void
        IC_PyMethod_Dealloc(IntPtr objPtr)
        {
            this.DecRef(CPyMarshal.ReadPtrField(objPtr, typeof(PyMethodObject), nameof(PyMethodObject.im_func)));
            this.DecRef(CPyMarshal.ReadPtrField(objPtr, typeof(PyMethodObject), nameof(PyMethodObject.im_self)));
            
            IntPtr objType = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type));
            dgt_void_ptr freeDgt = CPyMarshal.ReadFunctionPtrField<dgt_void_ptr>(objType, typeof(PyTypeObject), nameof(PyTypeObject.tp_free));
            freeDgt(objPtr);
        }
    }
}
