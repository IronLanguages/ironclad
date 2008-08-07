using System;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

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
                Builtin.hasattr(DefaultContext.Default, obj, "__len__") &&
                Builtin.hasattr(DefaultContext.Default, obj, "__getitem__") &&
                Builtin.hasattr(DefaultContext.Default, obj, "__add__") &&
                Builtin.hasattr(DefaultContext.Default, obj, "__radd__") &&
                Builtin.hasattr(DefaultContext.Default, obj, "__mul__") &&
                Builtin.hasattr(DefaultContext.Default, obj, "__rmul__") &&
                !Builtin.hasattr(DefaultContext.Default, obj, "__coerce__"))
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
                throw PythonOps.TypeError("failed to convert {0} to sequence", sequence);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
    }
}