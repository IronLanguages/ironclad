
import os
import sys
import shutil
import tempfile
from textwrap import dedent
from tests.utils.runtest import automakesuite, run
from tests.utils.testcase import TestCase
from tests.utils.functionaltestcase import FunctionalTestCase

from Ironclad import PythonMapper


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

bz2_test_str = "I wonder why. I wonder why. I wonder why I wonder why. "
bz2_test_text = bz2_test_str * 1000
bz2_test_data = 'BZh91AY&SYM\xf6FM\x00!\xd9\x95\x80@\x01\x00 \x06A\x90\xa0 \x00\x90 \x1ai\xa0)T4\x1bS\x81R\xa6\tU\xb0J\xad\x02Ur*T\xd0%W\xc0\x95^\x02U`%V\x02Up\tU\xb0J\xae\xc0\x95X\tU\xf8\xbb\x92)\xc2\x84\x82o\xb22h'

bz2_test_line = "I wonder why. I wonder why. I wonder why I wonder why.\n"
bz2_test_text_lines = bz2_test_line * 1000

DLL_PATH = os.path.join("build", "ironclad", "python27.dll")
 

def ModuleTestCase(module):
    import_code = 'import ' + module
    locals_ = locals()
    class _ModuleTestCase(TestCase):
        __name__ = module + 'Test'
        def assertRuns(self, test_code=''): 
            mapper = PythonMapper(DLL_PATH)
            try:
                exec '\n'.join([import_code, test_code]) in globals(), locals_
            finally:
                mapper.Dispose()
                if module in sys.modules:
                    del sys.modules[module]
    return _ModuleTestCase


def TrivialModuleTestCase(module):
    test = ModuleTestCase(module)
    test.testImports = test.assertRuns
    return test


class ExternalFunctionalityTest(FunctionalTestCase):

    def testImportHook(self):
        self.assertRuns(dedent("""\
            import bz2
            assert bz2.compress(%(uncompressed)r) == %(compressed)r
            assert bz2.decompress(%(compressed)r) == %(uncompressed)r
            # check that clr imports still work
            import clr
            import System
            """) % {
            "compressed": bz2_test_data,
            "uncompressed": bz2_test_text})


    def testNumPySciPyH5Py(self):
        # combine several tests into one, so we don't have to wait for multiple reloads
        file_path = os.path.abspath(os.path.join('tests', 'data', 'text.txt'))
        file_contents = list(open(file_path).read())
        
        self.assertRuns(dedent("""\
            #=====================================================
            # test we can actually import them
            
            import scipy as sp
            import numpy as np
            
            #=====================================================
            # perform a few basic numpy sanity checks
            
            assert np.core.multiarray.__name__ == 'numpy.core.multiarray'
            
            r1 = np.arange(20)
            r2 = np.arange(20)
            assert r1 is not r2
            assert np.all(r1 == r2)

            r1[...] = 20
            assert np.all(r1 > r2)

            def assert_equals(a, b):
                assert a == b, '%%r != %%r' %% (a, b)
            assert_equals((1+3j), np.complex128(1+3j))
            
            #=====================================================
            # test matrices probably work
            
            m = np.matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
            assert abs(np.linalg.det(m)) < 0.0000001
            
            #=====================================================
            # test memmap when patched
            
            ironclad.patch_native_filenos()
            f = np.core.memmap(%r)
            assert map(chr, f) == %r
            
            #=====================================================
            # adapted from numpy.core.test_print.TestPrint
            # This test is a placeholder for one which fails 
            # due to float formatting differences.

            def mangle(num):
                return str(num).lower().replace('+0', '+')
            def assert_complex_type(type):
                for x in (0, 1,-1, 1e10, 1e20):
                    assert_equals(mangle(type(x)),
                                  mangle(complex(x)).lower())
                    assert_equals(mangle(type(x*1j)).lower(), 
                                  mangle(complex(x*1j)).lower())
                    assert_equals(mangle(type(x + x*1j)).lower(), 
                                  mangle(complex(x + x*1j)).lower())
    
            assert_complex_type(np.cfloat)
            assert_complex_type(np.cdouble)
            
            # this one is a known failure in certain environments, 
            # butI'm not sure how to identify those environments.
            #
            # assert_complex_type(np.clongdouble)
            
            #=====================================================
            # test for no dupe h5 imports
            # we still have dupe .py imports from .pyds for some reason
            
            import h5py
            import sys
            assert 'h5py.h5g.h5' not in sys.modules # .pyd dupes
            assert 'h5py.h5i.h5' not in sys.modules # .pyd dupes
            assert 'h5py.h5t.h5' not in sys.modules # .pyd dupes
            assert 'h5py.h5g._sync' not in sys.modules # .py dupes
            assert 'h5py.h5i._sync' not in sys.modules # .py dupes
            assert 'h5py.h5t._sync' not in sys.modules # .py dupes
            
            """ % (file_path, file_contents)), insert_args='-X:Frames')

    def testPatchNativeFilenos(self):
        self.assertRuns(dedent("""\
            import os
            import sys
            builtinBefore = dict(sys.modules['__builtin__'].__dict__)
            osBefore = dict(sys.modules['os'].__dict__)
            
            ironclad.patch_native_filenos()
            
            # check kwargs propagated
            f = open(%r, mode='r')
            f.close()
            
            ironclad.unpatch_native_filenos()
            
            for k, v in builtinBefore.items():
                assert sys.modules['__builtin__'].__dict__[k] is v
            for k, v in osBefore.items():
                assert sys.modules['os'].__dict__[k] is v
            
            """ % os.path.abspath(__file__)))


class NumpyTest(FunctionalTestCase):

    def testNumpyCrash(self):
        self.assertRuns(dedent("""
            import numpy
            from System.Threading import Thread, ThreadStart
            a = numpy.matrix([[1, 2], [3, 4]])
            b = numpy.matrix([[1, 2], [3, 4]])

            def multiInvert(a):
                for ii in xrange(1000):
                    a = a.I

            t1 = Thread(ThreadStart(lambda: multiInvert(a)))
            t2 = Thread(ThreadStart(lambda: multiInvert(b)))
            t1.Start()
            t2.Start()
            t1.Join()
            t2.Join()
            """), insert_args='-X:Frames -X:Debug')


class BZ2Test(ModuleTestCase('bz2')):

    def testFunctionsAndDocstringsExist(self):
        self.assertRuns(dedent("""
            assert bz2.__doc__ == %r
            assert bz2.__author__ == %r
            assert callable(bz2.compress)
            assert bz2.compress.__doc__ == %r
            assert callable(bz2.decompress)
            assert bz2.decompress.__doc__ == %r
            """) % (bz2_doc,
                    bz2___author__,
                    bz2_compress_doc,
                    bz2_decompress_doc))

    def testFunctionsWork(self):
        self.assertRuns(dedent("""
            assert bz2.compress(%(uncompressed)r) == %(compressed)r
            assert bz2.decompress(%(compressed)r) == %(uncompressed)r
            """) % {"compressed": bz2_test_data,
                    "uncompressed": bz2_test_text})


    def testTypesExist(self):
        self.assertRuns(dedent("""
            assert bz2.BZ2File.__name__ == 'BZ2File'
            assert bz2.BZ2File.__module__ == 'bz2'
            assert bz2.BZ2Compressor.__name__ == 'BZ2Compressor'
            assert bz2.BZ2Compressor.__module__ == 'bz2'
            assert bz2.BZ2Decompressor.__name__ == 'BZ2Decompressor'
            assert bz2.BZ2Decompressor.__module__ == 'bz2'
            """))

    def testCompressor(self):
        self.assertRuns(dedent("""
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
            """) % (bz2_test_text, bz2_test_data))

    def testDecompressor(self):
        self.assertRuns(dedent("""
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
            """) % (bz2_test_data, bz2_test_text))
        

    def testFileRead(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r)
            try:
                assert f.read() == %r
            finally:
                f.close()
            """) % (testPath, bz2_test_text))

    def testFileReadLine(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r)
            try:
                assert f.readline() == %r
                assert f.readline() == ''
            finally:
                f.close()
            """) % (testPath, bz2_test_text))


    def testFileReadLines_Short(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r)
            try:
                lines = f.readlines()
                assert len(lines) == 1000
                assert ''.join(lines) == %r
            finally:
                f.close()
            """) % (testPath, bz2_test_text_lines))


    def testFileReadLines_Long(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r)
            try:
                lines = f.readlines()
                assert lines == [%r]
            finally:
                f.close()
            """) % (testPath, bz2_test_text))


    def testFileIterate(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r)
            try:
                assert f.xreadlines() is f
                assert f.__iter__() is f
                for _ in range(1000):
                    line = f.next() 
                    assert line == %r
                try:
                    f.next()
                    raise AssertionError("iteration did not stop")
                except StopIteration:
                    pass
            finally:
                f.close()
            """) % (testPath, bz2_test_line))

    
    def testFileSeekTell(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertRuns(dedent("""
            def assertSeeksTo(f, seekargs, expectedPosition):
                f.seek(*seekargs)
                assert f.tell() == expectedPosition
                assert f.read() == %r[expectedPosition:]
                f.seek(expectedPosition)
                
            f = bz2.BZ2File(%r)
            try:
                assertSeeksTo(f, (55000,), 55000)
                assertSeeksTo(f, (0,), 0)
                assertSeeksTo(f, (12345, 0), 12345)
                assertSeeksTo(f, (10000, 1), 22345)
                assertSeeksTo(f, (-10000, 1), 12345)
                assertSeeksTo(f, (-55000, 2), 0)
            finally:
                f.close()
            """) % (bz2_test_text, testPath))
        

    def testFileWrite(self):
        # read is tested separately elsewhere, so we assume it works
        testDir = tempfile.mkdtemp()
        path = os.path.join(testDir, "test.bz2")
        self.assertRuns(dedent("""
            w = bz2.BZ2File(%r, 'w')
            try:
                w.write(%r)
            finally:
                w.close()
            r = bz2.BZ2File(%r, 'r')
            try:
                assert r.read() == %r
            finally:
                r.close()
            """) % (path, bz2_test_text, path, bz2_test_text))
        shutil.rmtree(testDir)


    def testHeavyUse(self):
        self.assertRuns(dedent("""
            COUNT = 100
            compressors = [bz2.BZ2Compressor() for _ in range(COUNT)]
            decompressors = [bz2.BZ2Decompressor() for _ in range(COUNT)]
            
            current = %r
            for i in range(COUNT):
                current = decompressors[-i].decompress(
                    compressors[i].compress(current[:i * 40]) + 
                    compressors[i].compress(current[i * 40:]) + 
                    compressors[i].flush())
            
            assert current == %r
            """) % (bz2_test_text, bz2_test_text))
    
    
    def testFileProperties(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r, 'U')
            try:
                #assert f.mode == 'r' # IP2 bug -- no file.mode
                assert f.name == %r
                assert f.closed == False
                assert f.newlines == None
                
                f.readlines()
                assert f.newlines == '\\n'
                
                for attr in ['mode', 'name', 'closed', 'newlines']:
                    try:
                        setattr(f, attr, 123)
                    except AttributeError:
                        pass
                    else:
                        raise AssertionError('unexpected settable attribute: ' + attr)
            finally:
                f.close()
            assert f.closed == True
            """) % (testPath, testPath))


    def testFileMember(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertRuns(dedent("""
            f = bz2.BZ2File(%r)
            try:
                assert f.softspace == 0
                f.softspace = 1
                assert f.softspace == 1
            finally:
                f.close()
            """) % testPath)
        
        
    def assertFileWriteLines(self, sequence):
        # read is tested separately elsewhere, so we assume it works
        testDir = tempfile.mkdtemp()
        path = os.path.join(testDir, "test.bz2")
        self.assertRuns(dedent("""
            w = bz2.BZ2File(%r, 'w')
            try:
                w.writelines(%r)
            finally:
                w.close()
            r = bz2.BZ2File(%r, 'r')
            try:
                assert r.read() == %r
            finally:
                r.close()
            """) % (path, sequence, path, bz2_test_text))
        shutil.rmtree(testDir)
        

    def testFileWriteLines_List(self):
        self.assertFileWriteLines([bz2_test_str] * 1000)
        

    def testFileWriteLines_Tuple(self):
        self.assertFileWriteLines(tuple([bz2_test_str] * 1000))
        

class HashlibTest(ModuleTestCase('_hashlib')):

    def testTrivial(self):
        self.assertRuns(dedent("""
            assert _hashlib.openssl_md5('foobarbaz').digest() == u'm\xf2=\xc0?\x9bT\xcc8\xa0\xfc\x14\x83\xdfn!'
            """))


class PyFileTest(FunctionalTestCase):
    
    def testPyFile(self):
        # this is the CPython file type, interpreted just like an extension type
        mapper = PythonMapper(DLL_PATH)
        try:
            f1 = mapper.CPyFileClass(os.path.join(self.testDir, 'newFile'), 'w')
            f1.write("hello!")
            f1.close()
            
            f2 = mapper.CPyFileClass(os.path.join(self.testDir, 'newFile'), 'r')
            assert f2.read() == 'hello!'
            f2.close()
        finally:
            mapper.Dispose()

# TODO: crashes test run
# Sqlite3Test = TrivialModuleTestCase('sqlite3') # test PATH manipulation in LoadModule
PySVNTest = TrivialModuleTestCase('pysvn') # test misleading names passed to Py_InitModule4
MMapTest = TrivialModuleTestCase('mmap')
CsvTest = TrivialModuleTestCase('csv')

suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)


