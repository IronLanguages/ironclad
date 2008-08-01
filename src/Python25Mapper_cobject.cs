using System;
using System.Runtime.InteropServices;

using Ironclad.Structs;

namespace Ironclad
{
    public class OpaquePyCObject
    {
        private Python25Mapper mapper;
        private IntPtr instancePtr;
        
        public OpaquePyCObject(Python25Mapper inMapper, IntPtr inInstancePtr)
        {
            this.mapper = inMapper;
            this.instancePtr = inInstancePtr;
        }
        
        ~OpaquePyCObject()
        {
            if (this.mapper.Alive)
            {
                this.mapper.DecRef(this.instancePtr);
            }
        }
    }
    
    
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
        PyCObject_AsVoidPtr(IntPtr cobjPtr)
        {
            IntPtr cobjData = CPyMarshal.ReadPtrField(cobjPtr, typeof(PyCObject), "cobject");
            return cobjData;
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