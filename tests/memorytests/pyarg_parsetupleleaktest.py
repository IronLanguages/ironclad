
from tests.memorytests.leaktestcase import LeakTestCase, RunSeparateProcessTest

from Ironclad import Python25Mapper
from IroncladTestUtils import PythonStubHarness

from IronPython.Hosting import PythonEngine
from System import IntPtr

class PyArg_ParseTupleLeakTest(LeakTestCase):

    def getPythonMapper(self):
        class MyPM(Python25Mapper):
            def PyArg_ParseTuple(self, args, format, argptr):
                return 1
        return MyPM(PythonEngine())


    def testPyArg_ParseTuple(self):
        def operation():
            PythonStubHarness.Test_PA_PT__3arg(
                IntPtr(1), "iii",
                IntPtr(100), IntPtr(200), IntPtr(300))

        self.assertProbablyDoesntLeak(operation, 5000)


if __name__ == '__main__':
    RunSeparateProcessTest(PyArg_ParseTupleLeakTest)