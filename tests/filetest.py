
from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase, WithMapper

import os
import shutil
import tempfile

from System import IntPtr
from System.IO import FileStream
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, Python25Api, Python25Mapper, Unmanaged
from Ironclad.Structs import PyFileObject, PyObject, PyStringObject, PyTypeObject

from TestUtils.Unmanaged import fflush, fread, fwrite


READ_ARGS = (os.path.join('tests', 'data', 'text.txt'), 'r')
TEST_TEXT = """\
text text text
more text
"""


class PyFile_Type_Test(TestCase):

    @WithMapper
    def testPyFile_Type(self, mapper, addToCleanUp):
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(typeBlock))
        
        mapper.SetData("PyFile_Type", typeBlock)
        self.assertEquals(mapper.PyFile_Type, typeBlock, "type address not stored")
        self.assertEquals(mapper.Retrieve(typeBlock), file, "type not mapped")
        
        # no explicit test that PyFile_Type was not overwritten -- although it should indeed not be
    
    
    @WithMapper
    def testStoreIPyFile(self, mapper, _):
        f = open(*READ_ARGS)
        fPtr = mapper.Store(f)
        self.assertEquals(CPyMarshal.ReadPtrField(fPtr, PyObject, 'ob_type'), mapper.PyFile_Type)
        self.assertEquals(CPyMarshal.ReadIntField(fPtr, PyObject, 'ob_refcnt'), 1)
        self.assertEquals(CPyMarshal.ReadIntField(fPtr, PyFileObject, 'f_fp'), -2)
    
    
    @WithMapper
    def testOpenAsIfFromUnmanaged(self, mapper, addToCleanUp):
        self.fail('next steps: (1) make cpy calls create cpy files; (2) interpret cpy file type and store it in ironclad')
        
        argsPtr = mapper.Store(READ_ARGS)
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        addToCleanUp(deallocTypes)
        
        for kallable in (mapper.PyFile_Type, mapper.Store(open)):
            filePtr = mapper.PyObject_Call(kallable, argsPtr, kwargsPtr)
            self.assertEquals(CPyMarshal.ReadPtrField(filePtr, PyObject, 'ob_type'), mapper.PyFile_Type)
            f = mapper.Retrieve(filePtr)
            
            self.assertFalse(type(f) is file, "we don't want ipy files used in c code")
            self.assertFalse(CPyMarshal.ReadIntField(filePtr, PyFileObject, 'f_fp') in (0, -2), "shouldn't be either closed or magic")
            self.assertEquals(f.read(), TEST_TEXT, "didn't get a sufficiently real file")
            f.close()
            self.assertEquals(CPyMarshal.ReadIntField(filePtr, PyFileObject, 'f_fp'), 0, "didn't close")
            mapper.DecRef(filePtr)
        


    @WithMapper
    def testConvertPyFileToDescriptor(self, mapper, _):
        testDir = tempfile.mkdtemp()
        outFile = os.path.join(testDir, "test")
        pyFile = file(outFile, 'w')
        pyFile.write("I love streams ")
        pyFile.flush()

        fd = mapper.ConvertPyFileToDescriptor(pyFile)
        FILE = Unmanaged._fdopen(fd, "w")

        testStr = "and file descriptors!"
        testStrPtr = mapper.Store(testStr)
        testDataPtr = OffsetPtr(testStrPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))
        
        self.assertTrue(fwrite(testDataPtr, 1, len(testStr), FILE) > 0, "writing failed")
        fflush(FILE)
        pyFile.close()
        
        stream = file(outFile, 'r')
        output = stream.read()
        stream.close()
        self.assertEquals(output, "I love streams and file descriptors!")


class PyFileAPIFunctions(TestCase):

    @WithMapper
    def testIC_PyFile_AsFile(self, mapper, addToCleanUp):
        buflen = len(TEST_TEXT) + 10
        buf = Marshal.AllocHGlobal(buflen)
        
        filePtr = mapper.Store(open(*READ_ARGS))
        
        f = mapper.IC_PyFile_AsFile(filePtr)
        self.assertEquals(fread(buf, 1, buflen, f), len(TEST_TEXT), "didn't get a real FILE")
        ptr = buf
        for c in TEST_TEXT:
            self.assertEquals(Marshal.ReadByte(ptr), ord(c), "got bad data from FILE")
            ptr = OffsetPtr(ptr, 1)

        Marshal.FreeHGlobal(buf)


    @WithMapper
    def testPyFile_AsFile_Write(self, mapper, addToCleanUp):
        testDir = tempfile.mkdtemp()
        addToCleanUp(lambda: shutil.rmtree(testDir))
        path = os.path.join(testDir, "test")
        
        testStr = "meh, string data"
        testLength = len(testStr)
        testStrPtr = mapper.Store(testStr)
        testDataPtr = OffsetPtr(testStrPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))
        
        filePtr = mapper.Store(open(path, 'w'))
        
        f = mapper.IC_PyFile_AsFile(filePtr)
        self.assertEquals(fwrite(testDataPtr, 1, testLength, f), testLength, "didn't work")
        
        # nasty test: patch out PyObject_Free
        # the memory will not be deallocated, but the FILE handle should be
        
        calls = []
        def Free(ptr):
            calls.append(ptr)
        
        freeDgt = dgt_void_ptr(Free)
        CPyMarshal.WriteFunctionPtrField(mapper.PyFile_Type, PyTypeObject, 'tp_free', freeDgt)
        
        mapper.DecRef(filePtr)
        self.assertEquals(calls, [filePtr], 'failed to call tp_free function')
        
        mgdF = open(path)
        result = mgdF.read()
        self.assertEquals(result, testStr, "failed to write (got >>%s<<) -- deallocing filePtr did not close FILE" % result)
        mgdF.close()


    @WithMapper
    def testPyFile_AsFile_Exhaustion(self, mapper, _):
        argsPtr = mapper.Store(READ_ARGS)
        kwargsPtr = IntPtr.Zero
        
        buflen = len(TEST_TEXT) + 10
        buf = Marshal.AllocHGlobal(buflen)
        
        for _ in range(1000):
            filePtr = mapper.Store(open(*READ_ARGS))
            FILE = mapper.IC_PyFile_AsFile(filePtr)
            self.assertNotEquals(FILE, IntPtr.Zero, "exhausted")
            mapper.Retrieve(filePtr).close()
            # note: we don't call fclose until the file is destroyed, rather than closed
            # we don't *think* this will be a problem in normal use
            mapper.DecRef(filePtr)


    @WithMapper
    def testPyFileFunctionErrors(self, mapper, _):
        ptr = mapper.Store(object())
        self.assertEquals(mapper.IC_PyFile_AsFile(ptr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


suite = makesuite(
    PyFile_Type_Test,
    PyFileAPIFunctions,
)

if __name__ == '__main__':
    run(suite)
