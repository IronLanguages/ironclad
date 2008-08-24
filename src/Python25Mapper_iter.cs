using System;
using System.Collections;

using Microsoft.Scripting;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {

        public override IntPtr
        PySeqIter_New(IntPtr seqPtr)
        {
            try
            {
                object seq = this.Retrieve(seqPtr);
                return this.Store(PythonOps.GetEnumerator(seq));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyObject_GetIter(IntPtr objPtr)
        {
            IEnumerable enumerable = this.Retrieve(objPtr) as IEnumerable;
            if (enumerable == null)
            {
                this.LastException = new ArgumentTypeException("PyObject_GetIter: object is not iterable");
                return IntPtr.Zero;
            }
            return this.Store(enumerable.GetEnumerator());
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