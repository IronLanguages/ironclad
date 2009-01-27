using System;
using System.Runtime.InteropServices;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        
        public override IntPtr
        PyCObject_FromVoidPtr(IntPtr cobjData, IntPtr destructor)
        {
            IntPtr cobjPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyCObject)));
            CPyMarshal.Zero(cobjPtr, Marshal.SizeOf(typeof(PyCObject)));
            CPyMarshal.WriteIntField(cobjPtr, typeof(PyCObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "ob_type", this.PyCObject_Type);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "cobject", cobjData);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "destructor", destructor);
            
            OpaquePyCObject cobj = new OpaquePyCObject(this, cobjPtr);
            this.StoreBridge(cobjPtr, cobj);
            this.IncRef(cobjPtr);
            return cobjPtr;
        }

        public override IntPtr
        PyCObject_FromVoidPtrAndDesc(IntPtr cobjData, IntPtr desc, IntPtr destructor)
        {
            IntPtr cobjPtr = this.PyCObject_FromVoidPtr(cobjData, destructor);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "desc", desc);
            return cobjPtr;
        }

        
        public override IntPtr
        PyCObject_AsVoidPtr(IntPtr cobjPtr)
        {
            return CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "cobject");
        }
    
        public void
        IC_PyCObject_Dealloc(IntPtr cobjPtr)
        {
            if (CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "destructor") != IntPtr.Zero)
            {
                IntPtr desc = CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "desc");
                if (desc == IntPtr.Zero)
                {
                    dgt_void_ptr destructor = (dgt_void_ptr)
                        CPyMarshal.ReadFunctionPtrField(cobjPtr, typeof(PyCObject), "destructor", typeof(dgt_void_ptr));
                    destructor(CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "cobject"));
                }
                else
                {
                    dgt_void_ptrptr destructor2 = (dgt_void_ptrptr)
                        CPyMarshal.ReadFunctionPtrField(cobjPtr, typeof(PyCObject), "destructor", typeof(dgt_void_ptrptr));
                    destructor2(CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "cobject"), desc);
                }
            }
            PyObject_Free_Delegate free = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(this.PyCObject_Type, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            free(cobjPtr);
        }
    }

}
