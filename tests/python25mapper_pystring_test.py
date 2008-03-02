
import unittest
from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.runtest import makesuite, run

from System import Array, Byte, Char, IntPtr, OutOfMemoryException
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyStringObject, PyTypeObject
from IronPython.Hosting import PythonEngine


class PyString_TestCase(unittest.TestCase):

    def byteArrayFromString(self, testString):
        testLength = len(testString)
        chars = testString.ToCharArray()
        return Array.ConvertAll[Char, Byte](chars, lambda c: ord(c))


    def ptrFromByteArray(self, bytes):
        testData = Marshal.AllocHGlobal(bytes.Length + 1)
        Marshal.Copy(bytes, 0, testData, bytes.Length)
        Marshal.WriteByte(OffsetPtr(testData, bytes.Length), 0)
        return testData


    def dataPtrFromStrPtr(self, strPtr):
        return OffsetPtr(strPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))


    def fillStringDataWithBytes(self, strPtr, bytes):
        strDataPtr = self.dataPtrFromStrPtr(strPtr)
        Marshal.Copy(bytes, 0, strDataPtr, len(bytes))


    def getStringWithValues(self, start, pastEnd):
        return "".join(chr(c) for c in range(start, pastEnd))


    def assertHasStringType(self, ptr, mapper):
        typePtrPtr = OffsetPtr(ptr, Marshal.OffsetOf(PyStringObject, "ob_type"))
        self.assertEquals(CPyMarshal.ReadPtr(typePtrPtr), mapper.PyString_Type, "bad type")


    def assertStringObjectHasLength(self, strPtr, length):
        stringObject = Marshal.PtrToStructure(strPtr, PyStringObject)
        self.assertEquals(stringObject.ob_refcnt, 1, "unexpected refcount")
        self.assertEquals(stringObject.ob_size, length, "unexpected ob_size")
        self.assertEquals(stringObject.ob_shash, -1, "unexpected useless-field")
        self.assertEquals(stringObject.ob_sstate, 0, "unexpected useless-field")

        strDataPtr = self.dataPtrFromStrPtr(strPtr)
        terminatorPtr = OffsetPtr(strDataPtr, length)
        self.assertEquals(Marshal.ReadByte(terminatorPtr), 0, "string not terminated")


    def assertStringObjectHasDataBytes(self, strPtr, expectedBytes):
        strDataPtr = self.dataPtrFromStrPtr(strPtr)
        testLength = len(expectedBytes)
        writtenBytes = Array.CreateInstance(Byte, testLength)
        Marshal.Copy(strDataPtr, writtenBytes, 0, testLength)

        self.assertEquals(len(writtenBytes), testLength, "copied wrong")
        for (actual, expected) in zip(writtenBytes, expectedBytes):
            self.assertEquals(actual, expected, "failed to copy string data correctly")


class Python25Mapper_PyString_FromString_Test(PyString_TestCase):

    def testCreatesString(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)

        testString = "beset on all sides" + self.getStringWithValues(1, 256)
        bytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(bytes)

        strPtr = mapper.PyString_FromString(testData)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(strPtr, len(bytes) + baseSize)], "allocated wrong")
            self.assertStringObjectHasLength(strPtr, len(bytes))
            self.assertStringObjectHasDataBytes(strPtr, bytes)
            self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to map pointer correctly")
        finally:
            Marshal.FreeHGlobal(testData)
            Marshal.FreeHGlobal(strPtr)
            deallocTypes()


class Python25Mapper_PyString_FromStringAndSize_Test(PyString_TestCase):

    def testCreateEmptyString(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)

        testString = "we run the grease racket in this town" + self.getStringWithValues(0, 256)
        testLength = len(testString)

        strPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, testLength)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
            self.assertStringObjectHasLength(strPtr, testLength)
            self.assertHasStringType(strPtr, mapper)
            testBytes = self.byteArrayFromString(testString)
            self.fillStringDataWithBytes(strPtr, testBytes)

            self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to read string data")
        finally:
            Marshal.FreeHGlobal(strPtr)
            deallocTypes()


    def testCreateStringWithData(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)

        testString = "we also run the shovel racket" + self.getStringWithValues(0, 256)
        testBytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(testBytes)
        testLength = len(testString)

        strPtr = mapper.PyString_FromStringAndSize(testData, testLength)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
            self.assertHasStringType(strPtr, mapper)
            self.assertStringObjectHasLength(strPtr, testLength)
            self.assertStringObjectHasDataBytes(strPtr, testBytes)
            self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to read string data")
        finally:
            Marshal.FreeHGlobal(strPtr)
            deallocTypes()


class Python25Mapper__PyString_Resize_Test(PyString_TestCase):

    def testErrorHandling(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, 365)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, data)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(data, 365 + baseSize)], "allocated wrong")
            self.assertEquals(mapper._PyString_Resize(ptrPtr, 2000000000), -1, "bad return on error")
            self.assertEquals(type(mapper.LastException), OutOfMemoryException, "wrong exception type")
            self.assertTrue(data in frees, "did not deallocate")
        finally:
            if data not in frees:
                Marshal.FreeHGlobal(data)
            Marshal.FreeHGlobal(ptrPtr)
            deallocTypes()


    def testShrink(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)

        oldLength = 365
        newLength = 20

        strPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, oldLength)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, strPtr)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(strPtr, oldLength + baseSize)], "allocated wrong")
            self.assertEquals(mapper._PyString_Resize(ptrPtr, newLength), 0, "bad return on success")
            
            self.assertHasStringType(strPtr, mapper)
            self.assertStringObjectHasLength(strPtr, newLength)

            self.assertEquals(allocs, [(strPtr, oldLength + baseSize)], "unexpected extra alloc")
            self.assertEquals(frees, [], "unexpected frees")
        finally:
            Marshal.FreeHGlobal(strPtr)
            Marshal.FreeHGlobal(ptrPtr)
            deallocTypes()


    def testGrow(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)

        oldLength = 20
        testString = "slings and arrows" + self.getStringWithValues(0, 256)
        newLength = len(testString)

        oldStrPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, oldLength)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, oldStrPtr)
        newStrPtr = IntPtr.Zero
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(oldStrPtr, oldLength + baseSize)], "allocated wrong")
            self.assertEquals(mapper._PyString_Resize(ptrPtr, newLength), 0, "bad return on success")

            newStrPtr = Marshal.ReadIntPtr(ptrPtr)
            expectedAllocs = [(oldStrPtr, oldLength + baseSize), (newStrPtr, newLength + baseSize)]
            self.assertEquals(allocs, expectedAllocs,
                              "allocated wrong")
            self.assertEquals(frees, [oldStrPtr], "did not free unused memory")

            self.assertHasStringType(newStrPtr, mapper)
            self.assertStringObjectHasLength(newStrPtr, newLength)

            testBytes = self.byteArrayFromString(testString)
            self.fillStringDataWithBytes(newStrPtr, testBytes)

            self.assertEquals(mapper.Retrieve(newStrPtr), testString, "failed to read string data")
            self.assertEquals(mapper.RefCount(oldStrPtr), 0, "failed to unmap old string")
        finally:
            if oldStrPtr not in frees:
                Marshal.FreeHGlobal(oldStrPtr)
            Marshal.FreeHGlobal(ptrPtr)
            if newStrPtr != IntPtr.Zero and newStrPtr not in frees:
                Marshal.FreeHGlobal(newStrPtr)
            deallocTypes()

class PyStringStoreTest(PyString_TestCase):
    
    def testStoreStringCreatesStringType(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))

        testString = "fnord" + self.getStringWithValues(1, 256)
        testBytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(testBytes)
        testLength = len(testString)

        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyString_Type", typeBlock)
            strPtr = mapper.Store(testString)
            try:
                baseSize = Marshal.SizeOf(PyStringObject)
                self.assertEquals(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
                self.assertHasStringType(strPtr, mapper)
                self.assertStringObjectHasLength(strPtr, testLength)
                self.assertStringObjectHasDataBytes(strPtr, testBytes)
                self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to read string data")
            finally:
                mapper.DecRef(strPtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)
            


suite = makesuite(
    Python25Mapper_PyString_FromString_Test,
    Python25Mapper_PyString_FromStringAndSize_Test,
    Python25Mapper__PyString_Resize_Test,
    PyStringStoreTest,
)

if __name__ == '__main__':
    run(suite)