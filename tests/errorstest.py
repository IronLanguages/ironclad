import sys
from tests.utils.runtest import automakesuite, run
from tests.utils.testcase import TestCase, WithMapper, WithPatchedStdErr

import System
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal
from Ironclad.Structs import PyObject


class ErrorsTest(TestCase):

    @WithMapper
    def testException(self, mapper, _):
        self.assertEqual(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEqual(type(mapper.LastException), Exception,
                          "get should retrieve last set exception")
        self.assertEqual(str(mapper.LastException), "doozy",
                          "get should retrieve last set exception")
    
    
    @WithMapper
    def testStore(self, mapper, _):
        for type_ in (TypeError, ValueError, IOError):
            excPtr = mapper.Store(type_('whatever'))
            typePtr = CPyMarshal.ReadPtrField(excPtr, PyObject, 'ob_type')
            self.assertEqual(mapper.Retrieve(typePtr), type_)


    @WithMapper
    @WithPatchedStdErr
    def testPyErr_Print(self, mapper, _, stderr_writes):
        mapper.LastException = None
        self.assertRaises(Exception, mapper.PyErr_Print)
        
        mapper.LastException = AttributeError("twaddle")
        mapper.PyErr_Print()
        
        self.assertEqual(stderr_writes, [("twaddle",), ('\n',)])


suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)
