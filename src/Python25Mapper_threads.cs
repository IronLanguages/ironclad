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
                Thread.SetData(this.threadErrorStore, value);
            }
        }

        public override IntPtr 
        PyThread_allocate_lock()
        {
            return this.Store(new Object());
        }

        public override void 
        PyThread_free_lock(IntPtr lockPtr)
        {
            this.PyObject_Free(lockPtr);
        }

        public override int 
        PyThread_acquire_lock(IntPtr lockPtr, int flags)
        {
            object lockObject = this.Retrieve(lockPtr);
            if (flags == 1)
            {
                // TODO: this does not precisely match spec: we still return 1 if
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

        public override void 
        PyThread_release_lock(IntPtr lockPtr)
        {
            Monitor.Exit(this.Retrieve(lockPtr));
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
        
        /*
        temporary debugging code
        
        public delegate int IntVoidDgt();
        public int GetThreadId()
        {
            return Thread.CurrentThread.ManagedThreadId;
        }
        
        public delegate void VoidStringDgt(string str);
        public void WriteFlush(string info)
        {
            Console.WriteLine("{0} {1}", Stopwatch.GetTimestamp(), info);
            Console.Out.Flush();
        }*/
        
        public void
        EnsureGIL()
        {
            Monitor.Enter(this.dispatcherLock);
            //this.WriteFlush(String.Format("EnsureGIL ({1}) {0}", this.GetThreadId(), Builtin.id(this.dispatcherLock)));
        }
        
        public void
        ReleaseGIL()
        {
            //this.WriteFlush(String.Format("ReleaseGIL ({1}) {0}\n", this.GetThreadId(), Builtin.id(this.dispatcherLock)));
            Monitor.Exit(this.dispatcherLock);
        }
        
    }
}
