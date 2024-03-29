
import sys

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import CreateTypes, OffsetPtr, PtrToStructure
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr, Type
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, PythonMapper
from Ironclad.Structs import PyTupleObject, PyTypeObject

def MakeTuple(mapper, model):
    tuplePtr = mapper.PyTuple_New(IntPtr(len(model)))
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
            return PythonMapper(GetAllocatingTestAllocator([], frees))
        
        model = (1, 2, 3)
        itemPtrs = []
        def CreateInstance(mapper, calls):
            tuplePtr = mapper.PyTuple_New(IntPtr(len(model)))
            dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
            for i in range(len(model)):
                itemPtr = mapper.Store(model[i])
                itemPtrs.append(itemPtr)
                CPyMarshal.WritePtr(dataPtr, itemPtr)
                dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
            return tuplePtr
    
        def TestConsequences(mapper, tuplePtr, calls):
            for itemPtr in itemPtrs:
                self.assertEqual(itemPtr in frees, True, "did not decref item")
            self.assertEqual(calls, [('tp_free', tuplePtr)], "did not call tp_free")
            
        self.assertTypeDeallocWorks("PyTuple_Type", CreateMapper, CreateInstance, TestConsequences)
        
        

    def testPyTuple_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        with PythonMapper(GetAllocatingTestAllocator([], frees)) as mapper:
            deallocTypes = CreateTypes(mapper)
            
            calls = []
            def CustomFree(ptr):
                calls.append(ptr)
            freeDgt = dgt_void_ptr(CustomFree)
            
            CPyMarshal.WriteFunctionPtrField(mapper.PyTuple_Type, PyTypeObject, "tp_free", freeDgt)
            tuplePtr, itemPtrs = MakeTuple(mapper, (1, 2, 3))

            mapper.IC_PyTuple_Dealloc(tuplePtr)

            for itemPtr in itemPtrs:
                self.assertEqual(itemPtr in frees, True, "did not decref item")
            self.assertEqual(calls, [tuplePtr], "did not call type's free function")
            mapper.PyObject_Free(tuplePtr)

        deallocTypes()
    


class TupleTest(TestCase):
    
    def assertPyTuple_New_Works(self, length):
        allocs = []
        with PythonMapper(GetAllocatingTestAllocator(allocs, [])) as mapper:

            typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
            mapper.RegisterData("PyTuple_Type", typeBlock)
            tuplePtr = mapper.PyTuple_New(IntPtr(length))
            expectedSize = Marshal.SizeOf(PyTupleObject()) + CPyMarshal.PtrSize * max(0, length - 1)
            self.assertEqual(allocs, [(tuplePtr, expectedSize)], "bad alloc")
            tupleStruct = PtrToStructure(tuplePtr, PyTupleObject)
            self.assertEqual(tupleStruct.ob_refcnt, 1, "bad refcount")
            self.assertEqual(tupleStruct.ob_type, mapper.PyTuple_Type, "bad type")
            self.assertEqual(tupleStruct.ob_size, length, "bad size")
            self.assertEqual(mapper.PyTuple_Size(tuplePtr), length, "should still work with uninitialised tuple imo")
            dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
            itemPtrs = []
            for i in range(length):
                self.assertEqual(CPyMarshal.ReadPtr(dataPtr), IntPtr.Zero, "item memory not zeroed")
                itemPtr = mapper.Store(i + 100)
                CPyMarshal.WritePtr(dataPtr, itemPtr)
                itemPtrs.append(itemPtr)
                dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)

            immutableTuple = mapper.Retrieve(tuplePtr)
            self.assertEqual(immutableTuple, tuple(i + 100 for i in range(length)), "broken")

            tuplePtr2 = mapper.Store(immutableTuple)
            self.assertEqual(tuplePtr2, tuplePtr, "didn't realise already had this object stored")
            self.assertEqual(mapper.RefCount(tuplePtr), 2, "didn't incref")
            
        Marshal.FreeHGlobal(typeBlock)
    
    
    def testPyTuple_New(self):
        self.assertPyTuple_New_Works(1)
        self.assertPyTuple_New_Works(3)


    @WithMapper
    def testCanSafelyFreeUninitialisedTuple(self, mapper, _):
        markedPtr = mapper.PyTuple_New(IntPtr(2))
        mapper.DecRef(markedPtr)


    def test_PyTuple_Resize(self):
        allocs = []
        with PythonMapper(GetAllocatingTestAllocator(allocs, [])) as mapper:
            tuplePtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
            
            oldTuplePtr = mapper.PyTuple_New(IntPtr(1))
            del allocs[:]
            CPyMarshal.WritePtr(tuplePtrPtr, oldTuplePtr)
            self.assertEqual(mapper._PyTuple_Resize(tuplePtrPtr, IntPtr(100)), 0)

            newTuplePtr = CPyMarshal.ReadPtr(tuplePtrPtr)
            expectedSize = Marshal.SizeOf(PyTupleObject()) + (CPyMarshal.PtrSize * (99))
            self.assertEqual(allocs, [(newTuplePtr, expectedSize)])
            
            tupleStruct = PtrToStructure(newTuplePtr, PyTupleObject)
            self.assertEqual(tupleStruct.ob_refcnt, 1)
            self.assertEqual(tupleStruct.ob_type, mapper.PyTuple_Type)
            self.assertEqual(tupleStruct.ob_size, 100)
            
        Marshal.FreeHGlobal(tuplePtrPtr)
        

    @WithMapper
    def test_PyTuple_Resize_TooBig(self, mapper, addDealloc):
        tuplePtrPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(tuplePtrPtr))
        
        tuplePtr = mapper.PyTuple_New(IntPtr(1))
        CPyMarshal.WritePtr(tuplePtrPtr, tuplePtr)
        self.assertEqual(mapper._PyTuple_Resize(tuplePtrPtr, IntPtr(1<<40)), -1)
        self.assertEqual(CPyMarshal.ReadPtr(tuplePtrPtr), IntPtr.Zero)
        

    def testStoreTupleCreatesTupleType(self):
        allocs = []
        with PythonMapper(GetAllocatingTestAllocator(allocs, [])) as mapper:
            
            typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
            mapper.RegisterData("PyTuple_Type", typeBlock)

            theTuple = (0, 1, 2)
            tuplePtr = mapper.Store(theTuple)
            self.assertEqual(CPyMarshal.ReadPtrField(tuplePtr, PyTupleObject, "ob_type"), typeBlock, "wrong type")

            dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
            for i in range(3):
                item = mapper.Retrieve(CPyMarshal.ReadPtr(dataPtr))
                self.assertEqual(item, i, "did not store data")
                dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)

            tuplePtr2 = mapper.Store(theTuple)
            self.assertEqual(tuplePtr2, tuplePtr, "didn't realise already had this tuple")
            self.assertEqual(mapper.RefCount(tuplePtr), 2, "didn't incref")

        Marshal.FreeHGlobal(typeBlock)


    @WithMapper
    def testPyTuple_GetSlice(self, mapper, _):
        def TestSlice(originalTuplePtr, start, stop):
            newTuplePtr = mapper.PyTuple_GetSlice(originalTuplePtr, IntPtr(start), IntPtr(stop))
            self.assertMapperHasError(mapper, None)
            self.assertEqual(mapper.Retrieve(newTuplePtr), mapper.Retrieve(originalTuplePtr)[start:stop], "bad slice")
            mapper.DecRef(newTuplePtr)
        
        tuplePtr = mapper.Store((0, 1, 2, 3, 4, 5, 6, 7))
        slices = (
            (3, 4), (5, 0), (5, 200), (999, 1000)
        )
        for (start, stop) in slices:
            TestSlice(tuplePtr, start, stop)
            
         
    @WithMapper
    def testPyTuple_GetSlice_error(self, mapper, _):
        self.assertEqual(mapper.PyTuple_GetSlice(mapper.Store(object()), IntPtr(1), IntPtr(2)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)



suite = makesuite(
    PyTuple_Type_Test,
    TupleTest,
)

if __name__ == '__main__':
    run(suite)
