
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.memory import CreateTypes

from System import IntPtr

from Ironclad import PythonMapper
from Ironclad.Structs import EvalToken

class ExecTest(TestCase):
    
    @WithMapper
    def testPyRun_StringFlags_Trivial(self, mapper, _):
        globals_ = {'foo': 'bar'}
        resultPtr = mapper.PyRun_StringFlags(
            "baz = 123\nqux = foo", int(EvalToken.Py_file_input), mapper.Store(globals_), IntPtr.Zero, IntPtr.Zero)
        self.assertEqual(resultPtr, mapper._Py_NoneStruct)
        self.assertEqual(globals_['foo'], 'bar')
        self.assertEqual(globals_['baz'], 123)
        self.assertEqual(globals_['qux'], 'bar')
    
    @WithMapper
    def testPyRun_StringFlags_Locals(self, mapper, _):
        globals_ = {'foo': 'bar'}
        locals_ = {'baz': 'qux'}
        resultPtr = mapper.PyRun_StringFlags(
            "baz = 123\nqux = foo", int(EvalToken.Py_file_input), mapper.Store(globals_), mapper.Store(locals_), IntPtr.Zero)
        self.assertEqual(resultPtr, mapper._Py_NoneStruct)
        self.assertEqual(globals_['foo'], 'bar')
        self.assertEqual(locals_['baz'], 123)
        self.assertEqual(locals_['qux'], 'bar')


    @WithMapper
    def testPyRun_StringFlags_Error(self, mapper, _):
        resultPtr = mapper.PyRun_StringFlags(
            "raise ValueError('amoral')", int(EvalToken.Py_file_input), mapper.Store({}), IntPtr.Zero, IntPtr.Zero)
        self.assertEqual(resultPtr, IntPtr.Zero)
        self.assertMapperHasError(mapper, ValueError)


suite = makesuite(
    ExecTest,
)

if __name__ == '__main__':
    run(suite)
