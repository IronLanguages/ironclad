
import os
import shutil
import tempfile
from textwrap import dedent
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from Ironclad import Python25Mapper

from TestUtils import ExecUtils


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


class FunctionalityTest(TestCase):

    def assertWorksWithModule(self, path, name, testCode):
        mapper = Python25Mapper(os.path.join("build", "python25.dll"))
        try:
            try:
                mapper.LoadModule(path)
                ExecUtils.Exec(mapper.Engine, "import %s\n%s" % (name, testCode))
            except Exception, e:
                print "BOOM!"
                print e
                print e.clsException.StackTrace
                raise
        finally:
            mapper.Dispose()
        


    def assertWorksWithBZ2(self, testCode):
        self.assertWorksWithModule("C:\\Python25\\Dlls\\bz2.pyd", "bz2", testCode)


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
        

    def testBZ2FileRead(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertWorksWithBZ2(dedent("""
            f = bz2.BZ2File(%r)
            try:
                assert f.read() == %r
            finally:
                f.close()
            """) % (testPath, bz2_test_text)
        )

    def testBZ2FileReadLine(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertWorksWithBZ2(dedent("""
            f = bz2.BZ2File(%r)
            try:
                assert f.readline() == %r
                assert f.readline() == ''
            finally:
                f.close()
            """) % (testPath, bz2_test_text)
        )


    def testBZ2FileReadLines_Short(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertWorksWithBZ2(dedent("""
            f = bz2.BZ2File(%r)
            try:
                lines = f.readlines()
                assert len(lines) == 1000
                assert ''.join(lines) == %r
            finally:
                f.close()
            """) % (testPath, bz2_test_text_lines)
        )


    def testBZ2FileReadLines_Long(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertWorksWithBZ2(dedent("""
            f = bz2.BZ2File(%r)
            try:
                lines = f.readlines()
                assert lines == [%r]
            finally:
                f.close()
            """) % (testPath, bz2_test_text)
        )


    def testIterateBZ2File(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertWorksWithBZ2(dedent("""
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
            """) % (testPath, bz2_test_line)
        )

    
    def testBZ2FileSeekTell(self):
        testPath = os.path.join("tests", "data", "bz2", "compressed.bz2")
        self.assertWorksWithBZ2(dedent("""
            def assertSeeksTo(seekargs, expectedPosition):
                f.seek(*seekargs)
                assert f.tell() == expectedPosition
                assert f.read() == %r[expectedPosition:]
                f.seek(expectedPosition)
                
            f = bz2.BZ2File(%r)
            try:
                assertSeeksTo((55000,), 55000)
                assertSeeksTo((0,), 0)
                assertSeeksTo((12345, 0), 12345)
                assertSeeksTo((10000, 1), 22345)
                assertSeeksTo((-10000, 1), 12345)
                assertSeeksTo((-55000, 2), 0)
            finally:
                f.close()
            """) % (bz2_test_text, testPath)
        )
        

    def testBZ2FileWrite(self):
        # read is tested separately elsewhere, so we assume it works
        testDir = tempfile.mkdtemp()
        path = os.path.join(testDir, "test.bz2")
        self.assertWorksWithBZ2(dedent("""
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
            """) % (path, bz2_test_text, path, bz2_test_text)
        )
        shutil.rmtree(testDir)


    def testBZ2HeavyUse(self):
        self.assertWorksWithBZ2(dedent("""
            COUNT = 150
            compressors = [bz2.BZ2Compressor() for _ in range(COUNT)]
            decompressors = [bz2.BZ2Decompressor() for _ in range(COUNT)]
            
            current = %r
            for i in range(COUNT):
                current = decompressors[-i].decompress(
                    compressors[i].compress(current[:i * 40]) + 
                    compressors[i].compress(current[i * 40:]) + 
                    compressors[i].flush())
            
            assert current == %r
            """) % (bz2_test_text, bz2_test_text)
        )    
    
    
    def testBZ2FileProperties(self):
        testPath = os.path.join("tests", "data", "bz2", "compressedlines.bz2")
        self.assertWorksWithBZ2(dedent("""
            f = bz2.BZ2File(%r, 'U')
            try:
                # assert f.mode == 'r' # IP2 bug -- no file.mode
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
            """) % (testPath, testPath)
        )
        
        
    def assertBZ2FileWriteLines(self, sequence):
        # read is tested separately elsewhere, so we assume it works
        testDir = tempfile.mkdtemp()
        path = os.path.join(testDir, "test.bz2")
        self.assertWorksWithBZ2(dedent("""
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
            """) % (path, sequence, path, bz2_test_text)
        )
        shutil.rmtree(testDir)
        

    def testBZ2FileWriteLines_List(self):
        self.assertBZ2FileWriteLines([bz2_test_str] * 1000)
        

    def testBZ2FileWriteLines_Tuple(self):
        self.assertBZ2FileWriteLines(tuple([bz2_test_str] * 1000))


    def assertWorksWithMultiarray(self, testCode):
        self.assertWorksWithModule("C:\\Python25\\Lib\\site-packages\\numpy\\core\\multiarray.pyd", "multiarray", testCode)


    def testCanImportMultiarray(self):
        self.assertWorksWithMultiarray(dedent("""
            dir(multiarray)
            """)
        )



suite = makesuite(FunctionalityTest)

if __name__ == '__main__':
    run(suite)

