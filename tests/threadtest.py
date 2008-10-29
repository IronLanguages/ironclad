
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.gc import gcwait

from System import IntPtr
from System.Threading import AutoResetEvent, Monitor, Thread, ThreadStart

from Ironclad import Python25Mapper


class PyThread_functions_Test(TestCase):

    @WithMapper
    def testAllocateAndFreeLocks(self, mapper, _):
        lockPtr1 = mapper.PyThread_allocate_lock()
        lockPtr2 = mapper.PyThread_allocate_lock()

        self.assertNotEquals(lockPtr1, lockPtr2, "bad, wrong")

        lockObject1 = mapper.Retrieve(lockPtr1)
        lockObject2 = mapper.Retrieve(lockPtr2)

        self.assertNotEquals(lockObject1, lockObject2, "bad, wrong")

        mapper.PyThread_free_lock(lockPtr1)
        mapper.PyThread_free_lock(lockPtr2)  


    @WithMapper
    def testAcquireAndReleaseLocksWithWait(self, mapper, _):
        lockPtr1 = mapper.PyThread_allocate_lock()
        lockPtr2 = mapper.PyThread_allocate_lock()

        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr1, 1), 1, "claimed failure")
        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr2, 1), 1, "claimed failure")

        acquired = set()
        def AcquireLock(ptr):
            self.assertEquals(mapper.PyThread_acquire_lock(ptr, 1), 1, "claimed failure")
            acquired.add(ptr)
            mapper.PyThread_release_lock(ptr)

        t1 = Thread(ThreadStart(lambda: AcquireLock(lockPtr1)))
        t2 = Thread(ThreadStart(lambda: AcquireLock(lockPtr2)))
        t1.Start()
        t2.Start()
        Thread.CurrentThread.Join(100)

        self.assertEquals(acquired, set(), "not properly locked")

        mapper.PyThread_release_lock(lockPtr1)
        Thread.CurrentThread.Join(100)
        self.assertEquals(acquired, set([lockPtr1]), "release failed")

        mapper.PyThread_release_lock(lockPtr2)
        Thread.CurrentThread.Join(100)
        self.assertEquals(acquired, set([lockPtr1, lockPtr2]), "release failed")    


    @WithMapper
    def testAcquireAndReleaseLocksWithNoWait(self, mapper, _):
        lockPtr1 = mapper.PyThread_allocate_lock()
        lockPtr2 = mapper.PyThread_allocate_lock()

        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr1, 1), 1, "claimed failure")
        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr2, 1), 1, "claimed failure")

        failedToAcquire = set()
        def FailToAcquireLock(ptr):
            self.assertEquals(mapper.PyThread_acquire_lock(ptr, 0), 0, "claimed success")
            failedToAcquire.add(ptr)

        t1 = Thread(ThreadStart(lambda: FailToAcquireLock(lockPtr1)))
        t2 = Thread(ThreadStart(lambda: FailToAcquireLock(lockPtr2)))
        t1.Start()
        t2.Start()
        Thread.CurrentThread.Join(100)

        self.assertEquals(failedToAcquire, set([lockPtr1, lockPtr2]), "failed")

        mapper.PyThread_release_lock(lockPtr1)
        mapper.PyThread_release_lock(lockPtr2)

        acquired = set()
        def AcquireLock(ptr):
            self.assertEquals(mapper.PyThread_acquire_lock(ptr, 0), 1, "claimed failure")
            acquired.add(ptr)
            mapper.PyThread_release_lock(ptr)

        t1 = Thread(ThreadStart(lambda: AcquireLock(lockPtr1)))
        t2 = Thread(ThreadStart(lambda: AcquireLock(lockPtr2)))
        t1.Start()
        t2.Start()
        Thread.CurrentThread.Join(100)

        self.assertEquals(acquired, set([lockPtr1, lockPtr2]), "acquires failed")    


class PyThreadStateDict_Test(TestCase):
    
    @WithMapper
    def testPyThreadState_GetDict(self, mapper, _):
        store = {}
        def GrabThreadDict(key):
            ptr = mapper.PyThreadState_GetDict()
            mapper.IncRef(ptr)
            local = mapper.Retrieve(ptr)
            local['content'] = key
            store[key] = local
            store[key + 'ptr'] = ptr
        
        GrabThreadDict('main')
        for name in ('other', 'another', 'and another'):
            thread = Thread(ThreadStart(lambda: GrabThreadDict(name)))
            thread.Start()
            thread.Join()
        
        gcwait()
        self.assertEquals(store['main']['content'], 'main')
        self.assertEquals(mapper.RefCount(store['mainptr']), 2, 'lost reference to dict while thread still active')
        
        for name in ('other', 'another', 'and another'):
            self.assertEquals(store[name]['content'], name)
            self.assertEquals(mapper.RefCount(store[name + 'ptr']), 1, 'failed to dispose of thread dicts when threads ended')


class PyThreadExceptionTest(TestCase):
    
    @WithMapper
    def testLastExceptionIsThreadLocal(self, mapper, _):
        def CheckOtherThread():
            self.assertEquals(mapper.LastException, None)
            mapper.LastException = ValueError('foo')
            self.assertEquals(isinstance(mapper.LastException, ValueError), True)

        mapper.LastException = TypeError('bar')
        thread = Thread(ThreadStart(CheckOtherThread))
        thread.Start()
        thread.Join()
        self.assertEquals(isinstance(mapper.LastException, TypeError), True)


class PyEvalGILThreadTest(TestCase):
    
    def assertLock(self, lock, expectLocked):
        unlocked = [False]
        def CheckUnlocked():
            unlocked[0] = Monitor.TryEnter(lock)
            if unlocked[0]:
                Monitor.Exit(lock)
        t = Thread(ThreadStart(CheckUnlocked))
        t.Start()
        t.Join()
        self.assertEquals(not unlocked[0], expectLocked)


    @WithMapper
    def testMultipleSaveRestoreOneThread(self, mapper, _):
        lock = mapper.DispatcherModule.Dispatcher._lock
        
        mapper.PyGILState_Ensure()
        self.assertLock(lock, True)
        mapper.PyEval_SaveThread()
        self.assertLock(lock, False)
        mapper.PyEval_SaveThread()
        self.assertLock(lock, False)
        mapper.PyEval_RestoreThread(IntPtr.Zero)
        self.assertLock(lock, False)
        mapper.PyEval_RestoreThread(IntPtr.Zero)
        self.assertLock(lock, True)
        self.assertRaises(Exception, mapper.PyEval_RestoreThread)
        mapper.PyGILState_Release(0)

    
    @WithMapper
    def testMultipleSaveRestoreMultiThread(self, mapper, _):       # order of execution (intended)
        lock = mapper.DispatcherModule.Dispatcher._lock
    
        oneThreadActed = AutoResetEvent(False)
        anotherThreadActed = AutoResetEvent(False)
        
        def OneThread():
            wait = lambda: anotherThreadActed.WaitOne()
            signal = lambda: oneThreadActed.Set()
            
            mapper.PyGILState_Ensure()                  # 1
            signal(); wait()
            
            pe_token = mapper.PyEval_SaveThread()       # 3
            self.assertNotEquals(pe_token, IntPtr.Zero)
            signal(); wait()
            
            self.assertFalse(Monitor.TryEnter(lock))    # 5
            signal(); wait()
            
            self.assertTrue(Monitor.TryEnter(lock))     # 7
            Monitor.Exit(lock)
            signal(); wait()
            
            self.assertTrue(Monitor.TryEnter(lock))     # 9
            Monitor.Exit(lock)
            signal(); wait()
            
            self.assertTrue(Monitor.TryEnter(lock))     # 11
            Monitor.Exit(lock)
            signal(); wait()
            
            self.assertFalse(Monitor.TryEnter(lock))    # 13
            signal(); wait()
            
            mapper.PyEval_RestoreThread(pe_token)       # 15
            signal(); wait()
            
            mapper.PyGILState_Release(0)                # 17

        def AnotherThread():
            wait = lambda: oneThreadActed.WaitOne()
            signal = lambda: anotherThreadActed.Set()
            wait()
            
            self.assertFalse(Monitor.TryEnter(lock))    # 2
            signal(); wait()
            
            mapper.PyGILState_Ensure()                  # 4
            signal(); wait()
            
            pe_token = mapper.PyEval_SaveThread()       # 6
            self.assertNotEquals(pe_token, IntPtr.Zero)
            signal(); wait()
            
            x = mapper.PyEval_SaveThread()              # 8
            self.assertEquals(x, IntPtr.Zero)
            signal(); wait()
            
            mapper.PyEval_RestoreThread(x)              # 10
            signal(); wait()
            
            mapper.PyEval_RestoreThread(pe_token)       # 12
            signal(); wait()
            
            mapper.PyGILState_Release(0)                # 14
            signal(); wait()
            
            self.assertFalse(Monitor.TryEnter(lock))    # 16
            signal()
            
        t = Thread(ThreadStart(AnotherThread))
        t.Start()
        OneThread()
        t.Join()
    
        mapper.Dispose()


suite = makesuite(
    PyThread_functions_Test,
    PyThreadStateDict_Test,
    PyThreadExceptionTest,
    PyEvalGILThreadTest,
)

if __name__ == '__main__':
    run(suite)
