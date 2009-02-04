
import sys

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, Python25Mapper
from Ironclad.Structs import PyTupleObject, PyTypeObject



def MakeTuple(mapper, model):
    tuplePtr = mapper.PyTuple_New(len(model))
    dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
    itemPtrs = []
    for i in range(len(model)):
        itemPtr = mapper.Store(model[i])
        itemPtrs.append(itemPtr)
        CPyMarshal.WritePtr(dataPtr, itemPtr)
        dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
    return tuplePtr, itemPtrs


class PyTuple_Type_Test(TypeTestCase):


    def testPyTupleTypeField_tp_free(self):
        self.assertUsual_tp_free("PyTuple_Type")
        

    def testPyTuple_Dealloc(self):
        frees = []
        def CreateMapper():
            return Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        model = (1, 2, 3)
        itemPtrs = []
        def CreateInstance(mapper, calls):
            tuplePtr = mapper.PyTuple_New(len(model))
            dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
            for i in range(len(model)):
                itemPtr = mapper.Store(model[i])
                itemPtrs.append(itemPtr)
                CPyMarshal.WritePtr(dataPtr, itemPtr)
                dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
            return tuplePtr
    
        def TestConsequences(mapper, tuplePtr, calls):
            for itemPtr in itemPtrs:
                self.assertEquals(itemPtr in frees, True, "did not decref item")
            self.assertEquals(calls, [('tp_free', tuplePtr)], "did not call tp_free")
            
        self.assertTypeDeallocWorks("PyTuple_Type", CreateMapper, CreateInstance, TestConsequences)
        
        

    def testPyTuple_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        
        calls = []
        def CustomFree(ptr):
            calls.append(ptr)
        freeDgt = dgt_void_ptr(CustomFree)
        
        CPyMarshal.WriteFunctionPtrField(mapper.PyTuple_Type, PyTypeObject, "tp_free", freeDgt)
        tuplePtr, itemPtrs = MakeTuple(mapper, (1, 2, 3))

        mapper.IC_PyTuple_Dealloc(tuplePtr)

        for itemPtr in itemPtrs:
            self.assertEquals(itemPtr in frees, True, "did not decref item")
        self.assertEquals(calls, [tuplePtr], "did not call type's free function")
        mapper.PyObject_Free(tuplePtr)

        mapper.Dispose()
        deallocTypes()
    


class TupleTest(TestCase):
    
    def assertPyTuple_New_Works(self, length):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))

        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        mapper.SetData("PyTuple_Type", typeBlock)
        tuplePtr = mapper.PyTuple_New(length)
        expectedSize = Marshal.SizeOf(PyTupleObject) + (CPyMarshal.PtrSize * (length - 1))
        self.assertEquals(allocs, [(tuplePtr, expectedSize)], "bad alloc")
        tupleStruct = Marshal.PtrToStructure(tuplePtr, PyTupleObject)
        self.assertEquals(tupleStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(tupleStruct.ob_type, mapper.PyTuple_Type, "bad type")
        self.assertEquals(tupleStruct.ob_size, length, "bad size")
        self.assertEquals(mapper.PyTuple_Size(tuplePtr), length, "should still work with uninitialised tuple imo")
        dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
        itemPtrs = []
        for i in range(length):
            self.assertEquals(CPyMarshal.ReadPtr(dataPtr), IntPtr.Zero, "item memory not zeroed")
            itemPtr = mapper.Store(i + 100)
            CPyMarshal.WritePtr(dataPtr, itemPtr)
            itemPtrs.append(itemPtr)
            dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)

        immutableTuple = mapper.Retrieve(tuplePtr)
        self.assertEquals(immutableTuple, tuple(i + 100 for i in range(length)), "broken")

        tuplePtr2 = mapper.Store(immutableTuple)
        self.assertEquals(tuplePtr2, tuplePtr, "didn't realise already had this object stored")
        self.assertEquals(mapper.RefCount(tuplePtr), 2, "didn't incref")
        
        mapper.Dispose()
        Marshal.FreeHGlobal(typeBlock)
    
    
    def testPyTuple_New(self):
        self.assertPyTuple_New_Works(1)
        self.assertPyTuple_New_Works(3)


    @WithMapper
    def testCanSafelyFreeUninitialisedTuple(self, mapper, _):
        markedPtr = mapper.PyTuple_New(2)
        mapper.DecRef(markedPtr)


    def test_PyTuple_Resize(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        tuplePtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        oldTuplePtr = mapper.PyTuple_New(1)
        del allocs[:]
        CPyMarshal.WritePtr(tuplePtrPtr, oldTuplePtr)
        self.assertEquals(mapper._PyTuple_Resize(tuplePtrPtr, 100), 0)

        newTuplePtr = CPyMarshal.ReadPtr(tuplePtrPtr)
        expectedSize = Marshal.SizeOf(PyTupleObject) + (CPyMarshal.PtrSize * (99))
        self.assertEquals(allocs, [(newTuplePtr, expectedSize)])
        
        tupleStruct = Marshal.PtrToStructure(newTuplePtr, PyTupleObject)
        self.assertEquals(tupleStruct.ob_refcnt, 1)
        self.assertEquals(tupleStruct.ob_type, mapper.PyTuple_Type)
        self.assertEquals(tupleStruct.ob_size, 100)
        
        mapper.Dispose()
        Marshal.FreeHGlobal(tuplePtrPtr)
        

    @WithMapper
    def test_PyTuple_Resize_TooBig(self, mapper, addDealloc):
        tuplePtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(tuplePtrPtr))
        
        tuplePtr = mapper.PyTuple_New(1)
        CPyMarshal.WritePtr(tuplePtrPtr, tuplePtr)
        self.assertEquals(mapper._PyTuple_Resize(tuplePtrPtr, 2000000000), -1)
        self.assertEquals(CPyMarshal.ReadPtr(tuplePtrPtr), IntPtr.Zero)
        

    def testStoreTupleCreatesTupleType(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        mapper.SetData("PyTuple_Type", typeBlock)

        theTuple = (0, 1, 2)
        tuplePtr = mapper.Store(theTuple)
        self.assertEquals(CPyMarshal.ReadPtrField(tuplePtr, PyTupleObject, "ob_type"), typeBlock, "wrong type")

        dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
        for i in range(3):
            item = mapper.Retrieve(CPyMarshal.ReadPtr(dataPtr))
            self.assertEquals(item, i, "did not store data")
            dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)

        tuplePtr2 = mapper.Store(theTuple)
        self.assertEquals(tuplePtr2, tuplePtr, "didn't realise already had this tuple")
        self.assertEquals(mapper.RefCount(tuplePtr), 2, "didn't incref")

        mapper.Dispose()
        Marshal.FreeHGlobal(typeBlock)


    @WithMapper
    def testPyTuple_GetSlice(self, mapper, _):
        def TestSlice(originalTuplePtr, start, stop):
            newTuplePtr = mapper.PyTuple_GetSlice(originalTuplePtr, start, stop)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(mapper.Retrieve(newTuplePtr), mapper.Retrieve(originalTuplePtr)[start:stop], "bad slice")
            mapper.DecRef(newTuplePtr)
        
        tuplePtr = mapper.Store((0, 1, 2, 3, 4, 5, 6, 7))
        slices = (
            (3, 4), (5, 0), (5, 200), (999, 1000)
        )
        for (start, stop) in slices:
            TestSlice(tuplePtr, start, stop)
            
         
    @WithMapper
    def testPyTuple_GetSlice_error(self, mapper, _):
        self.assertEquals(mapper.PyTuple_GetSlice(mapper.Store(object()), 1, 2), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)



suite = makesuite(
    PyTuple_Type_Test,
    TupleTest,
)

if __name__ == '__main__':
    run(suite)
