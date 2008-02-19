
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

bz2_test_text = "I wonder why. I wonder why. I wonder why I wonder why. " * 1000
bz2_test_data = 'BZh91AY&SYM\xf6FM\x00!\xd9\x95\x80@\x01\x00 \x06A\x90\xa0 \x00\x90 \x1ai\xa0)T4\x1bS\x81R\xa6\tU\xb0J\xad\x02Ur*T\xd0%W\xc0\x95^\x02U`%V\x02Up\tU\xb0J\xae\xc0\x95X\tU\xf8\xbb\x92)\xc2\x84\x82o\xb22h'


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


    def assertWorksWithBZ2(self, testCode):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        sr = StubReference(os.path.join("build", "python25.dll"))
        try:
            sr.Init(AddressGetterDelegate(mapper.GetAddress), DataSetterDelegate(mapper.SetData))
            pi = PydImporter()
            pi.Load("C:\\Python25\\Dlls\\bz2.pyd")
            try:
                engine.Execute("import bz2")
                engine.Execute(testCode)
            finally:
                pi.Dispose()
        finally:
            sr.Dispose()


    def testCanCreateIronPythonBZ2ModuleWithMethodsAndDocstrings(self):
        self.assertWorksWithBZ2(dedent("""
            assert bz2.__doc__ == %r
            assert bz2.__author__ == %r
            assert callable(bz2.compress)
            assert bz2.compress.__doc__ == %r
            assert callable(bz2.decompress)
            assert bz2.decompress.__doc__ == %r
            """) % (bz2_doc,
                    bz2___author__,
                    bz2_compress_doc,
                    bz2_decompress_doc)
        )

    def testCanUseFunctionsInCreatedBZ2Module(self):
        self.assertWorksWithBZ2(dedent("""
            assert bz2.compress(%(uncompressed)r) == %(compressed)r
            assert bz2.decompress(%(compressed)r) == %(uncompressed)r
            """) % {"compressed": bz2_test_data,
                    "uncompressed": bz2_test_text}
        )


    def testCreatedBZ2ModuleTypesExist(self):
        self.assertWorksWithBZ2(dedent("""
            assert bz2.BZ2File.__name__ == 'BZ2File'
            assert bz2.BZ2File.__module__ == 'bz2'
            assert bz2.BZ2Compressor.__name__ == 'BZ2Compressor'
            assert bz2.BZ2Compressor.__module__ == 'bz2'
            assert bz2.BZ2Decompressor.__name__ == 'BZ2Decompressor'
            assert bz2.BZ2Decompressor.__module__ == 'bz2'
            """)
        )

    def testBZ2Compressor(self):
        self.assertWorksWithBZ2(dedent("""
            # adapted from test_bz2.py
            compressor = bz2.BZ2Compressor()
            text = %r
            chunkSize = 50
            n = 0
            data = ''
            while 1:
                chunk = text[n*chunkSize:(n+1)*chunkSize]
                if not chunk:
                    break
                data += compressor.compress(chunk)
                n += 1
            data += compressor.flush()
            assert data == %r
            """) % (bz2_test_text, bz2_test_data)
        )

    def testBZ2Decompressor(self):
        self.assertWorksWithBZ2(dedent("""
            # adapted from test_bz2.py
            decompressor = bz2.BZ2Decompressor()
            data = %r
            chunkSize = 5
            n = 0
            text = ''
            while 1:
                chunk = data[n*chunkSize:(n+1)*chunkSize]
                if not chunk:
                    break
                text += decompressor.decompress(chunk)
                n += 1
            assert text == %r
            """) % (bz2_test_data, bz2_test_text)
        )



suite = makesuite(FunctionalityTest)

if __name__ == '__main__':
    run(suite)


