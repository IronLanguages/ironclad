using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyTuple_New(uint size)
        {
            IntPtr tuplePtr = this.CreateTuple(size);
            this.incompleteObjects[tuplePtr] = UnmanagedDataMarker.PyTupleObject;
            return tuplePtr;
        }
        
        public override void 
        IC_PyTuple_Dealloc(IntPtr tuplePtr)
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
            dgt_void_ptr freeDgt = (dgt_void_ptr)
                CPyMarshal.ReadFunctionPtrField(
                    this.PyTuple_Type, typeof(PyTypeObject), "tp_free", typeof(dgt_void_ptr));
            freeDgt(tuplePtr);
        }
        
        public override int
        _PyTuple_Resize(IntPtr tuplePtrPtr, uint length)
        {
            // note: make sure you don't actualise this
            try
            {
                IntPtr tuplePtr = CPyMarshal.ReadPtr(tuplePtrPtr);
                this.incompleteObjects.Remove(tuplePtr);
                
                uint newSize = (uint)Marshal.SizeOf(typeof(PyTupleObject)) + (uint)(CPyMarshal.PtrSize * ((int)length - 1));
                tuplePtr = this.allocator.Realloc(tuplePtr, newSize);
                CPyMarshal.WriteUIntField(tuplePtr, typeof(PyTupleObject), "ob_size", length);
                this.incompleteObjects[tuplePtr] = UnmanagedDataMarker.PyTupleObject;
                CPyMarshal.WritePtr(tuplePtrPtr, tuplePtr);
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                CPyMarshal.WritePtr(tuplePtrPtr, IntPtr.Zero);
                return -1;
            }
        }
        
        public override uint
        PyTuple_Size(IntPtr tuplePtr)
        {
            return CPyMarshal.ReadUIntField(tuplePtr, typeof(PyTupleObject), "ob_size");
        }
        
        public override IntPtr
        PyTuple_GetSlice(IntPtr tuplePtr, uint start, uint stop)
        {
            try
            {
                PythonTuple tuple = (PythonTuple)this.Retrieve(tuplePtr);
                PythonTuple sliced = (PythonTuple)tuple[new Slice((int)start, (int)stop)];
                return this.Store(sliced);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        private IntPtr
        CreateTuple(uint size)
        {
            PyTupleObject tuple = new PyTupleObject();
            tuple.ob_refcnt = 1;
            tuple.ob_type = this.PyTuple_Type;
            tuple.ob_size = size;

            uint baseSize = (uint)Marshal.SizeOf(typeof(PyTupleObject));
            uint extraSize = (uint)(CPyMarshal.PtrSize * ((int)size - 1));
            IntPtr tuplePtr = this.allocator.Alloc(baseSize + extraSize);
            Marshal.StructureToPtr(tuple, tuplePtr, false);

            IntPtr itemsPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), "ob_item"));
            CPyMarshal.Zero(itemsPtr, CPyMarshal.PtrSize * size);
            return tuplePtr;
        }
        
        private IntPtr
        Store(PythonTuple tuple)
        {
            uint length = (uint)tuple.__len__();
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
            this.incompleteObjects.Remove(ptr);
            this.map.Associate(ptr, new PythonTuple(items));
        }
    }
}
