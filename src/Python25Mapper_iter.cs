using System;
using System.Collections;

using Microsoft.Scripting;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {

        public override IntPtr
        PySeqIter_New(IntPtr seqPtr)
        {
            // I can't just use PythonOps.GetEnumerator here: that will call __iter__, which is a problem
            // if seq is a bridged CPython type whose tp_iter method calls PySeqIter_New (stack overflow :))
            try
            {
                object seq = this.Retrieve(seqPtr);
                if (Builtin.isinstance(seq, TypeCache.PythonType))
                {
                    // I always seem to be able to create an ItemEnumerator when I pass in a 
                    // type, which I'm pretty sure is wrong -- dirty hack fix here.
                    throw new ArgumentTypeException(String.Format("Even though I apparently can enumerate {0}, I'm pretty sure I shouldn't", seq));
                }
                IEnumerator enumerator = InappropriateReflection.CreateItemEnumerator(seq);
                return this.Store(enumerator);
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
