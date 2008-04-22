
using System;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override IntPtr Make_PyExc_BaseException()
        {
            return this.Store(TypeCache.BaseException);
        }
    }
}
