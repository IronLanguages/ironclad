
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from System.Threading import Thread, ThreadStart

from Ironclad import Lock, LockException


class LockTest(TestCase):
    
    def testSingleThreaded(self):
        lock = Lock()
        self.assertEqual(lock.IsAcquired, False)
        
        self.assertEqual(lock.Acquire(), 1)
        self.assertEqual(lock.IsAcquired, True)
        self.assertEqual(lock.CountAcquired, 1)
        
        self.assertEqual(lock.Acquire(), 2)
        self.assertEqual(lock.IsAcquired, True)
        self.assertEqual(lock.CountAcquired, 2)

        lock.Release()
        self.assertEqual(lock.IsAcquired, True)
        self.assertEqual(lock.CountAcquired, 1)
        
        self.assertEqual(lock.Acquire(), 2)
        self.assertEqual(lock.IsAcquired, True)
        self.assertEqual(lock.CountAcquired, 2)

        lock.Release()
        self.assertEqual(lock.IsAcquired, True)
        self.assertEqual(lock.CountAcquired, 1)

        lock.Release()
        self.assertEqual(lock.IsAcquired, False)
        self.assertEqual(lock.CountAcquired, 0)


    def testMultiThreaded(self):
        lock = Lock()
        
        def TestCanAcquire():
            self.assertEqual(lock.Acquire(), 1)
            self.assertEqual(lock.IsAcquired, True)
            lock.Release()
        t = Thread(ThreadStart(TestCanAcquire))
        t.Start()
        t.Join()
        
        lock.Acquire()
        
        def TestCannotAcquire():
            self.assertEqual(lock.TryAcquire(), False)
            self.assertEqual(lock.IsAcquired, False)
        t = Thread(ThreadStart(TestCannotAcquire))
        t.Start()
        t.Join()
        
        lock.Release()
        

suite = makesuite(
    LockTest,
)
if __name__ == '__main__':
    run(suite)
