
from tests.memorytests.leaktestcase import LeakTestCase, RunLeakTest

from JumPy import PythonMapper
from JumPyTestUtils import PythonStubHarness

from System import IntPtr

class PyArg_ParseTupleAndKeywordsLeakTest(LeakTestCase):

    def getPythonMapper(self):
        class MyPM(PythonMapper):
            def PyArg_ParseTupleAndKeywords(self, args, kwargs, format, kwlist, argptr):
                return 1
        return MyPM()


    def testPyArg_ParseTupleAndKeywords(self):
        def operation():
            PythonStubHarness.Test_PA_PTAK__3arg(
                IntPtr(1), IntPtr(2), "iii", IntPtr(3),
                IntPtr(100), IntPtr(200), IntPtr(300))

        self.assertProbablyDoesntLeak(operation, 5000)


if __name__ == '__main__':
    RunLeakTest(PyArg_ParseTupleAndKeywordsLeakTest)