using System;

using IronPython.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        
        public override IntPtr
        PyDict_New()
        {
            return this.Store(new Dict());
        }
    }
}