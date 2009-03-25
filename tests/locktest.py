
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from System.Threading import Thread, ThreadStart

from Ironclad import Lock, LockException


class LockTest(TestCase):
    
    def testSingleThreaded(self):
        lock = Lock()
        self.assertEquals(lock.IsAcquired, False)
        
        self.assertEquals(lock.Acquire(), 1)
        self.assertEquals(lock.IsAcquired, True)
        self.assertEquals(lock.CountAcquired, 1)
        
        self.assertEquals(lock.Acquire(), 2)
        self.assertEquals(lock.IsAcquired, True)
        self.assertEquals(lock.CountAcquired, 2)

        lock.Release()
        self.assertEquals(lock.IsAcquired, True)
        self.assertEquals(lock.CountAcquired, 1)
        
        self.assertEquals(lock.Acquire(), 2)
        self.assertEquals(lock.IsAcquired, True)
        self.assertEquals(lock.CountAcquired, 2)

        lock.Release()
        self.assertEquals(lock.IsAcquired, True)
        self.assertEquals(lock.CountAcquired, 1)

        lock.Release()
        self.assertEquals(lock.IsAcquired, False)
        self.assertEquals(lock.CountAcquired, 0)


    def testMultiThreaded(self):
        lock = Lock()
        
        def TestCanAcquire():
            self.assertEquals(lock.Acquire(), 1)
            self.assertEquals(lock.IsAcquired, True)
            lock.Release()
        t = Thread(ThreadStart(TestCanAcquire))
        t.Start()
        t.Join()
        
        lock.Acquire()
        
        def TestCannotAcquire():
            self.assertEquals(lock.TryAcquire(), False)
            self.assertEquals(lock.IsAcquired, False)
        t = Thread(ThreadStart(TestCannotAcquire))
        t.Start()
        t.Join()
        
        lock.Release()
        

suite = makesuite(
    LockTest,
)
if __name__ == '__main__':
    run(suite)
