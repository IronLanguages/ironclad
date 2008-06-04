using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override void
        Fill_PyTuple_Type(IntPtr address)
        {
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_dealloc", this.GetMethodFP("PyTuple_Dealloc"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_free", this.GetAddress("PyObject_Free"));
            this.map.Associate(address, TypeCache.PythonTuple);
        }
        
        private IntPtr CreateTuple(int size)
        {
            PyTupleObject tuple = new PyTupleObject();
            tuple.ob_refcnt = 1;
            tuple.ob_type = this.PyTuple_Type;
            tuple.ob_size = (uint)size;
            
            int baseSize = Marshal.SizeOf(typeof(PyTupleObject));
            int extraSize = CPyMarshal.PtrSize * (size - 1);
            IntPtr tuplePtr = this.allocator.Alloc(baseSize + extraSize);
            Marshal.StructureToPtr(tuple, tuplePtr, false);
            
            IntPtr itemsPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_item"));
            CPyMarshal.Zero(itemsPtr, CPyMarshal.PtrSize * size);
            return tuplePtr;
        }
        
        public override IntPtr
        PyTuple_New(int size)
        {
            IntPtr tuplePtr = this.CreateTuple(size);
            this.map.Associate(tuplePtr, UnmanagedDataMarker.PyTupleObject);
            return tuplePtr;
        }
        
        
        private IntPtr
        Store(PythonTuple tuple)
        {
            int length = tuple.__len__();
            IntPtr tuplePtr = this.CreateTuple(length);
            IntPtr itemPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_item"));
            for (int i = 0; i < length; i++)
            {
                CPyMarshal.WritePtr(itemPtr, this.Store(tuple[i]));
                itemPtr = CPyMarshal.Offset(itemPtr, CPyMarshal.PtrSize);
            }
            this.map.Associate(tuplePtr, tuple);
            return tuplePtr;
        }
        
        
        public virtual void 
        PyTuple_Dealloc(IntPtr tuplePtr)
        {
            int length = CPyMarshal.ReadIntField(tuplePtr, typeof(PyTupleObject), "ob_size");
            IntPtr itemsPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_item"));
            for (int i = 0; i < length; i++)
            {
                IntPtr itemPtr = CPyMarshal.ReadPtr(
                    CPyMarshal.Offset(
                        itemsPtr, i * CPyMarshal.PtrSize));
                if (itemPtr != IntPtr.Zero)
                {
                    this.DecRef(itemPtr);
                }
            }
            PyObject_Free_Delegate freeDgt = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(
                    this.PyTuple_Type, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            freeDgt(tuplePtr);
        }
        
        
        private void
        ActualiseTuple(IntPtr ptr)
        {
            int itemCount = CPyMarshal.ReadIntField(ptr, typeof(PyTupleObject), "ob_size");
            IntPtr itemAddressPtr = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_item"));

            object[] items = new object[itemCount];
            for (int i = 0; i < itemCount; i++)
            {
                IntPtr itemPtr = CPyMarshal.ReadPtr(itemAddressPtr);
                items[i] = this.Retrieve(itemPtr);
                itemAddressPtr = CPyMarshal.Offset(itemAddressPtr, CPyMarshal.PtrSize);
            }
            this.map.Associate(ptr, new PythonTuple(items));
        }
    }
}