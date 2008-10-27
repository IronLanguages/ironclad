
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase
from tests.utils.memory import CreateTypes

from System import IntPtr

from Ironclad import Python25Mapper
from Ironclad.Structs import EvalToken

class ExecTest(TestCase):
    
    def testPyRun_StringFlags_Trivial(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)

        globals_ = {'foo': 'bar'}
        resultPtr = mapper.PyRun_StringFlags(
            "baz = 123\nqux = foo", int(EvalToken.Py_file_input), mapper.Store(globals_), IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(resultPtr, mapper._Py_NoneStruct)
        self.assertEquals(globals_['foo'], 'bar')
        self.assertEquals(globals_['baz'], 123)
        self.assertEquals(globals_['qux'], 'bar')
        
        mapper.Dispose()
        deallocTypes()
    
    def testPyRun_StringFlags_Error(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)

        resultPtr = mapper.PyRun_StringFlags(
            "raise ValueError('amoral')", int(EvalToken.Py_file_input), mapper.Store({}), IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(resultPtr, IntPtr.Zero)
        self.assertMapperHasError(mapper, ValueError)
        
        mapper.Dispose()
        deallocTypes()


suite = makesuite(
    ExecTest,
)

if __name__ == '__main__':
    run(suite)