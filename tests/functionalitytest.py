
import os
import unittest
from textwrap import dedent
from tests.utils.runtest import makesuite, run

from System import IntPtr
from JumPy import (
    AddressGetterDelegate, DataSetterDelegate, PydImporter,
    Python25Mapper, PythonMapper, StubReference
)
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

bz2___author__ = """The bz2 python module was written by:

    Gustavo Niemeyer <niemeyer@conectiva.com>
"""

bz2_test_compress = "I wonder why. I wonder why. I wonder why I wonder why. " * 1000
bz2_test_decompress = 'BZh91AY&SYM\xf6FM\x00!\xd9\x95\x80@\x01\x00 \x06A\x90\xa0 \x00\x90 \x1ai\xa0)T4\x1bS\x81R\xa6\tU\xb0J\xad\x02Ur*T\xd0%W\xc0\x95^\x02U`%V\x02Up\tU\xb0J\xae\xc0\x95X\tU\xf8\xbb\x92)\xc2\x84\x82o\xb22h'


class FunctionalityTest(unittest.TestCase):

    def testCanCallbackIntoManagedCode(self):
        params = []
        class MyPM(PythonMapper):
            def Py_InitModule4(self, name, methods, doc, _self, apiver):
                params.append((name, methods, doc, _self, apiver))
                return IntPtr.Zero

        pm = MyPM()
        sr = StubReference(os.path.join("build", "python25.dll"))
        try:
            sr.Init(AddressGetterDelegate(pm.GetAddress), DataSetterDelegate(pm.SetData))
            pi = PydImporter()
            pi.Load("C:\\Python25\\Dlls\\bz2.pyd")
            try:
                name, methods, doc, _self, apiver = params[0]
                self.assertEquals(name, "bz2", "wrong name")
                self.assertNotEquals(methods, IntPtr.Zero, "expected some actual methods here")
                self.assertTrue(doc.startswith("The python bz2 module provides a comprehensive interface for\n"),
                                "wrong docstring")
                self.assertEquals(_self, IntPtr.Zero, "expected null pointer")
                self.assertEquals(apiver, 1013, "yep, python25")
            finally:
                pi.Dispose()
        finally:
            sr.Dispose()

    def testCanCreateIronPythonBZ2ModuleWithMethodsAndDocstrings(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        sr = StubReference(os.path.join("build", "python25.dll"))
        try:
            sr.Init(AddressGetterDelegate(mapper.GetAddress), DataSetterDelegate(mapper.SetData))
            pi = PydImporter()
            pi.Load("C:\\Python25\\Dlls\\bz2.pyd")
            try:
                testCode = dedent("""
                    import bz2
                    assert bz2.__doc__ == '''%s'''
                    """) % bz2_doc
                engine.Execute(testCode)

                testCode = dedent("""
                    assert callable(bz2.compress)
                    assert bz2.compress.__doc__ == '''%s'''
                    assert callable(bz2.decompress)
                    assert bz2.decompress.__doc__ == '''%s'''
                    """) % (bz2_compress_doc, bz2_decompress_doc)
                engine.Execute(testCode)
            finally:
                pi.Dispose()
        finally:
            sr.Dispose()


    def testCanUseMethodsInCreatedBZ2Module(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        sr = StubReference(os.path.join("build", "python25.dll"))
        try:
            sr.Init(AddressGetterDelegate(mapper.GetAddress), DataSetterDelegate(mapper.SetData))
            pi = PydImporter()
            pi.Load("C:\\Python25\\Dlls\\bz2.pyd")
            try:
                testCode = dedent("""
                    import bz2
                    assert bz2.compress(%r) == %r
                    """) % (bz2_test_compress, bz2_test_decompress)
                engine.Execute(testCode)

                testCode = dedent("""
                    assert bz2.decompress(%r) == %r
                    """) % (bz2_test_decompress, bz2_test_compress)
                engine.Execute(testCode)
            finally:
                pi.Dispose()
        finally:
            sr.Dispose()


    def testCreatedBZ2ModuleAuthorString(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        sr = StubReference(os.path.join("build", "python25.dll"))
        try:
            sr.Init(AddressGetterDelegate(mapper.GetAddress), DataSetterDelegate(mapper.SetData))
            pi = PydImporter()
            pi.Load("C:\\Python25\\Dlls\\bz2.pyd")
            try:
                testCode = dedent("""
                    import bz2
                    assert bz2.__author__ == %r
                    """) % (bz2___author__)
                engine.Execute(testCode)
            finally:
                pi.Dispose()
        finally:
            sr.Dispose()


    def testCreatedBZ2ModuleTypesExist(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        sr = StubReference(os.path.join("build", "python25.dll"))
        try:
            sr.Init(AddressGetterDelegate(mapper.GetAddress), DataSetterDelegate(mapper.SetData))
            pi = PydImporter()
            pi.Load("C:\\Python25\\Dlls\\bz2.pyd")
            try:
                testCode = dedent("""
                    import bz2
                    assert bz2.BZ2File.__name__ == 'BZ2File'
                    assert bz2.BZ2File.__module__ == 'bz2'
                    assert bz2.BZ2Compressor.__name__ == 'BZ2Compressor'
                    assert bz2.BZ2Compressor.__module__ == 'bz2'
                    assert bz2.BZ2Decompressor.__name__ == 'BZ2Decompressor'
                    assert bz2.BZ2Decompressor.__module__ == 'bz2'
                    """)
                engine.Execute(testCode)
            finally:
                pi.Dispose()
        finally:
            sr.Dispose()


suite = makesuite(FunctionalityTest)

if __name__ == '__main__':
    run(suite)


