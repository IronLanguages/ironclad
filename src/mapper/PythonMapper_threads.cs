using System;
using System.Threading;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        private Counter
        lockCount
        {
            get
            {
                Counter lockCount = (Counter)Thread.GetData(this._lockCount);
                if (lockCount == null)
                {
                    lockCount = new Counter();
                    Thread.SetData(this._lockCount, lockCount);
                }
                return lockCount;
            }
        }

        private ThreadState
        threadState
        {
            get
            {
                ThreadState threadState = (ThreadState)Thread.GetData(this._threadState);
                if (threadState == null)
                {
                    threadState = new ThreadState(this);
                    Thread.SetData(this._threadState, threadState);
                }
                return threadState;
            }
        }
        
        public object LastException
        {
            get
            {
                return this.threadState.LastException;
            }
            set
            {
                if (this.logErrors)
                {
                    Console.WriteLine();
                    Console.WriteLine("Error: {0}", value);
                    Console.WriteLine();
                    Console.WriteLine(Environment.StackTrace);
                    Console.WriteLine();
                }
                this.threadState.LastException = value;
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
            this.lockCount.Increment();
            if (lockCount.Value == 1)
            {
                this.ReleaseGIL();
                return new IntPtr(1);
            }
            return IntPtr.Zero;
        }

        public override void
        PyEval_RestoreThread(IntPtr token)
        {
            this.lockCount.Decrement();
            if (this.lockCount.Value < 0)
            {
                throw new Exception("Tried to restore a thread that wasn't saved?");
            }
            if (token != IntPtr.Zero || lockCount.Value == 0)
            {
                lockCount.Reset();
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
                CPyMarshal.WritePtr(this._PyThreadState_Current, this.threadState.Ptr);
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
