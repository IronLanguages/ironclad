using System;

using IronPython.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyMethod_New(IntPtr funcPtr, IntPtr selfPtr, IntPtr klassPtr)
        {
            object func = null;
            if (funcPtr != IntPtr.Zero)
            {
                func = this.Retrieve(funcPtr);
            }
            object self = null;
            if (selfPtr != IntPtr.Zero)
            {
                self = this.Retrieve(selfPtr);
            }
            object klass = null;
            if (klassPtr != IntPtr.Zero)
            {
                klass = this.Retrieve(klassPtr);
            }

            return this.Store(new Method(func, self, klass));
        }
    }
}
