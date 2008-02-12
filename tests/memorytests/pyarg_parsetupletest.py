
import tests.memorytests.loadassemblies

import os
import unittest
from tests.memorytests.leaktestcase import RunSeparateProcessTest
from tests.utils.memory import OffsetPtr

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from JumPy import AddressGetterDelegate, CPyMarshal, DataSetterDelegate, PythonMapper, StubReference

from JumPyTestUtils import PythonStubHarness


class PyArg_ParseTupleTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        test = self
        class MyPM(PythonMapper):
            def PyArg_ParseTuple(self, args, format, argptr):
                test.assertMatchesVargargs((args, format, argptr))
                return 1

        self.sr = StubReference(os.path.join("build", "python25.dll"))
        self.pm = MyPM()
        self.sr.Init(AddressGetterDelegate(self.pm.GetAddress), DataSetterDelegate(self.pm.SetData))


    def tearDown(self):
        self.sr.Dispose()
        del self.pm


    def assertMatchesVargargs(self, params):
        self.assertEquals(params[:2], (IntPtr(1), "i" * len(self.varargs)),
                          "error marshalling easy args")

        argPtr = params[2]
        for i, ptr in enumerate(self.varargs):
            thisArgAddressPtr = OffsetPtr(argPtr, CPyMarshal.PtrSize * i)
            thisArgAddress = CPyMarshal.ReadPtr(thisArgAddressPtr)
            self.assertEquals(thisArgAddress, ptr, "error marshalling varargs")


    def assertMarshalsVarargs(self, varargs):
        testFuncName = "Test_PA_PT__%darg" % len(varargs)
        testFunc = getattr(PythonStubHarness, testFuncName)
        self.varargs = varargs
        result = testFunc(IntPtr(1), "i" * len(varargs), *varargs)
        self.assertEquals(result, 1, "bad return value")


    def test1Arg(self):
        self.assertMarshalsVarargs((IntPtr(100),))


    def test2Args(self):
        self.assertMarshalsVarargs((IntPtr(100), IntPtr(200)))


    def test3Args(self):
        self.assertMarshalsVarargs((IntPtr(100), IntPtr(200), IntPtr(300)))



if __name__ == '__main__':
    RunSeparateProcessTest(PyArg_ParseTupleTest)