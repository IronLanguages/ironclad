
from tests.utils.runtest import automakesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import Array, Byte, Char, IntPtr, UInt32
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, dgt_int_ptrintptr, dgt_int_ptrptr, dgt_ptr_ptrptr, PythonMapper
from Ironclad.Structs import PyStringObject, PyTypeObject, PyBufferProcs, PySequenceMethods, Py_TPFLAGS


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


class PyString_Type_Test(TypeTestCase):
    
    def testString_tp_free(self):
        self.assertUsual_tp_free("PyString_Type")
    
    def testString_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyString_Type")


    @WithMapper
    def testFlags(self, mapper, _):
        flags = CPyMarshal.ReadUIntField(mapper.PyString_Type, PyTypeObject, "tp_flags")
        self.assertEquals(flags & UInt32(Py_TPFLAGS.HAVE_GETCHARBUFFER), UInt32(Py_TPFLAGS.HAVE_GETCHARBUFFER))
        

    @WithMapper
    def testSizes(self, mapper, _):
        tp_basicsize = CPyMarshal.ReadIntField(mapper.PyString_Type, PyTypeObject, 'tp_basicsize')
        self.assertNotEquals(tp_basicsize, 0)
        tp_itemsize = CPyMarshal.ReadIntField(mapper.PyString_Type, PyTypeObject, 'tp_itemsize')
        self.assertNotEquals(tp_itemsize, 0)


    @WithMapper
    def testStringifiers(self, mapper, _):
        IC_PyString_Str = mapper.GetAddress("IC_PyString_Str")
        tp_str = CPyMarshal.ReadPtrField(mapper.PyString_Type, PyTypeObject, "tp_str")
        self.assertEquals(tp_str, IC_PyString_Str)
        
        PyObject_Repr = mapper.GetAddress("PyObject_Repr")
        tp_repr = CPyMarshal.ReadPtrField(mapper.PyString_Type, PyTypeObject, "tp_repr")
        self.assertEquals(tp_repr, PyObject_Repr)


    @WithMapper
    def testSequenceProtocol(self, mapper, _):
        strPtr = mapper.PyString_Type
        
        seqPtr = CPyMarshal.ReadPtrField(strPtr, PyTypeObject, 'tp_as_sequence')
        self.assertNotEquals(seqPtr, IntPtr.Zero)
        concatPtr = CPyMarshal.ReadPtrField(seqPtr, PySequenceMethods, 'sq_concat')
        # concat_core tested further down
        self.assertEquals(concatPtr, mapper.GetAddress('IC_PyString_Concat_Core'))
        
        
    @WithMapper
    def testBufferProtocol(self, mapper, later):
        # should all be implemented in C really, but weaving cpy string type into
        # our code feels too much like hard work for now
        strPtr = mapper.PyString_Type
        
        bufPtr = CPyMarshal.ReadPtrField(strPtr, PyTypeObject, 'tp_as_buffer')
        self.assertNotEquals(bufPtr, IntPtr.Zero)
        getreadbuffer = CPyMarshal.ReadFunctionPtrField(bufPtr, PyBufferProcs, 'bf_getreadbuffer', dgt_int_ptrintptr)
        getwritebuffer = CPyMarshal.ReadFunctionPtrField(bufPtr, PyBufferProcs, 'bf_getwritebuffer', dgt_int_ptrintptr)
        getcharbuffer = CPyMarshal.ReadFunctionPtrField(bufPtr, PyBufferProcs, 'bf_getcharbuffer', dgt_int_ptrintptr)
        getsegcount = CPyMarshal.ReadFunctionPtrField(bufPtr, PyBufferProcs, 'bf_getsegcount', dgt_int_ptrptr)
        
        ptrptr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        later(lambda: Marshal.FreeHGlobal(ptrptr))
        
        strptr = mapper.Store("hullo")
        for getter in (getreadbuffer, getcharbuffer):
            self.assertEquals(getter(strptr, 0, ptrptr), 5)
            self.assertEquals(CPyMarshal.ReadPtr(ptrptr), CPyMarshal.GetField(strptr, PyStringObject, 'ob_sval'))
            self.assertEquals(getter(strptr, 1, ptrptr), -1)
            self.assertMapperHasError(mapper, SystemError)
        
        self.assertEquals(getwritebuffer(strptr, 0, ptrptr), -1)
        self.assertMapperHasError(mapper, SystemError)
        
        self.assertEquals(getsegcount(strptr, ptrptr), 1)
        self.assertEquals(CPyMarshal.ReadInt(ptrptr), 5)
        self.assertEquals(getsegcount(strptr, IntPtr.Zero), 1)
        



class PyString_FromString_Test(PyString_TestCase):

    def testCreatesString(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
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


class PyString_Concat_Test(PyString_TestCase):

    @WithMapper
    def testBasic(self, mapper, addToCleanup):
        part1Ptr = mapper.Store("one two")
        mapper.IncRef(part1Ptr) # avoid garbage collection
        part2Ptr = mapper.Store(" three")
        startingRefCnt = mapper.RefCount(part1Ptr)
        
        stringPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        addToCleanup(lambda: Marshal.FreeHGlobal(stringPtrPtr))
        
        Marshal.WriteIntPtr(stringPtrPtr, part1Ptr)
        mapper.PyString_Concat(stringPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, None)
        

        newStringPtr = Marshal.ReadIntPtr(stringPtrPtr)
        self.assertEquals(mapper.Retrieve(newStringPtr), "one two three")

        self.assertEquals(startingRefCnt - mapper.RefCount(part1Ptr), 1)


    @WithMapper
    def testErrorCaseSecondArg(self, mapper, addToCleanup):
        part1Ptr = mapper.Store("one two")
        mapper.IncRef(part1Ptr) # avoid garbage collection
        startingRefCnt = mapper.RefCount(part1Ptr)
        
        part2Ptr = mapper.Store(3)
        stringPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        addToCleanup(lambda: Marshal.FreeHGlobal(stringPtrPtr))
        
        Marshal.WriteIntPtr(stringPtrPtr, part1Ptr)
        mapper.PyString_Concat(stringPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, TypeError)

        self.assertEquals(Marshal.ReadIntPtr(stringPtrPtr), IntPtr(0))
        self.assertEquals(startingRefCnt - mapper.RefCount(part1Ptr), 1)


    @WithMapper
    def testErrorCaseSecondArg(self, mapper, addToCleanup):
        part1Ptr = mapper.Store(17)
        mapper.IncRef(part1Ptr) # avoid garbage collection
        startingRefCnt = mapper.RefCount(part1Ptr)

        part2Ptr = mapper.Store("three")
        stringPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        addToCleanup(lambda: Marshal.FreeHGlobal(stringPtrPtr))
        
        Marshal.WriteIntPtr(stringPtrPtr, part1Ptr)
        mapper.PyString_Concat(stringPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, TypeError)

        self.assertEquals(Marshal.ReadIntPtr(stringPtrPtr), IntPtr(0))
        self.assertEquals(startingRefCnt - mapper.RefCount(part1Ptr), 1)


class PyString_ConcatAndDel_Test(PyString_TestCase):

    @WithMapper
    def testBasic(self, mapper, addToCleanup):
        part1Ptr = mapper.Store("one two")
        mapper.IncRef(part1Ptr) # avoid garbage collection
        startingPart1RefCnt = mapper.RefCount(part1Ptr)
        
        part2Ptr = mapper.Store(" three")
        mapper.IncRef(part2Ptr) # avoid garbage collection
        startingPart2RefCnt = mapper.RefCount(part2Ptr)

        stringPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        addToCleanup(lambda: Marshal.FreeHGlobal(stringPtrPtr))
        
        Marshal.WriteIntPtr(stringPtrPtr, part1Ptr)
        mapper.PyString_ConcatAndDel(stringPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, None)

        newStringPtr = Marshal.ReadIntPtr(stringPtrPtr)
        self.assertEquals(mapper.Retrieve(newStringPtr), "one two three")

        self.assertEquals(startingPart1RefCnt - mapper.RefCount(part1Ptr), 1)
        self.assertEquals(startingPart2RefCnt - mapper.RefCount(part2Ptr), 1)
    


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
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
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
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
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
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, 365)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, data)
        baseSize = Marshal.SizeOf(PyStringObject)
        self.assertEquals(allocs, [(data, 365 + baseSize)], "allocated wrong")
        self.assertEquals(mapper._PyString_Resize(ptrPtr, 2000000000), -1, "bad return on error")
        self.assertEquals(type(mapper.LastException), MemoryError, "wrong exception type")
        self.assertTrue(data in frees, "did not deallocate")    
        
        mapper.Dispose()
        Marshal.FreeHGlobal(ptrPtr)
        deallocTypes()


    def testShrink(self):
        allocs = []
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
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
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
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


class PyString_OtherMethodsTest(TestCase):
    
    @WithMapper
    def testStringifiers(self, mapper, _):
        src = 'foo \0 bar " \' " \' supercalifragilisticexpialidocious'
        srcPtr = mapper.Store(src)
        
        str_ = mapper.Retrieve(mapper.IC_PyString_Str(srcPtr))
        self.assertEquals(str_, src)
        self.assertEquals(mapper.IC_PyString_Str(mapper.Store(object())), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        for smartquotes in (0, 1):
            # smartquotes is ignored for now
            repr_ = mapper.Retrieve(mapper.PyString_Repr(srcPtr, smartquotes))
            self.assertEquals(repr_, repr(src))
            self.assertEquals(mapper.PyString_Repr(mapper.Store(object()), smartquotes), IntPtr.Zero)
            self.assertMapperHasError(mapper, TypeError)
    
    @WithMapper
    def testConcat(self, mapper, _):
        strs = ('', 'abc', '\0xo')
        for s1 in strs:
            for s2 in strs:
                s3ptr = mapper.IC_PyString_Concat_Core(mapper.Store(s1), mapper.Store(s2))
                self.assertEquals(mapper.Retrieve(s3ptr), s1 + s2)


class PyString_AsStringTest(PyString_TestCase):
    
    @WithMapper
    def testWorks(self, mapper, _):
        strPtr = mapper.Store("You're fighting a business hippy. This is a hippy that understands the law of supply and demand.")
        strData = CPyMarshal.Offset(strPtr, Marshal.OffsetOf(PyStringObject, 'ob_sval'))
        self.assertEquals(mapper.PyString_AsString(strPtr), self.dataPtrFromStrPtr(strPtr))
        
        notstrPtr = mapper.Store(object())
        self.assertEquals(mapper.PyString_AsString(notstrPtr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testDoesNotActualiseString(self, mapper, _):
        testString = "She's the oldest planet-cracker in existence"
        strPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, len(testString))
        
        self.fillStringDataWithBytes(strPtr, self.byteArrayFromString("blah blah nonsense blah"))
        mapper.PyString_AsString(strPtr) # this should NOT bake the string data
        self.fillStringDataWithBytes(strPtr, self.byteArrayFromString(testString))
        
        self.assertEquals(mapper.Retrieve(strPtr), testString)


class PyString_AsStringAndSizeTest(PyString_TestCase):
    
    @WithMapper
    def testWorksWithEmbeddedNulls(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        testStr = "You're fighting a saber-toothed ferret." + self.getStringWithValues(0, 256)
        strPtr = mapper.Store(testStr)
        dataPtr = self.dataPtrFromStrPtr(strPtr)
        self.assertEquals(mapper.PyString_AsStringAndSize(strPtr, dataPtrPtr, sizePtr), 0)
        self.assertEquals(CPyMarshal.ReadPtr(dataPtrPtr), dataPtr)
        self.assertEquals(CPyMarshal.ReadInt(sizePtr), len(testStr))
        self.assertMapperHasError(mapper, None)
        
        self.assertEquals(mapper.PyString_AsStringAndSize(strPtr, dataPtrPtr, IntPtr.Zero), -1)
        self.assertMapperHasError(mapper, TypeError)
    
    
    @WithMapper
    def testWorksWithoutEmbeddedNulls(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        testStr = "You're fighting Ed the Undying." + self.getStringWithValues(1, 256)
        strPtr = mapper.Store(testStr)
        dataPtr = self.dataPtrFromStrPtr(strPtr)
        self.assertEquals(mapper.PyString_AsStringAndSize(strPtr, dataPtrPtr, sizePtr), 0)
        self.assertEquals(CPyMarshal.ReadPtr(dataPtrPtr), dataPtr)
        self.assertEquals(CPyMarshal.ReadInt(sizePtr), len(testStr))
        self.assertMapperHasError(mapper, None)
        
        CPyMarshal.Zero(dataPtrPtr, CPyMarshal.PtrSize * 2)
        self.assertEquals(mapper.PyString_AsStringAndSize(strPtr, dataPtrPtr, IntPtr.Zero), 0)
        self.assertEquals(CPyMarshal.ReadPtr(dataPtrPtr), dataPtr)
        self.assertMapperHasError(mapper, None)

        
    @WithMapper
    def testWorksWithNonString(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        self.assertEquals(mapper.PyString_AsStringAndSize(mapper.Store(object()), dataPtrPtr, sizePtr), -1)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testDoesNotActualiseString(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        testString = "You find a frozen Mob Penguin."
        strPtr = mapper.PyString_FromStringAndSize(IntPtr.Zero, len(testString))
        
        self.fillStringDataWithBytes(strPtr, self.byteArrayFromString("blah blah nonsense"))
        mapper.PyString_AsStringAndSize(strPtr, dataPtrPtr, sizePtr) # this should NOT bake the string data
        self.fillStringDataWithBytes(strPtr, self.byteArrayFromString(testString))
        
        self.assertEquals(mapper.Retrieve(strPtr), testString)
        

class PyStringStoreTest(PyString_TestCase):
    
    def testStoreStringCreatesStringType(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
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

suite = automakesuite(locals())

if __name__ == '__main__':
    run(suite)
