
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, Python25Mapper
from Ironclad.Structs import PyObject, PyListObject, PyTypeObject



class PyList_Type_Test(TypeTestCase):

    def testPyListTypeField_tp_dealloc(self):
        calls = []
        class MyPM(Python25Mapper):
            def IC_PyList_Dealloc(self, listPtr):
                calls.append(listPtr)
        
        mapper = MyPM()
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        mapper.SetData("PyList_Type", typeBlock)
        gcwait() # this will make the function pointers invalid if we forgot to store references to the delegates

        deallocDgt = CPyMarshal.ReadFunctionPtrField(typeBlock, PyTypeObject, "tp_dealloc", dgt_void_ptr)
        deallocDgt(IntPtr(12345))
        self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        
        mapper.Dispose()
        Marshal.FreeHGlobal(typeBlock)


    def testPyListTypeField_tp_free(self):
        self.assertUsual_tp_free("PyList_Type")
    
    
    def testPyList_Dealloc(self):
        frees = []
        def CreateMapper():
            return Python25Mapper(GetAllocatingTestAllocator([], frees))
        
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
                self.assertEquals(itemPtr in frees, True, "did not decref item")
            self.assertEquals(calls, [('tp_free', listPtr)], "did not call tp_free")
            
        self.assertTypeDeallocWorks("PyList_Type", CreateMapper, CreateInstance, TestConsequences)
    

    def testPyList_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
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
            self.assertEquals(itemPtr in frees, True, "did not decref item")
        self.assertEquals(calls, [listPtr], "did not call type's free function")
        
        mapper.Dispose()
        deallocTypes()
        
        
    @WithMapper
    def testStoreList(self, mapper, _):
        list_ = [1, 2, 3]
        listPtr = mapper.Store(list_)
        self.assertEquals(id(mapper.Retrieve(listPtr)), id(list_))
        
        typePtr = CPyMarshal.ReadPtrField(listPtr, PyObject, "ob_type")
        self.assertEquals(typePtr, mapper.PyList_Type, "wrong type")

        dataStore = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        for i in range(1, 4):
            self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtr(dataStore)), i, "contents not stored")
            self.assertEquals(mapper.RefCount(CPyMarshal.ReadPtr(dataStore)), 1, "bad refcount for items")
            dataStore = OffsetPtr(dataStore, CPyMarshal.PtrSize)


class ListFunctionsTest(TestCase):
    
    def testPyList_New_ZeroLength(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        listPtr = mapper.PyList_New(0)
        self.assertEquals(allocs, [(listPtr, Marshal.SizeOf(PyListObject))], "bad alloc")

        listStruct = Marshal.PtrToStructure(listPtr, PyListObject)
        self.assertEquals(listStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(listStruct.ob_type, mapper.PyList_Type, "bad type")
        self.assertEquals(listStruct.ob_size, 0, "bad ob_size")
        self.assertEquals(listStruct.ob_item, IntPtr.Zero, "bad data pointer")
        self.assertEquals(listStruct.allocated, 0, "bad allocated")
        self.assertEquals(mapper.Retrieve(listPtr), [], "mapped to wrong object")
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyList_New_NonZeroLength(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        del allocs[:]
        
        SIZE = 27
        listPtr = mapper.PyList_New(SIZE)
        
        listStruct = Marshal.PtrToStructure(listPtr, PyListObject)
        self.assertEquals(listStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(listStruct.ob_type, mapper.PyList_Type, "bad type")
        self.assertEquals(listStruct.ob_size, SIZE, "bad ob_size")
        self.assertEquals(listStruct.allocated, SIZE, "bad allocated")
        
        dataPtr = listStruct.ob_item
        self.assertNotEquals(dataPtr, IntPtr.Zero, "failed to allocate space for data")
        
        expectedAllocs = [(dataPtr, (SIZE * CPyMarshal.PtrSize)), (listPtr, Marshal.SizeOf(PyListObject))]
        self.assertEquals(set(allocs), set(expectedAllocs), "allocated wrong")
        
        for _ in range(SIZE):
            self.assertEquals(CPyMarshal.ReadPtr(dataPtr), IntPtr.Zero, "failed to zero memory")
            dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyList_Append(self):
        allocs = []
        deallocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, deallocs))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        listPtr = mapper.PyList_New(0)
        self.assertEquals(allocs, [(listPtr, Marshal.SizeOf(PyListObject))], "bad alloc")

        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        
        self.assertEquals(mapper.PyList_Append(listPtr, itemPtr1), 0, "failed to report success")
        self.assertEquals(len(allocs), 4, "didn't allocate memory for data store (list; item1; item2; data store comes 4th)")

        dataPtrAfterFirstAppend = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        self.assertEquals(allocs[3], (dataPtrAfterFirstAppend, CPyMarshal.PtrSize), "allocated wrong amount of memory")
        self.assertEquals(CPyMarshal.ReadPtr(dataPtrAfterFirstAppend), itemPtr1, "failed to fill memory")
        self.assertEquals(mapper.RefCount(itemPtr1), 2, "failed to incref new contents")
        self.assertEquals(mapper.Retrieve(listPtr), [item1], "retrieved wrong list")
        
        # make refcount 1, to prove that references are not lost when reallocing data
        mapper.DecRef(itemPtr1)

        self.assertEquals(mapper.PyList_Append(listPtr, itemPtr2), 0, "failed to report success")
        self.assertEquals(len(allocs), 5, "didn't allocate memory for new, larger data store")
        self.assertEquals(deallocs, [dataPtrAfterFirstAppend])

        dataPtrAfterSecondAppend = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")
        self.assertEquals(allocs[4], (dataPtrAfterSecondAppend, (CPyMarshal.PtrSize * 2)), 
                          "allocated wrong amount of memory")
        self.assertEquals(CPyMarshal.ReadPtr(dataPtrAfterSecondAppend), itemPtr1, 
                          "failed to keep reference to first item")
        self.assertEquals(CPyMarshal.ReadPtr(OffsetPtr(dataPtrAfterSecondAppend, CPyMarshal.PtrSize)), itemPtr2, 
                          "failed to keep reference to first item")
        self.assertEquals(mapper.RefCount(itemPtr1), 1, "wrong refcount for item existing only in list")
        self.assertEquals(mapper.RefCount(itemPtr2), 2, "wrong refcount newly-added item")
        self.assertEquals(mapper.Retrieve(listPtr), [item1, item2], "retrieved wrong list")
        
        mapper.Dispose()
        deallocTypes()
        
        
    @WithMapper
    def testPyList_SetItem_RefCounting(self, mapper, _):
        listPtr = mapper.PyList_New(4)
        itemPtr1 = mapper.Store(object())
        itemPtr2 = mapper.Store(object())
        
        self.assertEquals(mapper.PyList_SetItem(listPtr, 0, itemPtr1), 0, "returned error code")
        self.assertEquals(mapper.RefCount(itemPtr1), 1, "reference count wrong")
        
        mapper.IncRef(itemPtr1) # reference was stolen a couple of lines ago
        self.assertEquals(mapper.PyList_SetItem(listPtr, 0, itemPtr2), 0, "returned error code")
        self.assertEquals(mapper.RefCount(itemPtr1), 1, "failed to decref replacee")
        self.assertEquals(mapper.RefCount(itemPtr2), 1, "reference count wrong")
        
        mapper.IncRef(itemPtr2) # reference was stolen a couple of lines ago
        self.assertEquals(mapper.PyList_SetItem(listPtr, 0, IntPtr.Zero), 0, "returned error code")
        self.assertEquals(mapper.RefCount(itemPtr2), 1, "failed to decref replacee")


    @WithMapper
    def testPyList_SetItem_CompleteList(self, mapper, _):
        listPtr = mapper.PyList_New(4)
        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        mapper.IncRef(itemPtr1)
        mapper.IncRef(itemPtr2)
        
        mapper.PyList_SetItem(listPtr, 0, itemPtr1)
        mapper.PyList_SetItem(listPtr, 1, itemPtr2)
        mapper.PyList_SetItem(listPtr, 2, itemPtr1)
        mapper.PyList_SetItem(listPtr, 3, itemPtr2)
        
        self.assertEquals(mapper.Retrieve(listPtr), [item1, item2, item1, item2], "lists not synchronised")


    @WithMapper
    def testPyList_SetItem_Failures(self, mapper, _):
        objPtr = mapper.Store(object())
        listPtr = mapper.PyList_New(4)
        
        mapper.IncRef(objPtr) # failing PyList_SetItem will still steal a reference
        self.assertEquals(mapper.PyList_SetItem(objPtr, 1, objPtr), -1, "did not detect non-list")
        self.assertEquals(mapper.RefCount(objPtr), 1, "reference not stolen")
        
        mapper.IncRef(objPtr)
        self.assertEquals(mapper.PyList_SetItem(listPtr, 4, objPtr), -1, "did not detect set outside bounds")
        self.assertEquals(mapper.RefCount(objPtr), 1, "reference not stolen")
        
        mapper.IncRef(objPtr)
        self.assertEquals(mapper.PyList_SetItem(IntPtr.Zero, 1, objPtr), -1, "did not detect null list")
        self.assertEquals(mapper.RefCount(objPtr), 1, "reference not stolen")
    
        # list still contains uninitialised values
        self.assertRaises(ValueError, mapper.Retrieve, listPtr)


    @WithMapper
    def testPyList_SetItem_PreexistingIpyList(self, mapper, _):
        item = object()
        itemPtr = mapper.Store(item)
        listPtr = mapper.Store([1, 2, 3])
        
        self.assertEquals(mapper.PyList_SetItem(listPtr, 1, itemPtr), 0, "did not report success")
        self.assertEquals(mapper.Retrieve(listPtr), [1, item, 3])


    @WithMapper
    def testRetrieveListContainingItself(self, mapper, _):
        listPtr = mapper.PyList_New(1)
        
        mapper.PyList_SetItem(listPtr, 0, listPtr)
        self.assertEquals(mapper.RefCount(listPtr), 1, "list should be the only thing owning a reference to it")
        realList = mapper.Retrieve(listPtr)
        self.assertEquals(len(realList), 1, "wrong size list")
        anotherReferenceToRealList = realList[0]
        self.assertEquals(realList is anotherReferenceToRealList, True, "wrong list contents")


    @WithMapper
    def testRetrieveListContainingItselfIndirectly(self, mapper, _):
        listPtr1 = mapper.PyList_New(1)
        listPtr2 = mapper.PyList_New(1)
        listPtr3 = mapper.PyList_New(1)
        
        mapper.PyList_SetItem(listPtr1, 0, listPtr2)
        mapper.PyList_SetItem(listPtr2, 0, listPtr3)
        mapper.PyList_SetItem(listPtr3, 0, listPtr1)
        
        realList1 = mapper.Retrieve(listPtr1)
        realList2 = mapper.Retrieve(listPtr2)
        realList3 = mapper.Retrieve(listPtr3)
        
        anotherReferenceToRealList1 = realList3[0]
        anotherReferenceToRealList2 = realList1[0]
        anotherReferenceToRealList3 = realList2[0]
        
        self.assertEquals(realList1 is anotherReferenceToRealList1, True, "wrong list contents")
        self.assertEquals(realList2 is anotherReferenceToRealList2, True, "wrong list contents")
        self.assertEquals(realList3 is anotherReferenceToRealList3, True, "wrong list contents")


    def testDeleteList(self):
        deallocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], deallocs))
        deallocTypes = CreateTypes(mapper)
        
        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        
        listPtr = mapper.PyList_New(0)
        
        mapper.PyList_Append(listPtr, itemPtr1)
        mapper.PyList_Append(listPtr, itemPtr2)

        mapper.DecRef(itemPtr1)
        mapper.DecRef(itemPtr2)

        self.assertEquals(len(deallocs), 1, "should have deallocated original data block only at this point")
        dataStore = CPyMarshal.ReadPtrField(listPtr, PyListObject, "ob_item")

        mapper.DecRef(listPtr)
        listDeallocs = deallocs[1:]
        self.assertEquals(len(listDeallocs), 4, "should dealloc list object; data store; both items")
        expectedDeallocs = [listPtr, dataStore, itemPtr1, itemPtr2]
        self.assertEquals(set(listDeallocs), set(expectedDeallocs), "deallocated wrong stuff")
        
        mapper.Dispose()
        deallocTypes()
        
        
    @WithMapper
    def testPyList_GetSlice(self, mapper, _):
        # this will fail badly when we fix API signednesses
        def TestSlice(originalListPtr, start, stop):
            newListPtr = mapper.PyList_GetSlice(originalListPtr, start, stop)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(mapper.Retrieve(newListPtr), mapper.Retrieve(originalListPtr)[start:stop], "bad slice")
            mapper.DecRef(newListPtr)
        
        listPtr = mapper.Store([0, 1, 2, 3, 4, 5, 6, 7])
        slices = (
            (3, 4), (3, 0), (5, 200), (999, 1000)
        )
        for (start, stop) in slices:
            TestSlice(listPtr, start, stop)
            
         
    @WithMapper
    def testPyList_GetSlice_error(self, mapper, _):
        self.assertEquals(mapper.PyList_GetSlice(mapper.Store(object()), 1, 2), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        
    @WithMapper
    def testPyList_GetItem(self, mapper, _):
        listPtr = mapper.Store([1, 2, 3])
        for i in range(3):
            result = mapper.Retrieve(mapper.PyList_GetItem(listPtr, i))
            self.assertEquals(result, i + 1)
        
        notListPtr = mapper.Store(object())
        self.assertEquals(mapper.PyList_GetItem(notListPtr, 0), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        
        
suite = makesuite(
    PyList_Type_Test,
    ListFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
