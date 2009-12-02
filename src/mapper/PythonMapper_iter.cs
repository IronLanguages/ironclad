using System;
using System.Collections;

using Microsoft.Scripting;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override IntPtr
        PyObject_SelfIter(IntPtr objPtr)
        {
            this.IncRef(objPtr);
            return objPtr;
        }


        public override IntPtr
        PyObject_GetIter(IntPtr objPtr)
        {
            try
            {
                object obj = this.Retrieve(objPtr);
                return this.Store(Builtin.iter(this.scratchContext, obj));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyIter_Next(IntPtr iterPtr)
        {
            IEnumerator enumerator = this.Retrieve(iterPtr) as IEnumerator;
            if (enumerator == null)
            {
                this.LastException = new ArgumentTypeException("PyIter_Next: object is not an iterator");
                return IntPtr.Zero;
            }
            try
            {
                bool notFinished = enumerator.MoveNext();
                if (notFinished)
                {
                    return this.Store(enumerator.Current);
                }
                return IntPtr.Zero;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
