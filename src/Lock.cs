using System;
using System.Threading;


namespace Ironclad
{
    
    public class LockException : Exception
    {
        public LockException(string message): base(message)
        {
        }
    }
    
    public class Lock
    {
        private IntPtr hMutex;
        private int count;
        private int owner;
        
        private const int INFINITE = -1;
        private const int ABANDONED = 0x80;
        private const int TIMEOUT = 0x102;
        
        public Lock()
        {
            this.hMutex = Unmanaged.CreateMutex(IntPtr.Zero, 0, IntPtr.Zero);
            this.count = 0;
            this.owner = -1;
        }
        
        ~Lock()
        {
            this.Dispose(false);
        }
        
        public void 
        Dispose()
        {
            GC.SuppressFinalize(this);
            this.Dispose(true);
        }
        
        protected virtual void 
        Dispose(bool disposing)
        {
            if (this.hMutex == IntPtr.Zero)
            {
                return;
            }
            
            while (this.count > 0)
            {
                this.Release();
            }
            Unmanaged.CloseHandle(this.hMutex);
            
            this.hMutex = IntPtr.Zero;
        }
        
    
        public int
        Acquire()
        {
            if (Unmanaged.WaitForSingleObject(this.hMutex, INFINITE) == ABANDONED)
            {
                Console.WriteLine("warning: mutex abandoned\n{0}", System.Environment.StackTrace);
            }
            
            this.owner = Thread.CurrentThread.ManagedThreadId;
            this.count += 1;
            return this.count;
        }
        
        public bool
        TryAcquire()
        {
            int result = Unmanaged.WaitForSingleObject(this.hMutex, 0);
            if (result == TIMEOUT)
            {
                return false;
            }
            if (result == ABANDONED)
            {
                Console.WriteLine("warning: mutex abandoned\n{0}", System.Environment.StackTrace);
            }
            
            this.owner = Thread.CurrentThread.ManagedThreadId;
            this.count += 1;
            return true;
        }
        
        public bool
        IsAcquired
        {
            get
            {
                return (this.owner == Thread.CurrentThread.ManagedThreadId) && (this.count > 0);
            }
        }
        
        public int
        CountAcquired
        {
            get
            {
                if (this.owner == Thread.CurrentThread.ManagedThreadId)
                {
                    return this.count;
                }
                return 0;
            }
        }
        
        public void
        Release()
        {
            if (!this.IsAcquired)
            {
                throw new LockException("you can't release a lock you don't own");
            }
            this.count -= 1;
            if (this.count == 0)
            {
                this.owner = -1;
            }
            if (Unmanaged.ReleaseMutex(this.hMutex) == 0)
            {
                throw new LockException("ReleaseMutex failed, even though we're pretty certain we do own this lock");
            }
        }
    }
}
