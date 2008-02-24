
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime.Types;


namespace Ironclad
{

    public partial class Python25Mapper
    {


        public override void Fill_PyFile_Type(IntPtr address)
        {
            this.StoreUnmanagedData(address, TypeCache.PythonFile);
        }
    }
}
