using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override void
        Fill_PyTuple_Type(IntPtr address)
        {
            this.dgtMap["PyTuple_Dealloc"] = new CPython_destructor_Delegate(this.PyTuple_Dealloc);
            IntPtr tp_deallocPtr = CPyMarshal.Offset(
                address, Marshal.OffsetOf(typeof(PyTypeObject), "tp_dealloc"));
            CPyMarshal.WritePtr(tp_deallocPtr, Marshal.GetFunctionPointerForDelegate(this.dgtMap["PyTuple_Dealloc"]));

            this.dgtMap["Free"] = new CPython_destructor_Delegate(this.Free);
            IntPtr tp_freePtr = CPyMarshal.Offset(
                address, Marshal.OffsetOf(typeof(PyTypeObject), "tp_free"));
            CPyMarshal.WritePtr(tp_freePtr, Marshal.GetFunctionPointerForDelegate(this.dgtMap["Free"]));
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
            this.StoreUnmanagedData(tuplePtr, UnmanagedDataMarker.PyTupleObject);
            return tuplePtr;
        }
        
        
        private IntPtr
        Store(Tuple tuple)
        {
            int length = tuple.GetLength();
            IntPtr tuplePtr = this.CreateTuple(length);
            IntPtr itemPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_item"));
            for (int i = 0; i < length; i++)
            {
                CPyMarshal.WritePtr(itemPtr, this.Store(tuple[i]));
                itemPtr = CPyMarshal.Offset(itemPtr, CPyMarshal.PtrSize);
            }
            this.StoreUnmanagedData(tuplePtr, tuple);
            return tuplePtr;
        }
        
        
        public virtual void PyTuple_Dealloc(IntPtr tuplePtr)
        {
            IntPtr lengthPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_size"));
            int length = CPyMarshal.ReadInt(lengthPtr);
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
            IntPtr freeFPPtr = CPyMarshal.Offset(
                this.PyTuple_Type, Marshal.OffsetOf(typeof(PyTypeObject), "tp_free"));
            IntPtr freeFP = CPyMarshal.ReadPtr(freeFPPtr);
            CPython_destructor_Delegate freeDgt = (CPython_destructor_Delegate)Marshal.GetDelegateForFunctionPointer(
                freeFP, typeof(CPython_destructor_Delegate));
            freeDgt(tuplePtr);
        }
    }
}