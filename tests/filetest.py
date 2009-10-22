
from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase, WithMapper, WithPatchedStdErr

import os
import shutil
import tempfile

from System import IntPtr
from System.IO import FileStream
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, PythonApi, PythonMapper, Unmanaged
from Ironclad.Structs import PyFileObject, PyObject, PyStringObject, PyTypeObject


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
        self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtrField(fPtr, PyFileObject, 'f_name')), READ_ARGS[0])
        self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtrField(fPtr, PyFileObject, 'f_mode')), READ_ARGS[1])
    
    
    @WithMapper
    def testUnmanagedOpenCreatesCPyFile(self, mapper, addToCleanUp):
        argsPtr = mapper.Store(READ_ARGS)
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        addToCleanUp(deallocTypes)
        
        for kallable in (mapper.PyFile_Type, mapper.Store(open)):
            # ok, it seems these are the same object in ipy.
            # I doubt they always will be, though :-).
            filePtr = mapper.PyObject_Call(kallable, argsPtr, kwargsPtr)
            
            self.assertEquals(CPyMarshal.ReadPtrField(filePtr, PyObject, 'ob_type'), mapper.PyFile_Type)
            ipy_type = type(mapper.Retrieve(filePtr))
            self.assertFalse(ipy_type is file, "we don't want ipy files used in c code")
            self.assertEquals(ipy_type.__name__, "cpy_file")
            
            # note: no direct tests for cpy file type, for 2 reasons:
            #
            # (1) we need to load the stub dll to get the code, and
            #     it feels wrong to do that here; insufficiently unity.
            # (2) this test proves that functionalitytest.py is creating 
            #     cpy files, and functionalitytest.py should prove that 
            #     using those cpy files actually works.
            #


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
        
        self.assertTrue(Unmanaged.fwrite(testDataPtr, 1, len(testStr), FILE) > 0, "writing failed")
        Unmanaged.fflush(FILE)
        pyFile.close()
        
        stream = file(outFile, 'r')
        output = stream.read()
        stream.close()
        self.assertEquals(output, "I love streams and file descriptors!")


class PyFileAPIFunctions(TestCase):

    @WithMapper
    @WithPatchedStdErr
    def testIC_PyFile_AsFile(self, mapper, addToCleanUp, stderr_writes):
        buflen = len(TEST_TEXT) + 10
        buf = Marshal.AllocHGlobal(buflen)
        
        filePtr = mapper.Store(open(*READ_ARGS))
        
        f = mapper.IC_PyFile_AsFile(filePtr)
        self.assertEquals(stderr_writes, [('Warning: creating unmanaged FILE* from managed stream. Please use ironclad.open with this extension.',), ('\n',)])
        self.assertEquals(Unmanaged.fread(buf, 1, buflen, f), len(TEST_TEXT), "didn't get a real FILE")
        ptr = buf
        for c in TEST_TEXT:
            self.assertEquals(Marshal.ReadByte(ptr), ord(c), "got bad data from FILE")
            ptr = OffsetPtr(ptr, 1)

        Marshal.FreeHGlobal(buf)


    @WithMapper
    @WithPatchedStdErr
    def testIC_PyFile_AsFile_Write(self, mapper, addToCleanUp, _):
        testDir = tempfile.mkdtemp()
        addToCleanUp(lambda: shutil.rmtree(testDir))
        path = os.path.join(testDir, "test")
        
        testStr = "meh, string data"
        testLength = len(testStr)
        testStrPtr = mapper.Store(testStr)
        testDataPtr = OffsetPtr(testStrPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))
        
        filePtr = mapper.Store(open(path, 'w'))
        
        f = mapper.IC_PyFile_AsFile(filePtr)
        self.assertEquals(Unmanaged.fwrite(testDataPtr, 1, testLength, f), testLength, "didn't work")
        
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
    @WithPatchedStdErr
    def testIC_PyFile_AsFile_Exhaustion(self, mapper, _, __):
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
    @WithPatchedStdErr
    def testPyFileFunctionErrors(self, mapper, _, __):
        ptr = mapper.Store(object())
        self.assertEquals(mapper.IC_PyFile_AsFile(ptr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testIC_PyFile_WriteString(self, mapper, addToCleanUp):
        testDir = tempfile.mkdtemp()
        addToCleanUp(lambda: shutil.rmtree(testDir))
        path = os.path.join(testDir, "test")
        
        testStr = "meh, more string data"
        
        f = open(path, 'w')
        try:
            fPtr = mapper.Store(f)
            # note: don't pass a ptr, trust that magical string-marshalling works
            self.assertEquals(mapper.IC_PyFile_WriteString(testStr, fPtr), 0)
            mapper.DecRef(fPtr)
            self.assertEquals(mapper.IC_PyFile_WriteString(testStr, mapper.Store(object())), -1)
            self.assertMapperHasError(mapper, TypeError)
        finally:
            f.close()
        
        f = open(path)
        try:
            result = f.read()
            self.assertEquals(result, testStr)
        finally:
            f.close()


    @WithMapper
    def testIC_PyFile_WriteObject(self, mapper, addToCleanUp):
        testDir = tempfile.mkdtemp()
        addToCleanUp(lambda: shutil.rmtree(testDir))
        path = os.path.join(testDir, "test")
        
        class C(object):
            __str__ = lambda s: 'str'
            __repr__ = lambda s: 'repr'
        
        f = open(path, 'w')
        try:
            fPtr = mapper.Store(f)
            cPtr = mapper.Store(C())
            self.assertEquals(mapper.IC_PyFile_WriteObject(cPtr, fPtr, 0), 0)
            self.assertEquals(mapper.IC_PyFile_WriteObject(cPtr, fPtr, 1), 0)
            mapper.DecRef(fPtr)
            self.assertEquals(mapper.IC_PyFile_WriteObject(cPtr, mapper.Store(object()), 0), -1)
            self.assertMapperHasError(mapper, TypeError)
        finally:
            f.close()
        
        f = open(path)
        try:
            result = f.read()
            self.assertEquals(result, 'reprstr')
        finally:
            f.close()
        


suite = makesuite(
    PyFile_Type_Test,
    PyFileAPIFunctions,
)

if __name__ == '__main__':
    run(suite)
