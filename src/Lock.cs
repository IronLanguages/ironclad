using System;
using System.Threading;
using IronPython.Runtime.Exceptions;


namespace Ironclad
{
#if WINDOWS

    public class Lock : IDisposable
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
                throw new SynchronizationLockException("you can't release a lock you don't own");
            }
            this.count -= 1;
            if (this.count == 0)
            {
                this.owner = -1;
            }
            if (Unmanaged.ReleaseMutex(this.hMutex) == 0)
            {
                throw new SynchronizationLockException("ReleaseMutex failed, even though we're pretty certain we do own this lock");
            }
        }
    }

#else

    public sealed class Lock : IDisposable
    {
        private object _mutex;
        private int _count;

        public Lock()
        {
            _mutex = new();
            _count = 0;
        }

        ~Lock()
        {
            Console.WriteLine("warning: mutex not properly disposed\n{0}", System.Environment.StackTrace);
            try
            {
                Dispose(false);
            }
            catch
            {
                Console.WriteLine("warning: finalizing mutex failed");
            }
        }

        public void Dispose()
        {
            GC.SuppressFinalize(this);
            Dispose(true);
        }
        
        private void Dispose(bool disposing)
        {
            if (_mutex is null) return;

            if (_count > 0)
            {
                Monitor.PulseAll(_mutex);
                _count = 0;
            }
            _mutex = null;
        }

        private bool IsDisposed => _mutex is null;

        public int Acquire()
        {
            if (IsDisposed) throw new ObjectDisposedException(nameof(Lock));

            Monitor.Enter(_mutex);
            _count += 1;
            return _count;
        }
        
        public bool TryAcquire()
        {
            if (IsDisposed) return false;

            bool result = Monitor.TryEnter(_mutex);
            if (!result) return false;

            _count += 1;
            return true;
        }

        public bool IsAcquired => !IsDisposed && Monitor.IsEntered(_mutex);

        public int CountAcquired => IsAcquired ? _count : 0;

        public void Release()
        {
            if (IsDisposed) throw new ObjectDisposedException(nameof(Lock));

            Monitor.Exit(_mutex);
            _count -= 1;
        }
    }

#endif
}
