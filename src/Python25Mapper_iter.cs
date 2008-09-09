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
                    // bugtest.py
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
            try
            {
                object obj = this.Retrieve(objPtr);
                if (Builtin.isinstance(obj, TypeCache.PythonType))
                {
                    // bugtest.py
                    throw new ArgumentTypeException(String.Format("Even though I apparently can iter() {0}, I'm pretty sure I shouldn't", obj));
                }
                return this.Store(Builtin.iter(obj));
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
