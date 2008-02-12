
from tests.memorytests.leaktestcase import LeakTestCase, RunSeparateProcessTest

from JumPy import PythonMapper
from JumPyTestUtils import PythonStubHarness

from System import IntPtr

class PyArg_ParseTupleLeakTest(LeakTestCase):

    def getPythonMapper(self):
        class MyPM(PythonMapper):
            def PyArg_ParseTuple(self, args, format, argptr):
                return 1
        return MyPM()


    def testPyArg_ParseTuple(self):
        def operation():
            PythonStubHarness.Test_PA_PT__3arg(
                IntPtr(1), "iii",
                IntPtr(100), IntPtr(200), IntPtr(300))

        self.assertProbablyDoesntLeak(operation, 5000)


if __name__ == '__main__':
    RunSeparateProcessTest(PyArg_ParseTupleLeakTest)