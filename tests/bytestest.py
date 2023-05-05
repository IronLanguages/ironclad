
from tests.utils.runtest import automakesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr, CreateTypes, PtrToStructure
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import Array, Byte, Char, IntPtr, Type, UInt32
from System.Collections.Generic import List
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, dgt_int_ptrssizeptr, dgt_int_ptrptr, dgt_ptr_ptrptr, PythonMapper
from Ironclad.Structs import PyBytesObject, PyTypeObject, PyBufferProcs, PySequenceMethods


class PyBytes_TestCase(TestCase):

    def byteArrayFromBytes(self, testBytes):
        return List[Byte](testBytes).ToArray()

    def ptrFromByteArray(self, bytes):
        testData = Marshal.AllocHGlobal(bytes.Length + 1)
        Marshal.Copy(bytes, 0, testData, bytes.Length)
        Marshal.WriteByte(OffsetPtr(testData, bytes.Length), 0)
        return testData


    def dataPtrFromStrPtr(self, strPtr):
        return OffsetPtr(strPtr, Marshal.OffsetOf(PyBytesObject, "ob_sval"))


    def fillBytesDataWithBytes(self, bytesPtr, bytes):
        bytesDataPtr = self.dataPtrFromStrPtr(bytesPtr)
        Marshal.Copy(bytes, 0, bytesDataPtr, len(bytes))


    def getBytesWithValues(self, start, pastEnd):
        return bytes(range(start, pastEnd))


    def assertHasBytesType(self, ptr, mapper):
        self.assertEqual(CPyMarshal.ReadPtrField(ptr, PyBytesObject, "ob_type"), mapper.PyBytes_Type, "bad type")


    def assertBytesObjectHasLength(self, strPtr, length):
        bytesObject = PtrToStructure(strPtr, PyBytesObject)
        self.assertEqual(bytesObject.ob_refcnt, 1, "unexpected refcount")
        self.assertEqual(bytesObject.ob_size, length, "unexpected ob_size")
        self.assertEqual(bytesObject.ob_shash, -1, "unexpected currently-useless-field")
        
        strDataPtr = self.dataPtrFromStrPtr(strPtr)
        terminatorPtr = OffsetPtr(strDataPtr, length)
        self.assertEqual(Marshal.ReadByte(terminatorPtr), 0, "bytes not terminated")


    def assertBytesObjectHasDataBytes(self, strPtr, expectedBytes):
        strDataPtr = self.dataPtrFromStrPtr(strPtr)
        testLength = len(expectedBytes)
        writtenBytes = Array.CreateInstance(Byte, testLength)
        Marshal.Copy(strDataPtr, writtenBytes, 0, testLength)

        self.assertEqual(len(writtenBytes), testLength, "copied wrong")
        for (actual, expected) in zip(writtenBytes, expectedBytes):
            self.assertEqual(actual, expected, "failed to copy bytes data correctly")


class PyBytes_Type_Test(TypeTestCase):
    
    def testBytes_tp_free(self):
        self.assertUsual_tp_free("PyBytes_Type")
    
    def testBytes_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyBytes_Type")


    @WithMapper
    def testSizes(self, mapper, _):
        tp_basicsize = CPyMarshal.ReadIntField(mapper.PyBytes_Type, PyTypeObject, 'tp_basicsize')
        self.assertNotEqual(tp_basicsize, 0)
        tp_itemsize = CPyMarshal.ReadIntField(mapper.PyBytes_Type, PyTypeObject, 'tp_itemsize')
        self.assertNotEqual(tp_itemsize, 0)


    @WithMapper
    def testStringifiers(self, mapper, _):
        IC_PyBytes_Str = mapper.GetFuncPtr("IC_PyBytes_Str")
        tp_str = CPyMarshal.ReadPtrField(mapper.PyBytes_Type, PyTypeObject, "tp_str")
        self.assertEqual(tp_str, IC_PyBytes_Str)
        
        PyObject_Repr = mapper.GetFuncPtr("PyObject_Repr")
        tp_repr = CPyMarshal.ReadPtrField(mapper.PyBytes_Type, PyTypeObject, "tp_repr")
        self.assertEqual(tp_repr, PyObject_Repr)


    @WithMapper
    def testSequenceProtocol(self, mapper, _):
        strPtr = mapper.PyBytes_Type
        
        seqPtr = CPyMarshal.ReadPtrField(strPtr, PyTypeObject, 'tp_as_sequence')
        self.assertNotEqual(seqPtr, IntPtr.Zero)
        concatPtr = CPyMarshal.ReadPtrField(seqPtr, PySequenceMethods, 'sq_concat')
        # concat_core tested further down
        self.assertEqual(concatPtr, mapper.GetFuncPtr('IC_PyBytes_Concat_Core'))
        
        
    @WithMapper
    def testBufferProtocol(self, mapper, later):
        # should all be implemented in C really, but weaving cpy bytes type into
        # our code feels too much like hard work for now
        strPtr = mapper.PyBytes_Type
        
        bufPtr = CPyMarshal.ReadPtrField(strPtr, PyTypeObject, 'tp_as_buffer')
        self.assertNotEqual(bufPtr, IntPtr.Zero)
        getbuffer = CPyMarshal.ReadFunctionPtrField(bufPtr, PyBufferProcs, 'bf_getbuffer', dgt_int_ptrssizeptr)
        releasebuffer = CPyMarshal.ReadFunctionPtrField(bufPtr, PyBufferProcs, 'bf_releasebuffer', dgt_int_ptrssizeptr)
        raise NotImplementedError("buffer protocol...") # https://github.com/IronLanguages/ironclad/issues/15
        
        ptrptr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        later(lambda: Marshal.FreeHGlobal(ptrptr))
        
        strptr = mapper.Store("hullo")
        for getter in (getreadbuffer, getcharbuffer):
            self.assertEqual(getter(strptr, IntPtr(0), ptrptr), 5)
            self.assertEqual(CPyMarshal.ReadPtr(ptrptr), CPyMarshal.GetField(strptr, PyBytesObject, 'ob_sval'))
            self.assertEqual(getter(strptr, IntPtr(1), ptrptr), -1)
            self.assertMapperHasError(mapper, SystemError)
        
        self.assertEqual(getwritebuffer(strptr, IntPtr(0), ptrptr), -1)
        self.assertMapperHasError(mapper, SystemError)
        
        self.assertEqual(getsegcount(strptr, ptrptr), 1)
        self.assertEqual(CPyMarshal.ReadInt(ptrptr), 5)
        self.assertEqual(getsegcount(strptr, IntPtr.Zero), 1)


class PyBytes_FromString_Test(PyBytes_TestCase):

    def testCreatesBytes(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]
        testBytes = b"beset on all sides" + self.getBytesWithValues(1, 256)
        byteArray = self.byteArrayFromBytes(testBytes)
        testData = self.ptrFromByteArray(byteArray)
        try:
            strPtr = mapper.PyBytes_FromString(testData)
            baseSize = Marshal.SizeOf(PyBytesObject())
            self.assertEqual(allocs, [(strPtr, len(byteArray) + baseSize)], "allocated wrong")
            self.assertBytesObjectHasLength(strPtr, len(byteArray))
            self.assertBytesObjectHasDataBytes(strPtr, byteArray)
            self.assertEqual(mapper.Retrieve(strPtr), testBytes, "failed to map pointer correctly")
        finally:
            mapper.Dispose()
            Marshal.FreeHGlobal(testData)
            deallocTypes()


class PyBytes_Concat_Test(PyBytes_TestCase):

    @WithMapper
    def testBasic(self, mapper, addToCleanup):
        part1Ptr = mapper.Store(b"one two")
        mapper.IncRef(part1Ptr) # avoid garbage collection
        part2Ptr = mapper.Store(b" three")
        startingRefCnt = mapper.RefCount(part1Ptr)
        
        bytesPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        addToCleanup(lambda: Marshal.FreeHGlobal(bytesPtrPtr))
        
        Marshal.WriteIntPtr(bytesPtrPtr, part1Ptr)
        mapper.PyBytes_Concat(bytesPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, None)
        
        newBytesPtr = Marshal.ReadIntPtr(bytesPtrPtr)
        self.assertEqual(mapper.Retrieve(newBytesPtr), b"one two three")

        self.assertEqual(startingRefCnt - mapper.RefCount(part1Ptr), 1)


    @WithMapper
    def testErrorCaseSecondArg(self, mapper, addToCleanup):
        part1Ptr = mapper.Store(b"one two")
        mapper.IncRef(part1Ptr) # avoid garbage collection
        startingRefCnt = mapper.RefCount(part1Ptr)
        
        part2Ptr = mapper.Store(3)
        bytesPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        addToCleanup(lambda: Marshal.FreeHGlobal(bytesPtrPtr))
        
        Marshal.WriteIntPtr(bytesPtrPtr, part1Ptr)
        mapper.PyBytes_Concat(bytesPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, TypeError)

        self.assertEqual(Marshal.ReadIntPtr(bytesPtrPtr), IntPtr(0))
        self.assertEqual(startingRefCnt - mapper.RefCount(part1Ptr), 1)


    @WithMapper
    def testErrorCaseSecondArg(self, mapper, addToCleanup):
        part1Ptr = mapper.Store(17)
        mapper.IncRef(part1Ptr) # avoid garbage collection
        startingRefCnt = mapper.RefCount(part1Ptr)

        part2Ptr = mapper.Store(b"three")
        bytesPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        addToCleanup(lambda: Marshal.FreeHGlobal(bytesPtrPtr))
        
        Marshal.WriteIntPtr(bytesPtrPtr, part1Ptr)
        mapper.PyBytes_Concat(bytesPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, TypeError)

        self.assertEqual(Marshal.ReadIntPtr(bytesPtrPtr), IntPtr(0))
        self.assertEqual(startingRefCnt - mapper.RefCount(part1Ptr), 1)


class PyBytes_ConcatAndDel_Test(PyBytes_TestCase):

    @WithMapper
    def testBasic(self, mapper, addToCleanup):
        part1Ptr = mapper.Store(b"one two")
        mapper.IncRef(part1Ptr) # avoid garbage collection
        startingPart1RefCnt = mapper.RefCount(part1Ptr)
        
        part2Ptr = mapper.Store(b" three")
        mapper.IncRef(part2Ptr) # avoid garbage collection
        startingPart2RefCnt = mapper.RefCount(part2Ptr)

        bytesPtrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        addToCleanup(lambda: Marshal.FreeHGlobal(bytesPtrPtr))
        
        Marshal.WriteIntPtr(bytesPtrPtr, part1Ptr)
        mapper.PyBytes_ConcatAndDel(bytesPtrPtr, part2Ptr)
        self.assertMapperHasError(mapper, None)

        newBytesPtr = Marshal.ReadIntPtr(bytesPtrPtr)
        self.assertEqual(mapper.Retrieve(newBytesPtr), b"one two three")

        self.assertEqual(startingPart1RefCnt - mapper.RefCount(part1Ptr), 1)
        self.assertEqual(startingPart2RefCnt - mapper.RefCount(part2Ptr), 1)
    


class InternTest(PyBytes_TestCase):
        
    @WithMapper
    def testInternExisting(self, mapper, addToCleanUp):
        raise NotImplementedError("PyUnicode_InternFromString") # https://github.com/IronLanguages/ironclad/issues/13
        
        testString = "mars needs women" + self.getStringWithValues(1, 256)
        bytes = self.byteArrayFromString(testString)
        testData = self.ptrFromByteArray(bytes)
        
        sp1 = mapper.PyString_FromString(testData)
        addToCleanUp(lambda: Marshal.FreeHGlobal(sp1p))

        sp2 = mapper.PyString_InternFromString(testData)
        addToCleanUp(lambda: Marshal.FreeHGlobal(testData))

        self.assertNotEqual(sp1, sp2)
        self.assertFalse(mapper.Retrieve(sp1) is mapper.Retrieve(sp2))
        self.assertEqual(mapper.RefCount(sp1), 1)
        self.assertEqual(mapper.RefCount(sp2), 2, 'failed to grab extra reference to induce immortality')
        
        mapper.IncRef(sp1)
        sp1p = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        CPyMarshal.WritePtr(sp1p, sp1)
        mapper.PyString_InternInPlace(sp1p)
        sp1i = CPyMarshal.ReadPtr(sp1p)
        self.assertEqual(sp1i, sp2, 'failed to intern')
        self.assertTrue(mapper.Retrieve(sp1i) is mapper.Retrieve(sp2))
        self.assertEqual(mapper.RefCount(sp1), 1, 'failed to decref old string')
        self.assertEqual(mapper.RefCount(sp2), 3, 'failed to incref interned string')



class PyBytes_FromStringAndSize_Test(PyBytes_TestCase):

    def testCreateEmptyString(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        try:
            testBytes = b"we run the grease racket in this town" + self.getBytesWithValues(0, 256)
            testLength = len(testBytes)
            strPtr = mapper.PyBytes_FromStringAndSize(IntPtr.Zero, IntPtr(testLength))
            baseSize = Marshal.SizeOf(PyBytesObject())
            self.assertEqual(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
            self.assertBytesObjectHasLength(strPtr, testLength)
            self.assertHasBytesType(strPtr, mapper)
            testByteArray = self.byteArrayFromBytes(testBytes)
            self.fillBytesDataWithBytes(strPtr, testByteArray)

            resultStr = mapper.Retrieve(strPtr)
            self.assertEqual(resultStr, testBytes, "failed to read bytes data")
            
            strPtr2 = mapper.Store(resultStr)
            self.assertEqual(strPtr2, strPtr, "did not remember already had this bytes")
            self.assertEqual(mapper.RefCount(strPtr), 2, "did not incref on store")
        finally:
            mapper.Dispose()
            deallocTypes()


    def testCreateBytesWithData(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        try:
            testBytes = b"we also run the shovel racket" + self.getBytesWithValues(0, 256)
            testByteArray = self.byteArrayFromBytes(testBytes)
            testData = self.ptrFromByteArray(testByteArray)
            testLength = len(testBytes)

            strPtr = mapper.PyBytes_FromStringAndSize(testData, IntPtr(testLength))
            baseSize = Marshal.SizeOf(PyBytesObject())
            self.assertEqual(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
            self.assertHasBytesType(strPtr, mapper)
            self.assertBytesObjectHasLength(strPtr, testLength)
            self.assertBytesObjectHasDataBytes(strPtr, testByteArray)
            self.assertEqual(mapper.Retrieve(strPtr), testBytes, "failed to read bytes data")
        finally:
            mapper.Dispose()
            deallocTypes()


class _PyBytes_Resize_Test(PyBytes_TestCase):

    def testErrorHandling(self):
        allocs = []
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))

        try:
            data = mapper.PyBytes_FromStringAndSize(IntPtr.Zero, IntPtr(365))
            Marshal.WriteIntPtr(ptrPtr, data)
            baseSize = Marshal.SizeOf(PyBytesObject())
            self.assertEqual(allocs, [(data, 365 + baseSize)], "allocated wrong")
            self.assertEqual(mapper._PyBytes_Resize(ptrPtr, IntPtr(1<<40)), -1, "bad return on error")
            self.assertEqual(type(mapper.LastException), MemoryError, "wrong exception type")
            self.assertTrue(data in frees, "did not deallocate")    
        finally:
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
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))

        try:
            strPtr = mapper.PyBytes_FromStringAndSize(IntPtr.Zero, IntPtr(oldLength))
            Marshal.WriteIntPtr(ptrPtr, strPtr)
            
            baseSize = Marshal.SizeOf(PyBytesObject())
            self.assertEqual(allocs, [(strPtr, oldLength + baseSize)], "allocated wrong")
            self.assertEqual(mapper._PyBytes_Resize(ptrPtr, IntPtr(newLength)), 0, "bad return on success")
            
            self.assertHasBytesType(strPtr, mapper)
            self.assertBytesObjectHasLength(strPtr, newLength)

            self.assertEqual(allocs, [(strPtr, oldLength + baseSize)], "unexpected extra alloc")
            self.assertEqual(frees, [], "unexpected frees")
        finally:
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
        testBytes = b"slings and arrows" + self.getBytesWithValues(0, 256)
        newLength = len(testBytes)

        oldStrPtr = mapper.PyBytes_FromStringAndSize(IntPtr.Zero, IntPtr(oldLength))
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr()))
        
        try:
            Marshal.WriteIntPtr(ptrPtr, oldStrPtr)
            newStrPtr = IntPtr.Zero
            
            baseSize = Marshal.SizeOf(PyBytesObject())
            self.assertEqual(allocs, [(oldStrPtr, oldLength + baseSize)], "allocated wrong")
            self.assertEqual(mapper._PyBytes_Resize(ptrPtr, IntPtr(newLength)), 0, "bad return on success")

            newStrPtr = Marshal.ReadIntPtr(ptrPtr)
            expectedAllocs = [(oldStrPtr, oldLength + baseSize), (newStrPtr, newLength + baseSize)]
            self.assertEqual(allocs, expectedAllocs,
                              "allocated wrong")
            self.assertEqual(frees, [oldStrPtr], "did not free unused memory")

            self.assertHasBytesType(newStrPtr, mapper)
            self.assertBytesObjectHasLength(newStrPtr, newLength)

            testByteArray = self.byteArrayFromBytes(testBytes)
            self.fillBytesDataWithBytes(newStrPtr, testByteArray)

            self.assertEqual(mapper.Retrieve(newStrPtr), testBytes, "failed to read bytes data")
            if oldStrPtr != newStrPtr:
                # this would otherwise fail (very, very rarely)
                self.assertEqual(oldStrPtr in frees, True)
        finally:
            mapper.Dispose()
            Marshal.FreeHGlobal(ptrPtr)
            deallocTypes()
            

class PyBytes_Size_Test(PyBytes_TestCase):
    
    @WithMapper
    def testWorks(self, mapper, _):
        testBytes = b"Oh, sure, Lisa -- some wonderful, magical animal." + self.getBytesWithValues(0, 256)
        testLength = len(testBytes)
        
        strPtr = mapper.Store(testBytes)
        self.assertEqual(mapper.PyBytes_Size(strPtr), testLength)


class PyBytes_OtherMethodsTest(TestCase):
    
    @WithMapper
    def testStringifiers(self, mapper, _):
        src = b'foo \0 bar " \' " \' supercalifragilisticexpialidocious'
        srcPtr = mapper.Store(src)
        
        str_ = mapper.Retrieve(mapper.IC_PyBytes_Str(srcPtr))
        self.assertEqual(str_, src)
        self.assertEqual(mapper.IC_PyBytes_Str(mapper.Store(object())), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        for smartquotes in (0, 1):
            # smartquotes is ignored for now
            repr_ = mapper.Retrieve(mapper.PyBytes_Repr(srcPtr, smartquotes))
            self.assertEqual(repr_, repr(src))
            self.assertEqual(mapper.PyBytes_Repr(mapper.Store(object()), smartquotes), IntPtr.Zero)
            self.assertMapperHasError(mapper, TypeError)
    
    @WithMapper
    def testConcat(self, mapper, _):
        strs = (b'', b'abc', b'\0xo')
        for s1 in strs:
            for s2 in strs:
                s3ptr = mapper.IC_PyBytes_Concat_Core(mapper.Store(s1), mapper.Store(s2))
                self.assertEqual(mapper.Retrieve(s3ptr), s1 + s2)


class PyBytes_AsStringTest(PyBytes_TestCase):
    
    @WithMapper
    def testWorks(self, mapper, _):
        bytesPtr = mapper.Store(b"You're fighting a business hippy. This is a hippy that understands the law of supply and demand.")
        bytesData = CPyMarshal.Offset(bytesPtr, Marshal.OffsetOf(PyBytesObject, 'ob_sval'))
        self.assertEqual(mapper.PyBytes_AsString(bytesPtr), self.dataPtrFromStrPtr(bytesPtr))
        
        notBytesPtr = mapper.Store(object())
        self.assertEqual(mapper.PyBytes_AsString(notBytesPtr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testDoesNotActualisePyBytesObject(self, mapper, _):
        testBytes = b"She's the oldest planet-cracker in existence"
        strPtr = mapper.PyBytes_FromStringAndSize(IntPtr.Zero, IntPtr(len(testBytes)))
        
        self.fillBytesDataWithBytes(strPtr, self.byteArrayFromBytes(b"blah blah nonsense blah"))
        mapper.PyBytes_AsString(strPtr) # this should NOT bake the bytes data
        self.fillBytesDataWithBytes(strPtr, self.byteArrayFromBytes(testBytes))
        
        self.assertEqual(mapper.Retrieve(strPtr), testBytes)


class PyBytes_AsStringAndSizeTest(PyBytes_TestCase):
    
    @WithMapper
    def testWorksWithEmbeddedNulls(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        testBytes = b"You're fighting a saber-toothed ferret." + self.getBytesWithValues(0, 256)
        bytesPtr = mapper.Store(testBytes)
        dataPtr = self.dataPtrFromStrPtr(bytesPtr)
        self.assertEqual(mapper.PyBytes_AsStringAndSize(bytesPtr, dataPtrPtr, sizePtr), 0)
        self.assertEqual(CPyMarshal.ReadPtr(dataPtrPtr), dataPtr)
        self.assertEqual(CPyMarshal.ReadInt(sizePtr), len(testBytes))
        self.assertMapperHasError(mapper, None)
        
        self.assertEqual(mapper.PyBytes_AsStringAndSize(bytesPtr, dataPtrPtr, IntPtr.Zero), -1)
        self.assertMapperHasError(mapper, TypeError)
    
    
    @WithMapper
    def testWorksWithoutEmbeddedNulls(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        testBytes = b"You're fighting Ed the Undying." + self.getBytesWithValues(1, 256)
        bytesPtr = mapper.Store(testBytes)
        dataPtr = self.dataPtrFromStrPtr(bytesPtr)
        self.assertEqual(mapper.PyBytes_AsStringAndSize(bytesPtr, dataPtrPtr, sizePtr), 0)
        self.assertEqual(CPyMarshal.ReadPtr(dataPtrPtr), dataPtr)
        self.assertEqual(CPyMarshal.ReadInt(sizePtr), len(testBytes))
        self.assertMapperHasError(mapper, None)
        
        CPyMarshal.Zero(dataPtrPtr, CPyMarshal.PtrSize * 2)
        self.assertEqual(mapper.PyBytes_AsStringAndSize(bytesPtr, dataPtrPtr, IntPtr.Zero), 0)
        self.assertEqual(CPyMarshal.ReadPtr(dataPtrPtr), dataPtr)
        self.assertMapperHasError(mapper, None)

        
    @WithMapper
    def testWorksWithNonBytes(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        self.assertEqual(mapper.PyBytes_AsStringAndSize(mapper.Store(object()), dataPtrPtr, sizePtr), -1)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testDoesNotActualiseBytes(self, mapper, addDealloc):
        dataPtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 2)
        sizePtr = CPyMarshal.Offset(dataPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(dataPtrPtr))
        
        testBytes = b"You find a frozen Mob Penguin."
        bytesPtr = mapper.PyBytes_FromStringAndSize(IntPtr.Zero, IntPtr(len(testBytes)))
        
        self.fillBytesDataWithBytes(bytesPtr, self.byteArrayFromBytes(b"blah blah nonsense"))
        mapper.PyBytes_AsStringAndSize(bytesPtr, dataPtrPtr, sizePtr) # this should NOT bake the bytes data
        self.fillBytesDataWithBytes(bytesPtr, self.byteArrayFromBytes(testBytes))
        
        self.assertEqual(mapper.Retrieve(bytesPtr), testBytes)
        

class PyBytesStoreTest(PyBytes_TestCase):
    
    def testStoreBytesCreatesBytesType(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]

        testBytes = b"fnord" + self.getBytesWithValues(1, 256)
        testByteArray = self.byteArrayFromBytes(testBytes)
        testData = self.ptrFromByteArray(testByteArray)
        testLength = len(testBytes)

        try:
            strPtr = mapper.Store(testBytes)
            baseSize = Marshal.SizeOf(PyBytesObject())
            
            self.assertEqual(allocs, [(strPtr, testLength + baseSize)], "allocated wrong")
            self.assertHasBytesType(strPtr, mapper)
            self.assertBytesObjectHasLength(strPtr, testLength)
            self.assertBytesObjectHasDataBytes(strPtr, testByteArray)
            self.assertEqual(mapper.Retrieve(strPtr), testBytes, "failed to read bytes data")
            
            strPtr2 = mapper.Store(testBytes)
            self.assertEqual(strPtr2, strPtr, "did not remember already had this bytes")
            self.assertEqual(mapper.RefCount(strPtr), 2, "did not incref on store")
        finally:
            mapper.Dispose()
            deallocTypes()

suite = automakesuite(locals())

if __name__ == '__main__':
    run(suite)
