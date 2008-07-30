
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

import System
from System import IntPtr
from System.IO import MemoryStream, StreamReader
from System.Text import Encoding
from Ironclad import Python25Mapper


class Python25Mapper_Exception_Test(TestCase):

    def testException(self):
        mapper = Python25Mapper()
        self.assertEquals(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEquals(type(mapper.LastException), System.Exception,
                          "get should retrieve last set exception")
        self.assertEquals(mapper.LastException.Message, "doozy",
                          "get should retrieve last set exception")
        mapper.Dispose()


    def testPyErr_SetString_WithNull(self):
        mapper = Python25Mapper()

        msg = "You froze your tears and made a dagger"
        mapper.PyErr_SetString(IntPtr.Zero, msg)

        self.assertEquals(type(mapper.LastException), System.Exception,
                          "failed to set exception")
        self.assertEquals(mapper.LastException.Message, msg,
                          "set wrong exception message")
        mapper.Dispose()


    def testPyErr_Occurred(self):
        mapper = Python25Mapper()
        
        mapper.LastException = Exception("borked")
        errorPtr = mapper.Store(mapper.LastException)
        self.assertEquals(mapper.PyErr_Occurred(), errorPtr)
        mapper.FreeTemps()
        self.assertEquals(mapper.RefCount(errorPtr), 1, 'was not a temp object')
        
        mapper.LastException = None
        self.assertEquals(mapper.PyErr_Occurred(), IntPtr.Zero)
        
        mapper.Dispose()


    def testPyErr_Clear(self):
        mapper = Python25Mapper()
        
        mapper.LastException = Exception("borked")
        mapper.PyErr_Clear()
        self.assertEquals(mapper.LastException, None, "failed to clear")
        mapper.PyErr_Clear()
        
        mapper.Dispose()
        

    def testPyErr_Print(self):
        mapper = Python25Mapper()
        
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
        
        mapper.Dispose()


    def assertSetStringSetsCorrectError(self, name):
        mapper = Python25Mapper()
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
        mapper.Dispose()
        

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
    Python25Mapper_Exception_Test,
)

if __name__ == '__main__':
    run(suite)