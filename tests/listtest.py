
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes, OffsetPtr, PtrToStructure
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr, Type
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, PythonMapper
from Ironclad.Structs import PyObject, PyListObject, PyTypeObject


class PyList_Type_Test(TypeTestCase):

    def testPyListTypeField_tp_dealloc(self):
        calls = []
        class MyPM(PythonMapper):
            def IC_PyList_Dealloc(self, listPtr):
                calls.append(listPtr)
        
        mapper = MyPM()
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        mapper.RegisterData("PyList_Type", typeBlock)
        gcwait() # this will make the function pointers invalid if we forgot to store references to the delegates

        deallocDgt = CPyMarshal.ReadFunctionPtrField(typeBlock, PyTypeObject, "tp_dealloc", dgt_void_ptr)
        deallocDgt(IntPtr(12345))
        self.assertEqual(calls, [IntPtr(12345)], "wrong calls")
        
        mapper.Dispose()
        Marshal.FreeHGlobal(typeBlock)


    def testPyListTypeField_tp_free(self):
        self.assertUsual_tp_free("PyList_Type")
    
    
    def testPyList_Dealloc(self):
        frees = []
        def CreateMapper():
            return PythonMapper(GetAllocatingTestAllocator([], frees))
        
        itemPtrs = []
        def CreateInstance(mapper, calls):
            listPtr = mapper.Store([1, 2, 3])
            dataStore = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
            for _ in range(3):
                itemPtrs.append(CPyMarshal.ReadPtr(dataStore))
                dataStore = OffsetPtr(dataStore, CPyMarshal.PtrSize)
            return listPtr
    
        def TestConsequences(mapper, listPtr, calls):
            for itemPtr in itemPtrs:
                self.assertEqual(itemPtr in frees, True, "did not decref item")
            self.assertEqual(calls, [('tp_free', listPtr)], "did not call tp_free")
            
        self.assertTypeDeallocWorks("PyList_Type", CreateMapper, CreateInstance, TestConsequences)
    

    def testPyList_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        
        calls = []
        def CustomFree(ptr):
            calls.append(ptr)
            mapper.PyObject_Free(listPtr)
        self.freeDgt = dgt_void_ptr(CustomFree)
        
        CPyMarshal.WriteFunctionPtrField(mapper.PyList_Type, PyTypeObject, "tp_free", self.freeDgt)
        
        listPtr = mapper.Store([1, 2, 3])
        itemPtrs = []
        dataStore = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        for _ in range(3):
            itemPtrs.append(CPyMarshal.ReadPtr(dataStore))
            dataStore = OffsetPtr(dataStore, CPyMarshal.PtrSize)
        
        mapper.IC_PyList_Dealloc(listPtr)
        
        for itemPtr in itemPtrs:
            self.assertEqual(itemPtr in frees, True, "did not decref item")
        self.assertEqual(calls, [listPtr], "did not call type's free function")
        
        mapper.Dispose()
        deallocTypes()
        
        
    @WithMapper
    def testStoreList(self, mapper, _):
        list_ = [1, 2, 3]
        listPtr = mapper.Store(list_)
        self.assertEqual(id(mapper.Retrieve(listPtr)), id(list_))
        
        typePtr = CPyMarshal.ReadPtrField(listPtr, PyObject, "ob_type")
        self.assertEqual(typePtr, mapper.PyList_Type, "wrong type")

        dataStore = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        for i in range(1, 4):
            self.assertEqual(mapper.Retrieve(CPyMarshal.ReadPtr(dataStore)), i, "contents not stored")
            self.assertEqual(mapper.RefCount(CPyMarshal.ReadPtr(dataStore)), 1, "bad refcount for items")
            dataStore = OffsetPtr(dataStore, CPyMarshal.PtrSize)


class ListFunctionsTest(TestCase):
    
    def testPyList_New_ZeroLength(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        listPtr = mapper.PyList_New(IntPtr(0))
        self.assertEqual(allocs, [(listPtr, Marshal.SizeOf(PyListObject()))], "bad alloc")

        listStruct = PtrToStructure(listPtr, PyListObject)
        self.assertEqual(listStruct.ob_refcnt, 1, "bad refcount")
        self.assertEqual(listStruct.ob_type, mapper.PyList_Type, "bad type")
        self.assertEqual(listStruct.ob_size, 0, "bad ob_size")
        self.assertEqual(listStruct.ob_item, IntPtr.Zero, "bad data pointer")
        self.assertEqual(listStruct.allocated, 0, "bad allocated")
        self.assertEqual(mapper.Retrieve(listPtr), [], "mapped to wrong object")
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyList_New_NonZeroLength(self):
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]
        
        SIZE = 27
        listPtr = mapper.PyList_New(IntPtr(SIZE))
        
        listStruct = PtrToStructure(listPtr, PyListObject)
        self.assertEqual(listStruct.ob_refcnt, 1, "bad refcount")
        self.assertEqual(listStruct.ob_type, mapper.PyList_Type, "bad type")
        self.assertEqual(listStruct.ob_size, SIZE, "bad ob_size")
        self.assertEqual(listStruct.allocated, SIZE, "bad allocated")
        
        dataPtr = listStruct.ob_item
        self.assertNotEqual(dataPtr, IntPtr.Zero, "failed to allocate space for data")
        
        expectedAllocs = [(dataPtr, (SIZE * CPyMarshal.PtrSize)), (listPtr, Marshal.SizeOf(PyListObject()))]
        self.assertEqual(allocs, expectedAllocs, "allocated wrong")
        
        for _ in range(SIZE):
            self.assertEqual(CPyMarshal.ReadPtr(dataPtr), IntPtr.Zero, "failed to zero memory")
            dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyList_Append(self):
        allocs = []
        deallocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, deallocs))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        listPtr = mapper.PyList_New(IntPtr(0))
        self.assertEqual(allocs, [(listPtr, Marshal.SizeOf(PyListObject()))], "bad alloc")

        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        
        self.assertEqual(mapper.PyList_Append(listPtr, itemPtr1), 0, "failed to report success")
        self.assertEqual(len(allocs), 4, "didn't allocate memory for data store (list; item1; item2; data store comes 4th)")

        dataPtrAfterFirstAppend = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        self.assertEqual(allocs[3], (dataPtrAfterFirstAppend, CPyMarshal.PtrSize), "allocated wrong amount of memory")
        self.assertEqual(CPyMarshal.ReadPtr(dataPtrAfterFirstAppend), itemPtr1, "failed to fill memory")
        self.assertEqual(mapper.RefCount(itemPtr1), 2, "failed to incref new contents")
        self.assertEqual(mapper.Retrieve(listPtr), [item1], "retrieved wrong list")
        
        # make refcount 1, to prove that references are not lost when reallocing data
        mapper.DecRef(itemPtr1)

        self.assertEqual(mapper.PyList_Append(listPtr, itemPtr2), 0, "failed to report success")
        self.assertEqual(len(allocs), 5, "didn't allocate memory for new, larger data store")
        self.assertEqual(deallocs, [dataPtrAfterFirstAppend])

        dataPtrAfterSecondAppend = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        self.assertEqual(allocs[4], (dataPtrAfterSecondAppend, (CPyMarshal.PtrSize * 2)), 
                          "allocated wrong amount of memory")
        self.assertEqual(CPyMarshal.ReadPtr(dataPtrAfterSecondAppend), itemPtr1, 
                          "failed to keep reference to first item")
        self.assertEqual(CPyMarshal.ReadPtr(OffsetPtr(dataPtrAfterSecondAppend, CPyMarshal.PtrSize)), itemPtr2, 
                          "failed to keep reference to first item")
        self.assertEqual(mapper.RefCount(itemPtr1), 1, "wrong refcount for item existing only in list")
        self.assertEqual(mapper.RefCount(itemPtr2), 2, "wrong refcount newly-added item")
        self.assertEqual(mapper.Retrieve(listPtr), [item1, item2], "retrieved wrong list")
        
        mapper.Dispose()
        deallocTypes()
    
    
    @WithMapper
    def testPyList_Append_NotList(self, mapper, _):
        notListPtr = mapper.Store(object())
        self.assertEqual(mapper.PyList_Append(notListPtr, mapper.Store(object())), -1)
        self.assertMapperHasError(mapper, TypeError)
    
        
    @WithMapper
    def testPyList_SetItem_RefCounting(self, mapper, _):
        listPtr = mapper.PyList_New(IntPtr(4))
        itemPtr1 = mapper.Store(object())
        itemPtr2 = mapper.Store(object())
        
        self.assertEqual(mapper.PyList_SetItem(listPtr, IntPtr(0), itemPtr1), 0, "returned error code")
        self.assertEqual(mapper.RefCount(itemPtr1), 1, "reference count wrong")
        
        mapper.IncRef(itemPtr1) # reference was stolen a couple of lines ago
        self.assertEqual(mapper.PyList_SetItem(listPtr, IntPtr(0), itemPtr2), 0, "returned error code")
        self.assertEqual(mapper.RefCount(itemPtr1), 1, "failed to decref replacee")
        self.assertEqual(mapper.RefCount(itemPtr2), 1, "reference count wrong")
        
        mapper.IncRef(itemPtr2) # reference was stolen a couple of lines ago
        self.assertEqual(mapper.PyList_SetItem(listPtr, IntPtr(0), IntPtr.Zero), 0, "returned error code")
        self.assertEqual(mapper.RefCount(itemPtr2), 1, "failed to decref replacee")


    @WithMapper
    def testPyList_SetItem_CompleteList(self, mapper, _):
        listPtr = mapper.PyList_New(IntPtr(4))
        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        mapper.IncRef(itemPtr1)
        mapper.IncRef(itemPtr2)
        
        mapper.PyList_SetItem(listPtr, IntPtr(0), itemPtr1)
        mapper.PyList_SetItem(listPtr, IntPtr(1), itemPtr2)
        mapper.PyList_SetItem(listPtr, IntPtr(2), itemPtr1)
        mapper.PyList_SetItem(listPtr, IntPtr(3), itemPtr2)
        
        self.assertEqual(mapper.Retrieve(listPtr), [item1, item2, item1, item2], "lists not synchronised")


    @WithMapper
    def testPyList_SetItem_Failures(self, mapper, _):
        objPtr = mapper.Store(object())
        listPtr = mapper.PyList_New(IntPtr(4))
        
        mapper.IncRef(objPtr) # failing PyList_SetItem will still steal a reference
        self.assertEqual(mapper.PyList_SetItem(objPtr, IntPtr(1), objPtr), -1, "did not detect non-list")
        self.assertEqual(mapper.RefCount(objPtr), 1, "reference not stolen")
        
        mapper.IncRef(objPtr)
        self.assertEqual(mapper.PyList_SetItem(listPtr, IntPtr(4), objPtr), -1, "did not detect set outside bounds")
        self.assertEqual(mapper.RefCount(objPtr), 1, "reference not stolen")
        
        mapper.IncRef(objPtr)
        self.assertEqual(mapper.PyList_SetItem(IntPtr.Zero, IntPtr(1), objPtr), -1, "did not detect null list")
        self.assertEqual(mapper.RefCount(objPtr), 1, "reference not stolen")
    
        # list still contains uninitialised values
        self.assertRaises(ValueError, mapper.Retrieve, listPtr)


    @WithMapper
    def testPyList_SetItem_PreexistingIpyList(self, mapper, _):
        item = object()
        itemPtr = mapper.Store(item)
        listPtr = mapper.Store([1, 2, 3])
        
        self.assertEqual(mapper.PyList_SetItem(listPtr, IntPtr(1), itemPtr), 0, "did not report success")
        self.assertEqual(mapper.Retrieve(listPtr), [1, item, 3])


    @WithMapper
    def testRetrieveListContainingItself(self, mapper, _):
        listPtr = mapper.PyList_New(IntPtr(1))
        
        mapper.PyList_SetItem(listPtr, IntPtr(0), listPtr)
        self.assertEqual(mapper.RefCount(listPtr), 1, "list should be the only thing owning a reference to it")
        realList = mapper.Retrieve(listPtr)
        self.assertEqual(len(realList), 1, "wrong size list")
        anotherReferenceToRealList = realList[0]
        self.assertEqual(realList is anotherReferenceToRealList, True, "wrong list contents")


    @WithMapper
    def testRetrieveListContainingItselfIndirectly(self, mapper, _):
        listPtr1 = mapper.PyList_New(IntPtr(1))
        listPtr2 = mapper.PyList_New(IntPtr(1))
        listPtr3 = mapper.PyList_New(IntPtr(1))
        
        mapper.PyList_SetItem(listPtr1, IntPtr(0), listPtr2)
        mapper.PyList_SetItem(listPtr2, IntPtr(0), listPtr3)
        mapper.PyList_SetItem(listPtr3, IntPtr(0), listPtr1)
        
        realList1 = mapper.Retrieve(listPtr1)
        realList2 = mapper.Retrieve(listPtr2)
        realList3 = mapper.Retrieve(listPtr3)
        
        anotherReferenceToRealList1 = realList3[0]
        anotherReferenceToRealList2 = realList1[0]
        anotherReferenceToRealList3 = realList2[0]
        
        self.assertEqual(realList1 is anotherReferenceToRealList1, True, "wrong list contents")
        self.assertEqual(realList2 is anotherReferenceToRealList2, True, "wrong list contents")
        self.assertEqual(realList3 is anotherReferenceToRealList3, True, "wrong list contents")


    def testDeleteList(self):
        deallocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], deallocs))
        deallocTypes = CreateTypes(mapper)
        
        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        
        listPtr = mapper.PyList_New(IntPtr(0))
        
        mapper.PyList_Append(listPtr, itemPtr1)
        mapper.PyList_Append(listPtr, itemPtr2)

        mapper.DecRef(itemPtr1)
        mapper.DecRef(itemPtr2)

        self.assertEqual(len(deallocs), 1, "should have deallocated original data block only at this point")
        dataStore = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")

        mapper.DecRef(listPtr)
        listDeallocs = deallocs[1:]
        self.assertEqual(len(listDeallocs), 4, "should dealloc list object; data store; both items")
        expectedDeallocs = [listPtr, dataStore, itemPtr1, itemPtr2]
        self.assertEqual(set(listDeallocs), set(expectedDeallocs), "deallocated wrong stuff")
        
        mapper.Dispose()
        deallocTypes()
        
        
    @WithMapper
    def testPyList_GetSlice(self, mapper, _):
        # this will fail badly when we fix API signednesses
        def TestSlice(originalListPtr, start, stop):
            newListPtr = mapper.PyList_GetSlice(originalListPtr, IntPtr(start), IntPtr(stop))
            self.assertMapperHasError(mapper, None)
            self.assertEqual(mapper.Retrieve(newListPtr), mapper.Retrieve(originalListPtr)[start:stop], "bad slice")
            mapper.DecRef(newListPtr)
        
        listPtr = mapper.Store([0, 1, 2, 3, 4, 5, 6, 7])
        slices = (
            (3, 4), (3, 0), (5, 200), (999, 1000)
        )
        for (start, stop) in slices:
            TestSlice(listPtr, start, stop)
            
         
    @WithMapper
    def testPyList_GetSlice_error(self, mapper, _):
        self.assertEqual(mapper.PyList_GetSlice(mapper.Store(object()), IntPtr(1), IntPtr(2)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        
    @WithMapper
    def testPyList_GetItem(self, mapper, _):
        listPtr = mapper.Store([1, 2, 3])
        for i in range(3):
            result = mapper.Retrieve(mapper.PyList_GetItem(listPtr, IntPtr(i)))
            self.assertEqual(result, i + 1)
        
        notListPtr = mapper.Store(object())
        self.assertEqual(mapper.PyList_GetItem(notListPtr, IntPtr(0)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
    
    
    @WithMapper
    def testPyList_AsTuple(self, mapper, _):
        tPtr = mapper.PyList_AsTuple(mapper.Store([1, 2, 3]))
        self.assertEqual(mapper.Retrieve(tPtr), (1, 2, 3))
        
        
suite = makesuite(
    PyList_Type_Test,
    ListFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
