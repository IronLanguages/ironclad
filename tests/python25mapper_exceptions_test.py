
import unittest
from tests.utils.runtest import makesuite, run

import System
from System import IntPtr
from Ironclad import Python25Mapper


class Python25Mapper_Exception_Test(unittest.TestCase):

    def testException(self):
        mapper = Python25Mapper()
        self.assertEquals(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEquals(type(mapper.LastException), System.Exception,
                          "get should retrieve last set exception")
        self.assertEquals(mapper.LastException.Message, "doozy",
                          "get should retrieve last set exception")


    def testPyErr_SetString_WithNull(self):
        mapper = Python25Mapper()

        msg = "You froze your tears and made a dagger"
        mapper.PyErr_SetString(IntPtr.Zero, msg)

        self.assertEquals(type(mapper.LastException), System.Exception,
                          "failed to set exception")
        self.assertEquals(mapper.LastException.Message, msg,
                          "set wrong exception message")


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
        

    def testSetsMostErrors(self):
        errors = (
            "BaseException",
            "StopIteration",
            "StandardError",
            "ArithmeticError",
            "LookupError",
            "AssertionError",
            "AttributeError",
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
            "GeneratorExit",
            "Warning",
            "UserWarning",
            "DeprecationWarning",
            "PendingDeprecationWarning",
            "SyntaxWarning",
            "RuntimeWarning",
            "FutureWarning",
            "ImportWarning",
        )
        for error in errors:
            self.assertSetStringSetsCorrectError(error)

        # for reference, the missing errors are as follows:
        #
        #    "Exception",
        #    "BaseException",
        #    "EnvironmentError",
        #    "SyntaxError",
        #    "SystemExit",
        #    "UnicodeEncodeError",
        #    "UnicodeDecodeError",
        #    "UnicodeWarning"
        #    "UnboundLocalError",
        #    "UnicodeError",
        #    "UnicodeTranslateError",
        #    "WindowsError",
        #
        # ...they will be dealt with when necessary.

suite = makesuite(
    Python25Mapper_Exception_Test,
)

if __name__ == '__main__':
    run(suite)