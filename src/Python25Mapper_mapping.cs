using System;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override int
        PyMapping_Check(IntPtr maybeMapping)
        {
            object obj = this.Retrieve(maybeMapping);
            if (Builtin.isinstance(obj, TypeCache.PythonType))
            {
                return 0;
            }
            if(Builtin.hasattr(this.scratchContext, obj, "__getitem__"))
            {
                return 1;
            }
            return 0;
        }

        public override IntPtr
        PyMapping_GetItemString(IntPtr mappingPtr, string key)
        {
            try
            {
                object result = PythonOperator.getitem(this.scratchContext, this.Retrieve(mappingPtr), key);
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}