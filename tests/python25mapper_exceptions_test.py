
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

import System
from System import IntPtr
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
        
        # the following errors are a hassle to construct, and are being ignored for now:
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