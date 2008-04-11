
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import CreateTypes, OffsetPtr

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyListObject, PyTypeObject
from IronPython.Hosting import PythonEngine
from Unmanaged.msvcrt import fclose, fread



class Python25Mapper_PyList_Test(unittest.TestCase):

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
    
    
    def testPyList_New_ZeroLength(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        
        listPtr = mapper.PyList_New(0)
        self.assertEquals(allocs, [(listPtr, Marshal.SizeOf(PyListObject))], "bad alloc")
        
        listStruct = Marshal.PtrToStructure(listPtr, PyListObject)
        self.assertEquals(listStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(listStruct.ob_type, mapper.PyList_Type, "bad type")
        self.assertEquals(listStruct.ob_size, 0, "bad ob_size")
        self.assertEquals(listStruct.ob_item, IntPtr.Zero, "bad data pointer")
        self.assertEquals(listStruct.allocated, 0, "bad allocated")
        self.assertEquals(mapper.Retrieve(listPtr), [], "mapped to wrong object")
        
        mapper.DecRef(listPtr)
        deallocTypes()
    
    
    def testPyList_New_NonZeroLength(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        
        self.assertRaises(NotImplementedError, mapper.PyList_New, 27)
        
        deallocTypes()
    
    
    def testPyList_Append(self):
        allocs = []
        deallocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, deallocs))
        deallocTypes = CreateTypes(mapper)
        
        listPtr = mapper.PyList_New(0)
        self.assertEquals(allocs, [(listPtr, Marshal.SizeOf(PyListObject))], "bad alloc")
        
        def GetDataPtr():
            ob_item = OffsetPtr(listPtr, Marshal.OffsetOf(PyListObject, "ob_item"))
            return CPyMarshal.ReadPtr(ob_item)
        
        item1 = object()
        item2 = object()
        itemPtr1 = mapper.Store(item1)
        itemPtr2 = mapper.Store(item2)
        
        self.assertEquals(mapper.PyList_Append(listPtr, itemPtr1), 0, "failed to report success")
        self.assertEquals(len(allocs), 4, "didn't allocate memory for data store (list; item1; item2; data store comes 4th)")
        
        dataPtrAfterFirstAppend = GetDataPtr()
        self.assertEquals(allocs[3], (dataPtrAfterFirstAppend, CPyMarshal.PtrSize), "allocated wrong amount of memory")
        self.assertEquals(CPyMarshal.ReadPtr(dataPtrAfterFirstAppend), itemPtr1, "failed to fill memory")
        self.assertEquals(mapper.RefCount(itemPtr1), 2, "failed to incref new contents")
        self.assertEquals(mapper.Retrieve(listPtr), [item1], "retrieved wrong list")
        
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
        
        mapper.DecRef(itemPtr2)
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
        
        deallocTypes()
        
        
    

suite = makesuite(
    Python25Mapper_PyList_Test,
)

if __name__ == '__main__':
    run(suite)