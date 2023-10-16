using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override IntPtr
        PyTuple_New(nint size)
        {
            IntPtr tuplePtr = this.CreateTuple(checked((int)size));
            this.incompleteObjects[tuplePtr] = UnmanagedDataMarker.PyTupleObject;
            return tuplePtr;
        }
        
        public override void 
        IC_PyTuple_Dealloc(IntPtr tuplePtr)
        {
            nint length = CPyMarshal.ReadPtrField(tuplePtr, typeof(PyTupleObject), nameof(PyTupleObject.ob_size));
            IntPtr itemsPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), nameof(PyTupleObject.ob_item)));
            for (nint i = 0; i < length; i++)
            {
                IntPtr itemPtr = CPyMarshal.ReadPtr(
                    CPyMarshal.Offset(
                        itemsPtr, i * CPyMarshal.PtrSize));
                if (itemPtr != IntPtr.Zero)
                {
                    this.DecRef(itemPtr);
                }
            }
            dgt_void_ptr freeDgt = CPyMarshal.ReadFunctionPtrField<dgt_void_ptr>(this.PyTuple_Type, typeof(PyTypeObject), nameof(PyTypeObject.tp_free));
            freeDgt(tuplePtr);
        }
        
        public override IntPtr
        IC_tuple_iter(IntPtr tuplePtr)
        {
            var tuple = (PythonTuple)this.Retrieve(tuplePtr);
            return this.Store(tuple.__iter__());
        }

        public override int
        _PyTuple_Resize(IntPtr tuplePtrPtr, nint length)
        {
            // note: make sure you don't actualise this
            try
            {
                IntPtr tuplePtr = CPyMarshal.ReadPtr(tuplePtrPtr);
                this.incompleteObjects.Remove(tuplePtr);
                
                nint newSize = (nint)Marshal.SizeOf<PyTupleObject>() + (CPyMarshal.PtrSize * (length - 1));
                tuplePtr = this.allocator.Realloc(tuplePtr, newSize);
                CPyMarshal.WritePtrField(tuplePtr, typeof(PyTupleObject), nameof(PyTupleObject.ob_size), length);
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
        
        public override nint
        PyTuple_Size(IntPtr tuplePtr)
        {
            return CPyMarshal.ReadPtrField(tuplePtr, typeof(PyTupleObject), nameof(PyTupleObject.ob_size));
        }
        
        public override IntPtr
        PyTuple_GetSlice(IntPtr tuplePtr, nint start, nint stop)
        {
            try
            {
                PythonTuple tuple = (PythonTuple)this.Retrieve(tuplePtr);
                PythonTuple sliced = (PythonTuple)tuple[new Slice(checked((int)start), checked((int)stop))];
                return this.Store(sliced);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        private IntPtr
        CreateTuple(int size)
        {
            PyTupleObject tuple = new PyTupleObject();
            tuple.ob_refcnt = 1;
            tuple.ob_type = this.PyTuple_Type;
            tuple.ob_size = size;

            int baseSize = Marshal.SizeOf<PyTupleObject>();
            int extraSize = CPyMarshal.PtrSize * Math.Max(0, size - 1);
            IntPtr tuplePtr = this.allocator.Alloc(baseSize + extraSize);
            Marshal.StructureToPtr(tuple, tuplePtr, false);

            IntPtr itemsPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), nameof(PyTupleObject.ob_item)));
            CPyMarshal.Zero(itemsPtr, CPyMarshal.PtrSize * size);
            return tuplePtr;
        }
        
        private IntPtr
        StoreTyped(PythonTuple tuple)
        {
            int length = tuple.__len__();
            IntPtr tuplePtr = this.CreateTuple(length);
            IntPtr itemPtr = CPyMarshal.Offset(
                tuplePtr, Marshal.OffsetOf(typeof(PyTupleObject), nameof(PyTupleObject.ob_item)));
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
            nint itemCount = CPyMarshal.ReadPtrField(ptr, typeof(PyTupleObject), nameof(PyTupleObject.ob_size));
            IntPtr itemAddressPtr = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyTupleObject), nameof(PyTupleObject.ob_item)));

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
