
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import Array, Byte, Char, IntPtr, OutOfMemoryException
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyStringObject, PyTypeObject


class PyString_TestCase(TestCase):

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
        self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyStringObject, "ob_type"), mapper.PyString_Type, "bad type")


    def assertStringObjectHasLength(self, strPtr, length):
        stringObject = Marshal.PtrToStructure(strPtr, PyStringObject)
        self.assertEquals(stringObject.ob_refcnt, 1, "unexpected refcount")
        self.assertEquals(stringObject.ob_size, length, "unexpected ob_size")
        self.assertEquals(stringObject.ob_shash, -1, "unexpected currently-useless-field")
        self.assertEquals(stringObject.ob_sstate, 0, "unexpected currently-useless-field")

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


class PyString_Type_test(TypeTestCase):
    
    def testString_tp_free(self):
        self.assertUsual_tp_free("PyString_Type")
    
    def testString_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyString_Type")


class PyString_FromString_Test(PyString_TestCase):

    def testCreatesString(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        testString = "beset on all sides" + self.getStringWithValues(1, 256)
        bytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(bytes)

        strPtr = mapper.PyString_FromString(testData)
        baseSize = Marshal.SizeOf(PyStringObject)
        self.assertEquals(allocs, [(strPtr, len(bytes) + baseSize)], "allocated wrong")
        self.assertStringObjectHasLength(strPtr, len(bytes))
        self.assertStringObjectHasDataBytes(strPtr, bytes)
        self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to map pointer correctly")
            
        mapper.Dispose()
        Marshal.FreeHGlobal(testData)
        deallocTypes()


class InternTest(PyString_TestCase):
        
    @WithMapper
    def testInternExisting(self, mapper, addToCleanUp):
        testString = "mars needs women" + self.getStringWithValues(1, 256)
        bytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(bytes)
        
        sp1 = mapper.PyString_FromString(testData)
        addToCleanUp(lambda: Marshal.FreeHGlobal(sp1p))

        sp2 = mapper.PyString_InternFromString(testData)
        addToCleanUp(lambda: Marshal.FreeHGlobal(testData))

        self.assertNotEquals(sp1, sp2)
        self.assertFalse(mapper.Retrieve(sp1) is mapper.Retrieve(sp2))
        self.assertEquals(mapper.RefCount(sp1), 1)
        self.assertEquals(mapper.RefCount(sp2), 2, 'failed to grab extra reference to induce immortality')
        
        mapper.IncRef(sp1)
        sp1p = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        CPyMarshal.WritePtr(sp1p, sp1)
        mapper.PyString_InternInPlace(sp1p)
        sp1i = CPyMarshal.ReadPtr(sp1p)
        self.assertEquals(sp1i, sp2, 'failed to intern')
        self.assertTrue(mapper.Retrieve(sp1i) is mapper.Retrieve(sp2))
        self.assertEquals(mapper.RefCount(sp1), 1, 'failed to decref old string')
        self.assertEquals(mapper.RefCount(sp2), 3, 'failed to incref interned string')



class PyString_FromStringAndSize_Test(PyString_TestCase):

    def testCreateEmptyString(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        testString = "we run the grease racket in this town" + self.getStringWithValues(0, 256)
        testLength = len(testString)

        strPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, testLength)
        baseSize = Marshal.SizeOf(PyStringObject)
        self.assertEquals(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
        self.assertStringObjectHasLength(strPtr, testLength)
        self.assertHasStringType(strPtr, mapper)
        testBytes = self.byteArrayFromString(testString)
        self.fillStringDataWithBytes(strPtr, testBytes)

        resultStr = mapper.Retrieve(strPtr)
        self.assertEquals(resultStr, testString, "failed to read string data")
        
        strPtr2 = mapper.Store(resultStr)
        self.assertEquals(strPtr2, strPtr, "did not remember already had this string")
        self.assertEquals(mapper.RefCount(strPtr), 2, "did not incref on store")
            
        mapper.Dispose()
        deallocTypes()


    def testCreateStringWithData(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        testString = "we also run the shovel racket" + self.getStringWithValues(0, 256)
        testBytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(testBytes)
        testLength = len(testString)

        strPtr = mapper.PyString_FromStringAndSize(testData, testLength)
        baseSize = Marshal.SizeOf(PyStringObject)
        self.assertEquals(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
        self.assertHasStringType(strPtr, mapper)
        self.assertStringObjectHasLength(strPtr, testLength)
        self.assertStringObjectHasDataBytes(strPtr, testBytes)
        self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to read string data")
            
        mapper.Dispose()
        deallocTypes()


class _PyString_Resize_Test(PyString_TestCase):

    def testErrorHandling(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, 365)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, data)
        baseSize = Marshal.SizeOf(PyStringObject)
        self.assertEquals(allocs, [(data, 365 + baseSize)], "allocated wrong")
        self.assertEquals(mapper._PyString_Resize(ptrPtr, 2000000000), -1, "bad return on error")
        self.assertEquals(type(mapper.LastException), OutOfMemoryException, "wrong exception type")
        self.assertTrue(data in frees, "did not deallocate")    
        
        mapper.Dispose()
        Marshal.FreeHGlobal(ptrPtr)
        deallocTypes()


    def testShrink(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        oldLength = 365
        newLength = 20

        strPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, oldLength)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, strPtr)
        
        baseSize = Marshal.SizeOf(PyStringObject)
        self.assertEquals(allocs, [(strPtr, oldLength + baseSize)], "allocated wrong")
        self.assertEquals(mapper._PyString_Resize(ptrPtr, newLength), 0, "bad return on success")
        
        self.assertHasStringType(strPtr, mapper)
        self.assertStringObjectHasLength(strPtr, newLength)

        self.assertEquals(allocs, [(strPtr, oldLength + baseSize)], "unexpected extra alloc")
        self.assertEquals(frees, [], "unexpected frees")
            
        mapper.Dispose()
        Marshal.FreeHGlobal(ptrPtr)
        deallocTypes()


    def testGrow(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        oldLength = 20
        testString = "slings and arrows" + self.getStringWithValues(0, 256)
        newLength = len(testString)

        oldStrPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, oldLength)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, oldStrPtr)
        newStrPtr = IntPtr.Zero
        
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
        if oldStrPtr != newStrPtr:
            # this would otherwise fail (very, very rarely)
            self.assertEquals(oldStrPtr in frees, True)
            
        mapper.Dispose()
        Marshal.FreeHGlobal(ptrPtr)
        deallocTypes()
            

class PyString_Size_Test(PyString_TestCase):
    
    @WithMapper
    def testWorks(self, mapper, _):
        testString = "Oh, sure, Lisa -- some wonderful, magical animal." + self.getStringWithValues(0, 256)
        testLength = len(testString)
        
        strPtr = mapper.Store(testString)
        self.assertEquals(mapper.PyString_Size(strPtr), testLength)


class PyString_AsStringTest(TestCase):
    
    @WithMapper
    def testWorks(self, mapper, _):
        strPtr = mapper.Store("You're fighting a business hippy. This is a hippy that understands the law of supply and demand.")
        strData = CPyMarshal.Offset(strPtr, Marshal.OffsetOf(PyStringObject, 'ob_sval'))
        self.assertEquals(mapper.PyString_AsString(strPtr), strData)
        
        notstrPtr = mapper.Store(object())
        self.assertEquals(mapper.PyString_AsString(notstrPtr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


class PyStringStoreTest(PyString_TestCase):
    
    def testStoreStringCreatesStringType(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        testString = "fnord" + self.getStringWithValues(1, 256)
        testBytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(testBytes)
        testLength = len(testString)

        strPtr = mapper.Store(testString)
        baseSize = Marshal.SizeOf(PyStringObject)
        
        self.assertEquals(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
        self.assertHasStringType(strPtr, mapper)
        self.assertStringObjectHasLength(strPtr, testLength)
        self.assertStringObjectHasDataBytes(strPtr, testBytes)
        self.assertEquals(mapper.Retrieve(strPtr), testString, "failed to read string data")
        
        strPtr2 = mapper.Store(testString)
        self.assertEquals(strPtr2, strPtr, "did not remember already had this string")
        self.assertEquals(mapper.RefCount(strPtr), 2, "did not incref on store")
            
        mapper.Dispose()
        deallocTypes()



suite = makesuite(
    PyString_Type_test,
    PyString_FromString_Test,
    InternTest,
    PyString_FromStringAndSize_Test,
    _PyString_Resize_Test,
    PyString_Size_Test,
    PyString_AsStringTest,
    PyStringStoreTest,
)

if __name__ == '__main__':
    run(suite)
