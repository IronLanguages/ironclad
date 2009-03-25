import sys
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

import System
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal

class my_stderr(object):
    def __init__(self, calls):
        self.calls = calls
    def write(self, *args):
        self.calls.append(args)

class LastExceptionTest(TestCase):

    @WithMapper
    def testException(self, mapper, _):
        self.assertEquals(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEquals(type(mapper.LastException), Exception,
                          "get should retrieve last set exception")
        self.assertEquals(str(mapper.LastException), "doozy",
                          "get should retrieve last set exception")


class ErrFunctionsTest(TestCase):


    @WithMapper
    def testPyErr_Print(self, mapper, _):
        mapper.LastException = None
        self.assertRaises(Exception, mapper.PyErr_Print)
        
        mapper.LastException = AttributeError("twaddle")
        
        calls = []
        old = sys.stderr
        sys.stderr = my_stderr(calls)
        try:
            mapper.PyErr_Print()
        finally:
            sys.stderr = old
        
        self.assertEquals(calls, [("twaddle",), ('\n',)])
        

    @WithMapper
    def testPyErr_NewException(self, mapper, _):
        newExcPtr = mapper.PyErr_NewException("foo.bar.bazerror", IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.RefCount(newExcPtr), 2)
        
        newExc = mapper.Retrieve(newExcPtr)
        self.assertEquals(newExc.__name__, 'bazerror')
        self.assertEquals(newExc.__module__, 'foo.bar')
        self.assertEquals(issubclass(newExc, Exception), True)
        

    @WithMapper
    def testPyErr_NewException_WithBase(self, mapper, _):
        basePtr = mapper.Store(ValueError)
        newExcPtr = mapper.PyErr_NewException("foo.bar.bazerror", basePtr, IntPtr.Zero)
        self.assertEquals(mapper.RefCount(newExcPtr), 2)
        
        newExc = mapper.Retrieve(newExcPtr)
        self.assertEquals(newExc.__name__, 'bazerror')
        self.assertEquals(newExc.__module__, 'foo.bar')
        self.assertEquals(issubclass(newExc, ValueError), True)
        

    @WithMapper
    def testPyErr_NewException_WithEmptyDict(self, mapper, _):
        newExcPtr = mapper.PyErr_NewException("foo.bar.bazerror", IntPtr.Zero, mapper.Store({}))
        self.assertEquals(mapper.RefCount(newExcPtr), 2)
        
        newExc = mapper.Retrieve(newExcPtr)
        self.assertEquals(newExc.__name__, 'bazerror')
        self.assertEquals(newExc.__module__, 'foo.bar')
        self.assertEquals(issubclass(newExc, Exception), True)


    @WithMapper
    def testPyErr_NewException_WithNonEmptyDict(self, mapper, _):
        attrs = {'foo': 3}
        newExcPtr = mapper.PyErr_NewException("foo.bar.bazerror", IntPtr.Zero, mapper.Store(attrs))
        self.assertEquals(mapper.RefCount(newExcPtr), 2)
        
        newExc = mapper.Retrieve(newExcPtr)
        self.assertEquals(newExc.__name__, 'bazerror')
        self.assertEquals(newExc.__module__, 'foo.bar')
        self.assertEquals(issubclass(newExc, Exception), True)
        self.assertEquals(newExc.foo, 3)


suite = makesuite(
    LastExceptionTest,
    ErrFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
