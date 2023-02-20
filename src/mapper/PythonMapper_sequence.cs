using System;
using System.Runtime.InteropServices;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using System.Numerics;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override int
        PySequence_Check(IntPtr objPtr)
        {
            object obj = this.Retrieve(objPtr);
            if (Builtin.isinstance(obj, Builtin.range))
            {
                return 1;
            }

            // I don't *think* a type's attributes can meaningfully count...
            // TODO: regardless, there must be a better way to do this
            if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                Builtin.hasattr(this.scratchContext, obj, "__len__") &&
                Builtin.hasattr(this.scratchContext, obj, "__getitem__") &&
                Builtin.hasattr(this.scratchContext, obj, "__add__") &&
                Builtin.hasattr(this.scratchContext, obj, "__radd__") &&
                Builtin.hasattr(this.scratchContext, obj, "__mul__") &&
                Builtin.hasattr(this.scratchContext, obj, "__rmul__") &&
                !Builtin.hasattr(this.scratchContext, obj, "__coerce__"))
            {
                return 1;
            }
            return 0;
        }
        
        public override nint
        PySequence_Size(IntPtr objPtr)
        {
            try
            {
                return (int)Builtin.len(this.Retrieve(objPtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override IntPtr
        PySequence_GetItem(IntPtr objPtr, nint idx)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type)) == this.PyTuple_Type)
                {
                    IntPtr storagePtr = CPyMarshal.Offset(objPtr, Marshal.OffsetOf(typeof(PyTupleObject), nameof(PyTupleObject.ob_item)));
                    nint size = CPyMarshal.ReadPtrField(objPtr, typeof(PyTupleObject), nameof(PyTupleObject.ob_size));
                    if (idx >= size)
                    {
                        throw PythonOps.IndexError("PySequence_GetItem: tuple index {0} out of range", idx);
                    }
                    
                    IntPtr slotPtr = CPyMarshal.Offset(storagePtr, idx * CPyMarshal.PtrSize);
                    IntPtr itemPtr =  CPyMarshal.ReadPtr(slotPtr);
                    nint refcnt = CPyMarshal.ReadPtrField(itemPtr, typeof(PyObject), nameof(PyObject.ob_refcnt));
                    CPyMarshal.WritePtrField(itemPtr, typeof(PyObject), nameof(PyObject.ob_refcnt), refcnt + 1);
                    return itemPtr;
                }
            
                object sequence = this.Retrieve(objPtr);
                object getitem;
                if (PythonOps.TryGetBoundAttr(sequence, "__getitem__", out getitem))
                {
                    return this.Store(PythonCalls.Call(getitem, checked((int)idx)));
                }
                throw PythonOps.TypeError("PySequence_GetItem: failed to convert {0} to sequence", sequence);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override int
        PySequence_SetItem(IntPtr objPtr, nint idx, IntPtr valuePtr)
        {
            try
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type));
                if (typePtr == this.PyList_Type)
                {
                    nint newIdx = idx;
                    nint length = CPyMarshal.ReadPtrField(objPtr, typeof(PyListObject), nameof(PyListObject.ob_size));
                    if (newIdx < 0)
                    {
                        newIdx += length;
                    }
                    if (newIdx >= 0 && newIdx < length)
                    {
                        this.IncRef(valuePtr);
                        return this.PyList_SetItem(objPtr, newIdx, valuePtr);
                    }
                    // otherwise, fall through and allow normal exception to occur
                }

                object sequence = this.Retrieve(objPtr);
                object setitem;
                if (PythonOps.TryGetBoundAttr(sequence, "__setitem__", out setitem))
                {
                    PythonCalls.Call(setitem, checked((int)idx), this.Retrieve(valuePtr));
                    return 0;
                }
                throw PythonOps.TypeError("PySequence_SetItem: failed to convert {0} to sequence", sequence);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override IntPtr
        PySequence_GetSlice(IntPtr objPtr, nint start, nint stop)
        {
            try
            {
                object sequence = this.Retrieve(objPtr);
                object getitem;
                if (PythonOps.TryGetBoundAttr(sequence, "__getitem__", out getitem))
                {
                    return this.Store(PythonCalls.Call(getitem, new Slice(checked((int)start), checked((int)stop))));
                }
                throw PythonOps.TypeError("PySequence_GetItem: failed to slice {0}", sequence);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override IntPtr
        PySequence_Repeat(IntPtr objPtr, nint count)
        {
            try
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type));
                IntPtr seqPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_sequence));
                if (seqPtr != IntPtr.Zero)
                {
                    IntPtr sq_repeat = CPyMarshal.ReadPtrField(seqPtr, typeof(PySequenceMethods), nameof(PySequenceMethods.sq_repeat));
                    if (sq_repeat != IntPtr.Zero)
                    {
                        dgt_ptr_ptrssize dgt = CPyMarshal.ReadFunctionPtrField<dgt_ptr_ptrssize>(seqPtr, typeof(PySequenceMethods), nameof(PySequenceMethods.sq_repeat));
                        return dgt(objPtr, count);
                    }
                }
                object obj = this.Retrieve(objPtr);
                if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                     Builtin.hasattr(this.scratchContext, obj, "__len__") &&
                     Builtin.hasattr(this.scratchContext, obj, "__getitem__"))
                {
                    return this.Store(PythonOperator.mul(this.scratchContext, obj, checked((int)count)));
                }
                throw PythonOps.TypeError("PySequence_Repeat: failed to convert {0} to sequence", obj);
            }                
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PySequence_Concat(IntPtr seq1Ptr, IntPtr seq2Ptr)
        {
            try
            {
                return this.Store(PythonOperator.add(
                    this.scratchContext, this.Retrieve(seq1Ptr), this.Retrieve(seq2Ptr)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override int
        PySequence_Contains(IntPtr seqPtr, IntPtr memberPtr)
        {
            try
            {
                if ((bool)PythonOperator.contains(this.scratchContext, this.Retrieve(seqPtr), this.Retrieve(memberPtr)))
                {
                    return 1;
                }
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override IntPtr
        PySequence_Tuple(IntPtr seqPtr)
        {
            try
            {
                if (CPyMarshal.ReadPtrField(seqPtr, typeof(PyObject), nameof(PyObject.ob_type)) == this.PyTuple_Type)
                {
                    this.IncRef(seqPtr);
                    return seqPtr;
                }
                object seq = this.Retrieve(seqPtr);
                return this.Store(PythonCalls.Call(TypeCache.PythonTuple, new object[] { seq }));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
