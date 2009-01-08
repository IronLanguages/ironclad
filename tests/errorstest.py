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
    def testPyErr_Occurred(self, mapper, _):
        mapper.LastException = Exception("borked")
        errorPtr = mapper.PyErr_Occurred()
        self.assertEquals(mapper.Retrieve(errorPtr), Exception)
        refcnt = mapper.RefCount(errorPtr)
        
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        self.assertEquals(mapper.RefCount(errorPtr), refcnt - 1, 'was not a temp object')
        
        mapper.LastException = None
        self.assertEquals(mapper.PyErr_Occurred(), IntPtr.Zero)


    @WithMapper
    def testPyErr_Clear(self, mapper, _):
        mapper.LastException = Exception("borked")
        mapper.PyErr_Clear()
        self.assertEquals(mapper.LastException, None, "failed to clear")
        mapper.PyErr_Clear()


    @WithMapper
    def testPyErr_FetchRestoreError(self, mapper, addToCleanUp):
        mapper.LastException = Exception("borked")
        space = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 3)
        addToCleanUp(lambda: Marshal.FreeHGlobal(space))

        typePtrPtr = space
        valuePtrPtr = CPyMarshal.Offset(typePtrPtr, CPyMarshal.PtrSize)
        tbPtrPtr = CPyMarshal.Offset(valuePtrPtr, CPyMarshal.PtrSize)
        
        mapper.PyErr_Fetch(typePtrPtr, valuePtrPtr, tbPtrPtr)
        self.assertEquals(mapper.LastException, None)
        
        typePtr = CPyMarshal.ReadPtr(typePtrPtr)
        self.assertEquals(mapper.Retrieve(typePtr), Exception)
        
        valuePtr = CPyMarshal.ReadPtr(valuePtrPtr)
        self.assertEquals(mapper.Retrieve(valuePtr), "borked")
        
        tbPtr = CPyMarshal.ReadPtr(tbPtrPtr)
        self.assertEquals(tbPtr, IntPtr.Zero)
        
        mapper.PyErr_Restore(typePtr, valuePtr, tbPtr)
        self.assertEquals(type(mapper.LastException), Exception)
        self.assertEquals(str(mapper.LastException), "borked")


    @WithMapper
    def testPyErr_RestoreErrorNoValue(self, mapper, addToCleanUp):
        mapper.PyErr_Restore(mapper.Store(IndexError), IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(type(mapper.LastException), IndexError)
        self.assertEquals(mapper.LastException.args, tuple())


    @WithMapper
    def testPyErr_FetchRestoreNoError(self, mapper, addToCleanUp):
        space = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 3)
        addToCleanUp(lambda: Marshal.FreeHGlobal(space))

        typePtrPtr = space
        valuePtrPtr = CPyMarshal.Offset(typePtrPtr, CPyMarshal.PtrSize)
        tbPtrPtr = CPyMarshal.Offset(valuePtrPtr, CPyMarshal.PtrSize)
        
        mapper.PyErr_Fetch(typePtrPtr, valuePtrPtr, tbPtrPtr)
        self.assertEquals(mapper.LastException, None)
        
        typePtr = CPyMarshal.ReadPtr(typePtrPtr)
        self.assertEquals(typePtr, IntPtr.Zero)
        
        valuePtr = CPyMarshal.ReadPtr(valuePtrPtr)
        self.assertEquals(valuePtr, IntPtr.Zero)
        
        tbPtr = CPyMarshal.ReadPtr(tbPtrPtr)
        self.assertEquals(tbPtr, IntPtr.Zero)
        
        mapper.LastException = Exception("make sure Restore null clears error")
        mapper.PyErr_Restore(typePtr, valuePtr, tbPtr)
        self.assertEquals(mapper.LastException, None)


    @WithMapper
    def testPyErr_Print(self, mapper, _):
        mapper.LastException = None
        self.assertRaises(Exception, mapper.PyErr_Print)
        
        somethingToWrite = "yes, I know this isn't an exception; no, I don't want to test precise traceback printing."
        mapper.LastException = somethingToWrite
        
        calls = []
        old = sys.stderr
        sys.stderr = my_stderr(calls)
        try:
            mapper.PyErr_Print()
        finally:
            sys.stderr = old
        
        self.assertEquals(calls, [(somethingToWrite,), ('\n',)])
        

    @WithMapper
    def testPyErr_NewException(self, mapper, _):
        newExcPtr = mapper.PyErr_NewException("foo.bar.bazerror", IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.RefCount(newExcPtr), 2)
        
        newExc = mapper.Retrieve(newExcPtr)
        self.assertEquals(newExc.__name__, 'bazerror')
        self.assertEquals(newExc.__module__, 'foo.bar')
        self.assertEquals(issubclass(newExc, Exception), True)


    def assertMatch(self, mapper, given, exc, expected):
        self.assertEquals(mapper.PyErr_GivenExceptionMatches(
            mapper.Store(given), mapper.Store(exc)), expected)
        

    @WithMapper
    def testPyErr_GivenExceptionMatches(self, mapper, _):
        self.assertMatch(mapper, TypeError, TypeError, 1)
        self.assertMatch(mapper, TypeError(), TypeError, 1)
        self.assertMatch(mapper, TypeError, (TypeError, float), 1)
        self.assertMatch(mapper, TypeError(), (TypeError, float), 1)
        self.assertMatch(mapper, ValueError, TypeError, 0)
        self.assertMatch(mapper, ValueError(), TypeError, 0)
        self.assertMatch(mapper, ValueError, (TypeError, float), 0)
        self.assertMatch(mapper, ValueError(), (TypeError, float), 0)
        
        specificInstance = TypeError('yes, this specific TypeError')
        self.assertMatch(mapper, specificInstance, specificInstance, 1)
        
        
        calls = []
        old = sys.stderr
        sys.stderr = my_stderr(calls)
        try:
            self.assertMatch(mapper, 'whatever', str, 0)
        finally:
            sys.stderr = old
        
        expectedCalls = [
            ('PyErr_GivenExceptionMatches: something went wrong. Assuming exception does not match.',), 
            ('\n',)
        ]
        self.assertEquals(calls, expectedCalls)


    def assertRestoreSetsCorrectError(self, mapper, name):
        errorPtr = mapper.GetAddress("PyExc_" + name)
        self.assertNotEquals(errorPtr, IntPtr.Zero, "failed to find %s" % name)

        msg = "I can has meme?"
        mapper.LastException = None
        mapper.PyErr_Restore(errorPtr, mapper.Store(msg), IntPtr.Zero)
        try:
            raise mapper.LastException
        except BaseException, e:
            self.assertEquals(type(e), eval(name), "error was not a %s" % name)
            self.assertEquals(str(e), msg, "wrong message")
        else:
            self.fail("got no exception")


    @WithMapper
    def testSetsMostErrors(self, mapper, _):
        errors = (
            "BaseException",
            "Exception",
            "StopIteration",
            "GeneratorExit",
            "StandardError",
            "ArithmeticError",
            "LookupError",
            "AssertionError",
            "AttributeError",
            "EnvironmentError",
            "EOFError",
            "FloatingPointError",
            "IOError",
            "OSError",
            "ImportError",
            "IndexError",
            "KeyError",
            "KeyboardInterrupt",
            "MemoryError",
            "NameError",
            "OverflowError",
            "RuntimeError",
            "NotImplementedError",
            "IndentationError",
            "TabError",
            "ReferenceError",
            "SystemError",
            "TypeError",
            "ValueError",
            "ZeroDivisionError",
            "Warning",
            "UserWarning",
            "UnicodeWarning",
            "DeprecationWarning",
            "PendingDeprecationWarning",
            "SyntaxWarning",
            "RuntimeWarning",
            "FutureWarning",
            "ImportWarning",
            
            "SyntaxError",
            "SystemExit",
            "WindowsError",
            "UnboundLocalError",
            "UnicodeError",

        )
        for error in errors:
            self.assertRestoreSetsCorrectError(mapper, error)
        
        # TODO: the following errors are a hassle to construct, and are being ignored for now:
        #
        #    "UnicodeEncodeError",
        #    "UnicodeDecodeError",
        #    "UnicodeTranslateError",
        #

suite = makesuite(
    LastExceptionTest,
    ErrFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
