using System;
using System.Threading;

using IronPython.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyThreadState_GetDict()
        {
            ThreadLocalDict threadDict = (ThreadLocalDict)Thread.GetData(this.threadDictStore);
            if (threadDict == null)
            {
                threadDict = new ThreadLocalDict(this);
                Thread.SetData(this.threadDictStore, threadDict);
            }
            return threadDict.Ptr;
        }
        
        public object LastException
        {
            get
            {
                return Thread.GetData(this.threadErrorStore);
            }
            set
            {
                if (value != null)
                {
                    Exception clrException = value as Exception;
                    if (clrException != null)
                    {
                        value = InappropriateReflection.GetPythonException(clrException);
                    }
                }
                Thread.SetData(this.threadErrorStore, value);
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
            this.Unmap(lockPtr);
        }

        public override int 
        PyThread_acquire_lock(IntPtr lockPtr, int flags)
        {
            Lock lockObject = (Lock)this.Retrieve(lockPtr);
            if (lockObject.IsAcquired)
            {
                return 0;
            }
            
            if (flags == 1)
            {
                lockObject.Acquire();
                return 1;
            }
            else
            {
                if (lockObject.TryAcquire())
                {
                    return 1;
                }
                return 0;
            }
        }

        public override void 
        PyThread_release_lock(IntPtr lockPtr)
        {
            Lock lockObject = (Lock)this.Retrieve(lockPtr);
            lockObject.Release();
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

        // I can only assume that an enum is near-enough the same as an int :)
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
            this.GIL.Acquire();
        }
        
        public void
        ReleaseGIL()
        {
            // CheckBridgePtrs call not explicitly tested; however, if it's not here,
            // you'll run out of memory before too long. Improvements gratefully received.
            this.map.CheckBridgePtrs();
            this.GIL.Release();
        }
        
    }
}
