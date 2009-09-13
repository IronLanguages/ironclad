using System;
using System.Threading;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private ThreadState
        ts
        {
            get
            {
                ThreadState ts = (ThreadState)Thread.GetData(this.threadStateStore);
                if (ts == null)
                {
                    ts = new ThreadState(this);
                    Thread.SetData(this.threadStateStore, ts);
                }
                return ts;
            }
        }
        
        public object LastException
        {
            get
            {
                return this.ts.LastException;
            }
            set
            {
                if (this.logErrors)
                {
                    Console.WriteLine(value);
                    Console.WriteLine(Environment.StackTrace);
                }
                this.ts.LastException = value;
            }
        }

        public override IntPtr 
        PyThread_allocate_lock()
        {
            return this.Store(new Lock());
        }

        public override void 
        PyThread_free_lock(IntPtr lockPtr)
        {
            Lock lock_ = (Lock)this.Retrieve(lockPtr);
            lock_.Dispose();
            this.Unmap(lockPtr);
        }

        public override int 
        PyThread_acquire_lock(IntPtr lockPtr, int flags)
        {
            Lock lock_ = (Lock)this.Retrieve(lockPtr);
            if (lock_.IsAcquired)
            {
                return 0;
            }
            
            if (flags == 1)
            {
                lock_.Acquire();
                return 1;
            }
            else
            {
                if (lock_.TryAcquire())
                {
                    return 1;
                }
                return 0;
            }
        }

        public override void 
        PyThread_release_lock(IntPtr lockPtr)
        {
            Lock lock_ = (Lock)this.Retrieve(lockPtr);
            lock_.Release();
        }

        public override void
        PyEval_InitThreads()
        {
        }

        public override IntPtr
        PyEval_SaveThread()
        {
            ThreadLocalCounter threadLock = (ThreadLocalCounter)Thread.GetData(this.threadLockStore);
            if (threadLock == null)
            {
                threadLock = new ThreadLocalCounter();
                Thread.SetData(this.threadLockStore, threadLock);
            }
            threadLock.Increment();
            if (threadLock.Count == 1)
            {
                this.ReleaseGIL();
                return new IntPtr(1);
            }
            return IntPtr.Zero;
        }

        public override void
        PyEval_RestoreThread(IntPtr token)
        {
            // no check: if someone calls Restore before Save we may as well just explode
            ThreadLocalCounter threadLock = (ThreadLocalCounter)Thread.GetData(this.threadLockStore);
            threadLock.Decrement();
            if (token != IntPtr.Zero || threadLock.Count == 0)
            {
                threadLock.Reset();
                this.EnsureGIL();
            }
        }

        // I can only assume that an enum is near-enough the same as an int, and I choose
        // to assume that nobody ever does anything interesting with the return value.
        // I also assume nobody will call Ensure twice without an intervening Release
        public override int
        PyGILState_Ensure()
        {
            this.EnsureGIL();
            return 0;
        }

        public override void
        PyGILState_Release(int _)
        {
            this.ReleaseGIL();
        }
        
        
        public void
        EnsureGIL()
        {
            if (this.GIL.Acquire() == 1)
            {
                CPyMarshal.WritePtr(this._PyThreadState_Current, this.ts.Ptr);
            }
        }
        
        public void
        ReleaseGIL()
        {
            foreach (IntPtr ptr in this.tempObjects)
            {
                this.DecRef(ptr);
            }
            this.tempObjects.Clear();
            this.map.CheckBridgePtrs(false);
            
            if (this.GIL.CountAcquired == 1)
            {
                CPyMarshal.WritePtr(this._PyThreadState_Current, IntPtr.Zero);
            }
            this.GIL.Release();
        }
        
    }
}
