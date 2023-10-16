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
        PyFrozenSet_New(IntPtr iterablePtr)
        {
            // TODO: frozen set!
            if (iterablePtr == IntPtr.Zero) {
                return this.Store(new SetCollection());
            }

            throw new NotImplementedException("PyFrozenSet_New");
        }

        public override int
        PySet_Add(IntPtr set, IntPtr key)
        {
            switch(this.Retrieve(set)) {
                case SetCollection setCollection:
                    setCollection.add(this.Retrieve(key));
                    return 0;
                default:
                    throw new NotImplementedException("PySet_Add");
            }
        }
    }
}
