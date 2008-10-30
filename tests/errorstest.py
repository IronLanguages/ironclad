
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.memory import CreateTypes

import System
from System import IntPtr
from System.IO import MemoryStream, StreamReader
from System.Runtime.InteropServices import Marshal
from System.Text import Encoding
from Ironclad import CPyMarshal, Python25Mapper


class LastExceptionTest(TestCase):

    @WithMapper
    def testException(self, mapper, _):
        self.assertEquals(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEquals(type(mapper.LastException), System.Exception,
                          "get should retrieve last set exception")
        self.assertEquals(mapper.LastException.Message, "doozy",
                          "get should retrieve last set exception")


class ErrFunctionsTest(TestCase):

    @WithMapper
    def testPyErr_SetString_WithNull(self, mapper, _):
        msg = "You froze your tears and made a dagger"
        mapper.PyErr_SetString(IntPtr.Zero, msg)

        self.assertEquals(type(mapper.LastException), System.Exception,
                          "failed to set exception")
        self.assertEquals(mapper.LastException.Message, msg,
                          "set wrong exception message")


    @WithMapper
    def testPyErr_Occurred(self, mapper, _):
        mapper.LastException = Exception("borked")
        errorPtr = mapper.Store(mapper.LastException)
        self.assertEquals(mapper.PyErr_Occurred(), errorPtr)
        mapper.FreeTemps()
        self.assertEquals(mapper.RefCount(errorPtr), 1, 'was not a temp object')
        
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
        
        mapper.PyErr_Restore(typePtr, valuePtr, tbPtr)
        self.assertEquals(mapper.LastException, None)


    @WithMapper
    def testPyErr_Print(self, mapper, _):
        mapper.LastException = None
        self.assertRaises(Exception, mapper.PyErr_Occurred())
        
        somethingToWrite = "yes, I know this isn't an exception; no, I don't want to test precise traceback printing."
        mapper.LastException = somethingToWrite
        stderr = MemoryStream()
        mapper.Engine.Runtime.IO.SetErrorOutput(stderr, Encoding.UTF8)
        mapper.PyErr_Print()
        
        stderr.Flush()
        stderr.Position = 0
        printed = StreamReader(stderr, True).ReadToEnd()
        self.assertEquals(printed, somethingToWrite + '\r\n')
        self.assertEquals(mapper.LastException, None)


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
        
        self.assertMatch(mapper, 'whatever', str, 0)


    @WithMapper
    def assertSetStringSetsCorrectError(self, name, mapper, _):
        errorPtr = mapper.GetAddress("PyExc_" + name)
        self.assertNotEquals(errorPtr, IntPtr.Zero, "failed to find %s" % name)

        msg = "I can has meme?"
        mapper.PyErr_SetString(errorPtr, msg)
        try:
            raise mapper.LastException
        except BaseException, e:
            self.assertEquals(isinstance(e, eval(name)), True, "error was not a %s" % name)
            self.assertEquals(str(e), msg, "wrong message")
        else:
            self.fail("got no exception")


    def testSetsMostErrors(self):
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
            self.assertSetStringSetsCorrectError(error)
        
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
