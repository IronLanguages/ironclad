
import unittest

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import METH, PyMethodDef, Python25Mapper, StubReference
from IronPython.Hosting import PythonEngine

class Python25StructsTest(unittest.TestCase):

    def testConstructPyMethodDef(self):
        pmd = PyMethodDef(
            "jennifer",
            IntPtr.Zero,
            METH.VARARGS,
            "jennifer's docs"
        )
        self.assertEquals(pmd.ml_name, "jennifer", "field not remembered")
        self.assertEquals(pmd.ml_meth, IntPtr.Zero, "field not remembered")
        self.assertEquals(pmd.ml_flags, METH.VARARGS, "field not remembered")
        self.assertEquals(pmd.ml_doc, "jennifer's docs", "field not remembered")


suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(Python25StructsTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)