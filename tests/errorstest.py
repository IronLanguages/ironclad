import sys
from tests.utils.runtest import automakesuite, run
from tests.utils.testcase import TestCase, WithMapper, WithPatchedStdErr

import System
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal

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
    @WithPatchedStdErr
    def testPyErr_Print(self, mapper, _, stderr_writes):
        mapper.LastException = None
        self.assertRaises(Exception, mapper.PyErr_Print)
        
        mapper.LastException = AttributeError("twaddle")
        mapper.PyErr_Print()
        
        self.assertEquals(stderr_writes, [("twaddle",), ('\n',)])


suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)
