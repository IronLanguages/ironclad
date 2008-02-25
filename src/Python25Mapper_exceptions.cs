
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime.Exceptions;


namespace Ironclad
{

    public partial class Python25Mapper
    {


        public override IntPtr Make_PyExc_SystemError()
        {
            return this.Store(ExceptionConverter.GetPythonException("SystemError"));
        }
    }
}
