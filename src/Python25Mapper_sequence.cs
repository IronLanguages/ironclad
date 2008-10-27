using System;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override int
        PySequence_Check(IntPtr objPtr)
        {
            // I don't *think* a type's attributes can meaningfully count...
            // TODO: regardless, there must be a better way to do this
            object obj = this.Retrieve(objPtr);
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
        
        public override int
        PySequence_Size(IntPtr objPtr)
        {
            try
            {
                return Builtin.len(this.Retrieve(objPtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override IntPtr
        PySequence_GetItem(IntPtr objPtr, int idx)
        {
            try
            {
                object sequence = this.Retrieve(objPtr);
                object getitem;

                if (PythonOps.TryGetBoundAttr(sequence, Symbols.GetItem, out getitem))
                {
                    return this.Store(PythonCalls.Call(getitem, idx));
                }
                throw PythonOps.TypeError("PySequence_GetItem: failed to convert {0} to sequence", sequence);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override IntPtr
        PySequence_Repeat(IntPtr objPtr, int count)
        {
            try
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), "ob_type");
                IntPtr seqPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_as_sequence");
                if (seqPtr != IntPtr.Zero)
                {
                    IntPtr sq_repeat = CPyMarshal.ReadPtrField(seqPtr, typeof(PySequenceMethods), "sq_repeat");
                    if(sq_repeat != IntPtr.Zero)
                    { 
                        CPython_ssizeargfunc_Delegate dgt = (CPython_ssizeargfunc_Delegate) CPyMarshal.ReadFunctionPtrField(
                            seqPtr, typeof(PySequenceMethods), "sq_repeat", typeof(CPython_ssizeargfunc_Delegate));
                        return dgt(objPtr, count);
                    }
                }
                object obj = this.Retrieve(objPtr);
                if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                     Builtin.hasattr(this.scratchContext, obj, "__len__") &&
                     Builtin.hasattr(this.scratchContext, obj, "__getitem__"))
                {
                    return this.Store(PythonOperator.mul(this.scratchContext, obj, count));
                }
                throw PythonOps.TypeError("PySequence_Repeat: failed to convert {0} to sequence", obj);
                
            }                
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
