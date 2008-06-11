using System;
using System.Runtime.InteropServices;

using Ironclad.Structs;

namespace Ironclad
{
    public class OpaquePyCObject
    {
    }
    
    
    public partial class Python25Mapper : Python25Api
    {
        public override void 
        Fill_PyCObject_Type(IntPtr address)
        {
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_dealloc", this.GetMethodFP("PyCObject_Dealloc"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_free", this.GetAddress("PyObject_Free"));
            this.map.Associate(address, typeof(OpaquePyCObject));
        }
        
        public override IntPtr
        PyCObject_FromVoidPtr(IntPtr cobj, IntPtr destructor)
        {
            IntPtr cobjPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyCObject)));
            CPyMarshal.Zero(cobjPtr, Marshal.SizeOf(typeof(PyCObject)));
            CPyMarshal.WriteIntField(cobjPtr, typeof(PyCObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "ob_type", this.PyCObject_Type);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "cobject", cobj);
            CPyMarshal.WritePtrField(cobjPtr, typeof(PyCObject), "destructor", destructor);
            
            this.map.Associate(cobjPtr, new OpaquePyCObject());
            return cobjPtr;
        }
    
        public void
        PyCObject_Dealloc(IntPtr cobjPtr)
        {
            if (CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "destructor") != IntPtr.Zero)
            {
                CPython_destructor_Delegate destructor = (CPython_destructor_Delegate)
                    CPyMarshal.ReadFunctionPtrField(cobjPtr, typeof(PyCObject), "destructor", typeof(CPython_destructor_Delegate));
                destructor(CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "cobject"));
            }
            PyObject_Free_Delegate free = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(this.PyCObject_Type, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            free(cobjPtr);
        }
    }

}