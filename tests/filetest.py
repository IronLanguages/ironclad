
from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase

import os
import shutil
import tempfile

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import Python25Mapper
from Ironclad.Structs import PyStringObject, PyTypeObject

from TestUtils.Unmanaged import fclose, fread, fwrite


READ_ARGS = (os.path.join('tests', 'data', 'text.txt'), 'r')
TEST_TEXT = """\
text text text
more text
"""


class PyFile_Type_Test(TestCase):

    def testPyFile_Type(self):
        mapper = Python25Mapper()
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        
        mapper.SetData("PyFile_Type", typeBlock)
        self.assertEquals(mapper.PyFile_Type, typeBlock, "type address not stored")
        self.assertEquals(mapper.Retrieve(typeBlock), file, "type not mapped")
        
        mapper.Dispose()
        Marshal.FreeHGlobal(typeBlock)
    
    
    def testCallPyFile_Type(self):
        mapper = Python25Mapper()
        
        argsPtr = mapper.Store(READ_ARGS)
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        
        filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
        f = mapper.Retrieve(filePtr)
        self.assertEquals(f.read(), TEST_TEXT, "didn't get a real file")

        mapper.Dispose()
        deallocTypes()
    
    
    def testPyFile_AsFile(self):
        mapper = Python25Mapper()
        
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        buflen = len(TEST_TEXT) + 10
        buf = Marshal.AllocHGlobal(buflen)
        argsPtr = mapper.Store(READ_ARGS)
        
        filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
        
        f = mapper.PyFile_AsFile(filePtr)
        self.assertEquals(fread(buf, 1, buflen, f), len(TEST_TEXT), "didn't get a real FILE")
        ptr = buf
        for c in TEST_TEXT:
            self.assertEquals(Marshal.ReadByte(ptr), ord(c), "got bad data from FILE")
            ptr = OffsetPtr(ptr, 1)

        Marshal.FreeHGlobal(buf)
        mapper.Dispose()
        deallocTypes()


    def testPyFile_AsFile_Write(self):
        mapper = Python25Mapper()
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        
        testDir = tempfile.mkdtemp()
        path = os.path.join(testDir, "test")
        write_args = (path, 'w')
        argsPtr = mapper.Store(write_args)
        
        testStr = "meh, string data"
        testLength = len(testStr)
        testStrPtr = mapper.Store(testStr)
        testDataPtr = OffsetPtr(testStrPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))
        
        filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
        f = mapper.PyFile_AsFile(filePtr)
        self.assertEquals(fwrite(testDataPtr, 1, testLength, f), testLength, "didn't work")
        # implicit test that Dispose will close remaining file handles
        mapper.Dispose()
        deallocTypes()

        mgdF = open(path)
        result = mgdF.read()
        self.assertEquals(result, testStr, "failed to write (got >>%s<<)" % result)
        mgdF.close()
        
        shutil.rmtree(testDir)


    def testPyFile_AsFile_Exhaustion(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        argsPtr = mapper.Store(READ_ARGS)
        kwargsPtr = IntPtr.Zero
        
        buflen = len(TEST_TEXT) + 10
        buf = Marshal.AllocHGlobal(buflen)
        
        for _ in range(1000):
            filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
            FILE = mapper.PyFile_AsFile(filePtr)
            self.assertNotEquals(FILE, IntPtr.Zero, "exhausted")
            mapper.Retrieve(filePtr).close()
            # note: we don't call fclose until the file is destroyed, rather than closed
            # we don't *think* this will be a problem in normal use
            mapper.DecRef(filePtr)
        
        mapper.Dispose()
        deallocTypes()
        


suite = makesuite(
    PyFile_Type_Test,
)

if __name__ == '__main__':
    run(suite)