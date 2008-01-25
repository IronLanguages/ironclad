
import os
import unittest
from textwrap import dedent

from System import IntPtr
from JumPy import AddressGetterDelegate, PydImporter, Python25Mapper, PythonMapper, StubReference
from IronPython.Hosting import PythonEngine

bz2_doc = """The python bz2 module provides a comprehensive interface for
the bz2 compression library. It implements a complete file
interface, one shot (de)compression functions, and types for
sequential (de)compression.
"""

bz2_compress_doc = """compress(data [, compresslevel=9]) -> string

Compress data in one shot. If you want to compress data sequentially,
use an instance of BZ2Compressor instead. The compresslevel parameter, if
given, must be a number between 1 and 9.
"""

bz2_decompress_doc = """decompress(data) -> decompressed data

Decompress data in one shot. If you want to decompress data sequentially,
use an instance of BZ2Decompressor instead.
"""


class FunctionalityTest(unittest.TestCase):

    def testCanCallbackIntoManagedCode(self):
        params = []
        class MyPM(PythonMapper):
            def Py_InitModule4(self, name, methods, doc, _self, apiver):
                params.append((name, methods, doc, _self, apiver))
                return IntPtr.Zero

        sr = StubReference(os.path.join("build", "python25.dll"))
        sr.Init(AddressGetterDelegate(MyPM().GetAddress))
        PydImporter().load("C:\\Python25\\Dlls\\bz2.pyd")

        name, methods, doc, _self, apiver = params[0]
        self.assertEquals(name, "bz2", "wrong name")
        self.assertNotEquals(methods, IntPtr.Zero, "expected some actual methods here")
        self.assertTrue(doc.startswith("The python bz2 module provides a comprehensive interface for\n"),
                        "wrong docstring")
        self.assertEquals(_self, IntPtr.Zero, "expected null pointer")
        self.assertEquals(apiver, 1013, "meh, thought this would be different")


    def testCanCreateIronPythonModule(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        sr = StubReference(os.path.join("build", "python25.dll"))
        sr.Init(AddressGetterDelegate(mapper.GetAddress))
        PydImporter().load("C:\\Python25\\Dlls\\bz2.pyd")

        engine.Execute(dedent("""
            import bz2
            assert bz2.__doc__ == '''%s'''

            assert callable(bz2.compress)
            assert bz2.compress.__doc__ == '''%s'''
            assert callable(bz2.decompress)
            assert bz2.decompress.__doc__ == '''%s'''
            """) % (bz2_doc, bz2_compress_doc, bz2_decompress_doc)
        )



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(FunctionalityTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


