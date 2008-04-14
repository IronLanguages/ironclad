
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes, OffsetPtr

import os
import tempfile

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import Python25Mapper
from Ironclad.Structs import PyStringObject, PyTypeObject
from IronPython.Hosting import PythonEngine

from Unmanaged.msvcrt import fclose, fread, fwrite


READ_ARGS = (os.path.join('tests', 'data', 'text.txt'), 'r')
TEST_TEXT = """\
text text text
more text
"""


class Python25Mapper_PyFile_Type_Test(unittest.TestCase):

    def testPyFile_Type(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyFile_Type", typeBlock)
            self.assertEquals(mapper.PyFile_Type, typeBlock, "type address not stored")
            self.assertEquals(mapper.Retrieve(typeBlock), file, "type not mapped")
        finally:
            Marshal.FreeHGlobal(typeBlock)
    
    
    def testCallPyFile_Type(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        try:
            argsPtr = mapper.Store(READ_ARGS)
            filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
            try:
                f = mapper.Retrieve(filePtr)
                self.assertEquals(f.read(), TEST_TEXT, "didn't get a real file")
            finally:
                mapper.DecRef(argsPtr)
                mapper.DecRef(filePtr)
                f.close()
        finally:
            deallocTypes()
    
    
    def testPyFile_AsFile(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        try:
            buflen = len(TEST_TEXT) + 10
            buf = Marshal.AllocHGlobal(buflen)
            argsPtr = mapper.Store(READ_ARGS)
            filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
            try:
                f = mapper.PyFile_AsFile(filePtr)
                try:
                    self.assertEquals(fread(buf, 1, buflen, f), len(TEST_TEXT), "didn't get a real FILE")
                    ptr = buf
                    for c in TEST_TEXT:
                        self.assertEquals(Marshal.ReadByte(ptr), ord(c), "got bad data from FILE")
                        ptr = OffsetPtr(ptr, 1)
                finally:
                    fclose(f)
            finally:
                Marshal.FreeHGlobal(buf)
                mapper.DecRef(argsPtr)
                mapper.DecRef(filePtr)
        finally:
            deallocTypes()


    def testPyFile_AsFile_Write(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        
        testDir = tempfile.mkdtemp()
        path = os.path.join(testDir, "test")
        write_args = (path, 'w')
        argsPtr = mapper.Store(write_args)
        
        try:
            testStr = "meh, string data"
            testLength = len(testStr)
            testStrPtr = mapper.Store(testStr)
            testDataPtr = OffsetPtr(testStrPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))
            
            filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
            try:
                f = mapper.PyFile_AsFile(filePtr)
                try:
                    self.assertEquals(fwrite(testDataPtr, 1, testLength, f), testLength, "didn't work")
                finally:
                    fclose(f)
            finally:
                mapper.DecRef(filePtr)
        finally:
            mapper.DecRef(argsPtr)
            deallocTypes()

        mgdF = open(path)
        try:
            self.assertEquals(mgdF.read(), testStr, "failed to write")
        finally:
            mgdF.close()


suite = makesuite(
    Python25Mapper_PyFile_Type_Test,
)

if __name__ == '__main__':
    run(suite)