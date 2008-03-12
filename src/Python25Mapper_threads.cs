using System;
using System.Threading;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override IntPtr PyThread_allocate_lock(/* no args */)
        {
            return this.Store(new Object());
        }

        public override int PyThread_acquire_lock(IntPtr lockPtr, int flags)
        {
            object lockObject = this.Retrieve(lockPtr);
            if (flags == 1)
            {
                // this does not precisely match spec: we still return 1 if
                // the current thread has already acquired a lock.
                Monitor.Enter(lockObject);
                return 1;
            }
            else
            {
                bool entered = Monitor.TryEnter(lockObject);
                if (entered)
                {
                    return 1;
                }
                return 0;
            }
        }

        public override void PyThread_release_lock(IntPtr lockPtr)
        {
            Monitor.Exit(this.Retrieve(lockPtr));
        }

        public override void PyThread_free_lock(IntPtr lockPtr)
        {
            this.PyObject_Free(lockPtr);
        }
    }
}
