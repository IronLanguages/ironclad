
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import CreateTypes, OffsetPtr

from System import GC, IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, CPython_destructor_Delegate, Python25Mapper, PythonMapper
from Ironclad.Structs import PyObject, PyListObject, PyTypeObject
from IronPython.Hosting import PythonEngine



class Python25Mapper_PyList_Type_Test(unittest.TestCase):

    def testPyList_Type(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyList_Type", typeBlock)
            self.assertEquals(mapper.PyList_Type, typeBlock, "type address not stored")
            self.assertEquals(mapper.Retrieve(typeBlock), list, "type not mapped")
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def testPyListTypeField_tp_dealloc(self):
        calls = []
        class MyPM(Python25Mapper):
            def PyList_Dealloc(self, listPtr):
                calls.append(listPtr)
        
        engine = PythonEngine()
        mapper = MyPM(engine)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyList_Type", typeBlock)
            GC.Collect() # this will make the function pointers invalid if we forgot to store references to the delegates

            deallocFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
            deallocFP = CPyMarshal.ReadPtr(deallocFPPtr)
            deallocDgt = Marshal.GetDelegateForFunctionPointer(deallocFP, CPython_destructor_Delegate)
            deallocDgt(IntPtr(12345))
            self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def testPyListTypeField_tp_free(self):
        calls = []
        class MyPM(Python25Mapper):
            def PyObject_Free(self, listPtr):
                calls.append(listPtr)
        
        engine = PythonEngine()
        mapper = MyPM(engine)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyList_Type", typeBlock)
            GC.Collect() # this will make the function pointers invalid if we forgot to store references to the delegates

            freeFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_free"))
            freeFP = CPyMarshal.ReadPtr(freeFPPtr)
            freeDgt = Marshal.GetDelegateForFunctionPointer(freeFP, CPython_destructor_Delegate)
            freeDgt(IntPtr(12345))
            self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        finally:
            Marshal.FreeHGlobal(typeBlock)
        

    def testPyList_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], frees))
        
        calls = []
        def CustomFree(ptr):
            calls.append(ptr)
        freeDgt = PythonMapper.PyObject_Free_Delegate(CustomFree)
        freeFP = Marshal.GetFunctionPointerForDelegate(freeDgt)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyList_Type", typeBlock)
            freeFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_free"))
            CPyMarshal.WritePtr(freeFPPtr, freeFP)
            
            listPtr = mapper.Store([1, 2, 3])
            itemPtrs = []
            dataStore = CPyMarshal.ReadPtr(OffsetPtr(listPtr, Marshal.OffsetOf(PyListObject, "ob_item")))
            for _ in range(3):
                itemPtrs.append(CPyMarshal.ReadPtr(dataStore))
                dataStore = OffsetPtr(dataStore, CPyMarshal.PtrSize)
            
            mapper.PyList_Dealloc(listPtr)
            
            for itemPtr in itemPtrs:
                self.assertEquals(itemPtr in frees, True, "did not decref item")
                self.assertRaises(KeyError, lambda: mapper.RefCount(itemPtr))
            self.assertEquals(calls, [listPtr], "did not call type's free function")
            mapper.PyObject_Free(listPtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)
        
        
    def testStoreList(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        
        listPtr = mapper.Store([1, 2, 3])
        try:
            typePtr = CPyMarshal.ReadPtr(OffsetPtr(listPtr, Marshal.OffsetOf(PyObject, "ob_type")))
            self.assertEquals(typePtr, mapper.PyList_Type, "wrong type")

            dataStore = CPyMarshal.ReadPtr(OffsetPtr(listPtr, Marshal.OffsetOf(PyListObject, "ob_item")))
            for i in range(1, 4):
                self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtr(dataStore)), i, "contents not stored")
                self.assertEquals(mapper.RefCount(CPyMarshal.ReadPtr(dataStore)), 1, "bad refcount for items")
                dataStore = OffsetPtr(dataStore, CPyMarshal.PtrSize)
        finally:
            mapper.DecRef(listPtr)
            deallocTypes()


class Python25Mapper_PyList_Functions_Test(unittest.TestCase):
    
    def testPyList_New_ZeroLength(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        
        listPtr = mapper.PyList_New(0)
        try:
            self.assertEquals(allocs, [(listPtr, Marshal.SizeOf(PyListObject))], "bad alloc")

            listStruct = Marshal.PtrToStructure(listPtr, PyListObject)
            self.assertEquals(listStruct.ob_refcnt, 1, "bad refcount")
            self.assertEquals(listStruct.ob_type, mapper.PyList_Type, "bad type")
            self.assertEquals(listStruct.ob_size, 0, "bad ob_size")
            self.assertEquals(listStruct.ob_item, IntPtr.Zero, "bad data pointer")
            self.assertEquals(listStruct.allocated, 0, "bad allocated")
            self.assertEquals(mapper.Retrieve(listPtr), [], "mapped to wrong object")
        finally:
            mapper.DecRef(listPtr)
            deallocTypes()
    
    
    def testPyList_New_NonZeroLength(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        
        SIZE = 27
        listPtr = mapper.PyList_New(SIZE)
        try:
            listStruct = Marshal.PtrToStructure(listPtr, PyListObject)
            self.assertEquals(listStruct.ob_refcnt, 1, "bad refcount")
            self.assertEquals(listStruct.ob_type, mapper.PyList_Type, "bad type")
            self.assertEquals(listStruct.ob_size, SIZE, "bad ob_size")
            self.assertEquals(listStruct.allocated, SIZE, "bad allocated")
            
            dataPtr = listStruct.ob_item
            self.assertNotEquals(dataPtr, IntPtr.Zero, "failed to allocate space for data")
            
            expectedAllocs = [(dataPtr, (SIZE * CPyMarshal.PtrSize)), (listPtr, Marshal.SizeOf(PyListObject))]
            self.assertEquals(set(allocs), set(expectedAllocs), "allocated wrong")
            
            # as we test that the list is not-yet-filled, we fill it, so we can decref it safely
            objPtr = mapper.Store(object())
            for _ in range(SIZE):
                self.assertEquals(CPyMarshal.ReadPtr(dataPtr), IntPtr.Zero, "failed to zero memory")
                CPyMarshal.WritePtr(dataPtr, objPtr)
                mapper.IncRef(objPtr)
                dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
            mapper.DecRef(objPtr)
            
        finally:
            mapper.DecRef(listPtr)
            deallocTypes()
    
    
    def testPyList_Append(self):
        allocs = []
        deallocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, deallocs))
        deallocTypes = CreateTypes(mapper)
        
        listPtr = mapper.PyList_New(0)
        try:
            self.assertEquals(allocs, [(listPtr, Marshal.SizeOf(PyListObject))], "bad alloc")

            def GetDataPtr():
                ob_item = OffsetPtr(listPtr, Marshal.OffsetOf(PyListObject, "ob_item"))
                return CPyMarshal.ReadPtr(ob_item)

            item1 = object()
            item2 = object()
            itemPtr1 = mapper.Store(item1)
            itemPtr2 = mapper.Store(item2)
            try:
                try:
                    self.assertEquals(mapper.PyList_Append(listPtr, itemPtr1), 0, "failed to report success")
                    self.assertEquals(len(allocs), 4, "didn't allocate memory for data store (list; item1; item2; data store comes 4th)")

                    dataPtrAfterFirstAppend = GetDataPtr()
                    self.assertEquals(allocs[3], (dataPtrAfterFirstAppend, CPyMarshal.PtrSize), "allocated wrong amount of memory")
                    self.assertEquals(CPyMarshal.ReadPtr(dataPtrAfterFirstAppend), itemPtr1, "failed to fill memory")
                    self.assertEquals(mapper.RefCount(itemPtr1), 2, "failed to incref new contents")
                    self.assertEquals(mapper.Retrieve(listPtr), [item1], "retrieved wrong list")
                finally:
                    # ensure that references are not lost when reallocing data
                    mapper.DecRef(itemPtr1)

                self.assertEquals(mapper.PyList_Append(listPtr, itemPtr2), 0, "failed to report success")
                self.assertEquals(len(allocs), 5, "didn't allocate memory for new, larger data store")
                self.assertEquals(deallocs, [dataPtrAfterFirstAppend])

                dataPtrAfterSecondAppend = GetDataPtr()
                self.assertEquals(allocs[4], (dataPtrAfterSecondAppend, (CPyMarshal.PtrSize * 2)), 
                                  "allocated wrong amount of memory")
                self.assertEquals(CPyMarshal.ReadPtr(dataPtrAfterSecondAppend), itemPtr1, 
                                  "failed to keep reference to first item")
                self.assertEquals(CPyMarshal.ReadPtr(OffsetPtr(dataPtrAfterSecondAppend, CPyMarshal.PtrSize)), itemPtr2, 
                                  "failed to keep reference to first item")
                self.assertEquals(mapper.RefCount(itemPtr1), 1, "wrong refcount for item existing only in list")
                self.assertEquals(mapper.RefCount(itemPtr2), 2, "wrong refcount newly-added item")
                self.assertEquals(mapper.Retrieve(listPtr), [item1, item2], "retrieved wrong list")
            finally:
                mapper.DecRef(itemPtr2)
        finally:
            mapper.DecRef(listPtr)
            deallocTypes()
        
        
    def testDeleteList(self):
        deallocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], deallocs))
        deallocTypes = CreateTypes(mapper)
        
        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        
        listPtr = mapper.PyList_New(0)
        try:
            mapper.PyList_Append(listPtr, itemPtr1)
            mapper.PyList_Append(listPtr, itemPtr2)

            mapper.DecRef(itemPtr1)
            mapper.DecRef(itemPtr2)

            self.assertEquals(len(deallocs), 1, "should have deallocated original data block only at this point")
            dataStore = CPyMarshal.ReadPtr(OffsetPtr(listPtr, Marshal.OffsetOf(PyListObject, "ob_item")))

            mapper.DecRef(listPtr)
            listDeallocs = deallocs[1:]
            self.assertEquals(len(listDeallocs), 4, "should dealloc list object; data store; both items")
            expectedDeallocs = [listPtr, dataStore, itemPtr1, itemPtr2]
            self.assertEquals(set(listDeallocs), set(expectedDeallocs), "deallocated wrong stuff")
        finally:        
            deallocTypes()
        
        
    def testPyList_GetSlice(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        
        def TestSlice(originalListPtr, start, stop):
            newListPtr = mapper.PyList_GetSlice(originalListPtr, start, stop)
            try:
                self.assertEquals(mapper.Retrieve(newListPtr), mapper.Retrieve(originalListPtr)[start:stop], "bad slice")
            finally:
                mapper.DecRef(newListPtr)
        
        listPtr = mapper.Store([0, 1, 2, 3, 4, 5, 6, 7])
        try:
            slices = (
                (3, 4), (2, -1), (-5, -4), (5, 200), (999, 1000)
            )
            for (start, stop) in slices:
                TestSlice(listPtr, start, stop)
        finally:
            deallocTypes()
        
        

suite = makesuite(
    Python25Mapper_PyList_Type_Test,
    Python25Mapper_PyList_Functions_Test,
)

if __name__ == '__main__':
    run(suite)