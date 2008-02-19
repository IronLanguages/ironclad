
import unittest
from tests.utils.runtest import makesuite, run

from System import IntPtr

from JumPy.Structs import METH, PyMethodDef


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


suite = makesuite(Python25StructsTest)

if __name__ == '__main__':
    run(suite)