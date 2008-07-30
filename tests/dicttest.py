
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject




class DictTest(TestCase):

    def testPyDict_New(self):
        allocs = []
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
    
        dictPtr = mapper.PyDict_New()
        self.assertEquals(mapper.RefCount(dictPtr), 1, "bad refcount")
        self.assertEquals(allocs, [(dictPtr, Marshal.SizeOf(PyObject))], "did not allocate as expected")
        self.assertEquals(CPyMarshal.ReadPtrField(dictPtr, PyObject, "ob_type"), mapper.PyDict_Type, "wrong type")
        dictObj = mapper.Retrieve(dictPtr)
        self.assertEquals(dictObj, {}, "retrieved unexpected value")
        
        mapper.DecRef(dictPtr)
        self.assertRaises(KeyError, lambda: mapper.RefCount(dictPtr))
        self.assertEquals(frees, [dictPtr], "did not release memory")
        mapper.Dispose()
        deallocTypes()
        

    def testStoreDictCreatesDictType(self):
        mapper = Python25Mapper()
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        mapper.SetData("PyDict_Type", typeBlock)
        
        dictPtr = mapper.Store({0: 1, 2: 3})
        self.assertEquals(CPyMarshal.ReadPtrField(dictPtr, PyObject, "ob_type"), typeBlock, "wrong type")
        
        mapper.Dispose()
        Marshal.FreeHGlobal(typeBlock)


    def testPyDict_Size(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        dict0 = mapper.Store({})
        dict3 = mapper.Store({1:2, 3:4, 5:6})
        
        self.assertEquals(mapper.PyDict_Size(dict0), 0, "wrong")
        self.assertEquals(mapper.PyDict_Size(dict3), 3, "wrong")
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_GetItemStringSuccess(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({"abcde": 12345})
        
        itemPtr = mapper.PyDict_GetItemString(dictPtr, "abcde")
        self.assertEquals(mapper.Retrieve(itemPtr), 12345, "failed to get item")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "something is wrong")
        mapper.FreeTemps()
        self.assertRaises(KeyError, lambda: mapper.RefCount(itemPtr))
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_GetItemStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({"abcde": 12345})
        
        itemPtr = mapper.PyDict_GetItemString(dictPtr, "bwahahaha!")
        self.assertEquals(itemPtr, IntPtr.Zero, "bad return for missing key")
        self.assertEquals(mapper.LastException, None, "should not set exception")
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_GetItemSuccess(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({12345: 67890})
        
        itemPtr = mapper.PyDict_GetItem(dictPtr, mapper.Store(12345))
        self.assertEquals(mapper.Retrieve(itemPtr), 67890, "failed to get item")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "something is wrong")
        mapper.FreeTemps()
        self.assertRaises(KeyError, lambda: mapper.RefCount(itemPtr))
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_GetItemFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({12345: 67890})
        
        itemPtr = mapper.PyDict_GetItem(dictPtr, mapper.Store("something"))
        self.assertEquals(itemPtr, IntPtr.Zero, "bad return for missing key")
        self.assertEquals(mapper.LastException, None, "should not set exception")
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_SetItem(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        _dict = {}
        dictPtr = mapper.Store(_dict)
        keyPtr = mapper.Store(123)
        itemPtr = mapper.Store(456)
        self.assertEquals(mapper.PyDict_SetItem(dictPtr, keyPtr, itemPtr), 0, "reported failure")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "does not need to incref item")
        self.assertEquals(_dict, {123: 456}, "failed")
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_SetItem_Unhashable(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        _dict = {}
        dictPtr = mapper.Store(_dict)
        keyPtr = mapper.Store({})
        itemPtr = mapper.Store(456)
        self.assertEquals(mapper.PyDict_SetItem(dictPtr, keyPtr, itemPtr), -1, "failed to report failure")
        self.assertEquals(_dict, {}, 'dictionary changed')
        
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(TypeError, KindaConvertError)
        
        mapper.Dispose()
        deallocTypes()
        

    def testPyDict_SetItemString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        _dict = {}
        dictPtr = mapper.Store(_dict)
        itemPtr = mapper.Store(123)
        self.assertEquals(mapper.PyDict_SetItemString(dictPtr, 'blob', itemPtr), 0, "reported failure")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "does not need to incref item")
        self.assertEquals(_dict, {'blob': 123}, "failed")
        
        mapper.Dispose()
        deallocTypes()


    def testPyDict_SetItemString_UnknownType(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        
        _dict = {}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_SetItemString(dictPtr, 'klass', typePtr), 0, "reported failure")
        klass = _dict['klass']
        self.assertEquals(klass.__name__, 'klass', "failed")
        
        mapper.Dispose()
        deallocType()
        deallocTypes()



suite = makesuite(
    DictTest,
)

if __name__ == '__main__':
    run(suite)