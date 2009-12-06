
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_int_ptrptrptr, PythonMapper
from Ironclad.Structs import PyObject, PyTypeObject


class DictTest(TestCase):

    def testPyDict_New(self):
        allocs = []
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        try:
            del allocs[:]
            dictPtr = mapper.PyDict_New()
            self.assertEquals(mapper.RefCount(dictPtr), 1, "bad refcount")
            self.assertEquals(allocs, [(dictPtr, Marshal.SizeOf(PyObject))], "did not allocate as expected")
            self.assertEquals(CPyMarshal.ReadPtrField(dictPtr, PyObject, "ob_type"), mapper.PyDict_Type, "wrong type")
            dictObj = mapper.Retrieve(dictPtr)
            self.assertEquals(dictObj, {}, "retrieved unexpected value")
            
            mapper.DecRef(dictPtr)
            self.assertEquals(frees, [dictPtr], "did not release memory")
        finally:
            mapper.Dispose()
            deallocTypes()
    
    
    @WithMapper
    def testIC_PyDict_Init(self, mapper, _):
        IC_PyDict_Init = CPyMarshal.ReadFunctionPtrField(mapper.PyDict_Type, PyTypeObject, "tp_init", dgt_int_ptrptrptr)
        # really, this function does *nothing*. and certainly doesn't follow the pointers passed in
        self.assertEquals(IC_PyDict_Init(IntPtr(123), IntPtr(456), IntPtr(789)), 0)
        

    @WithMapper
    def testStoreDictCreatesDictType(self, mapper, addToCleanUp):
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(typeBlock))
        mapper.RegisterData("PyDict_Type", typeBlock)
        
        dictPtr = mapper.Store({0: 1, 2: 3})
        self.assertEquals(CPyMarshal.ReadPtrField(dictPtr, PyObject, "ob_type"), typeBlock, "wrong type")


    @WithMapper
    def testStoreTypeDictCreatesDictTypeWhichWorks(self, mapper, addToCleanUp):
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(typeBlock))
        mapper.RegisterData("PyDict_Type", typeBlock)
        
        class klass(object):
            pass
        
        dictPtr = mapper.Store(klass.__dict__)
        self.assertEquals(CPyMarshal.ReadPtrField(dictPtr, PyObject, "ob_type"), typeBlock, "wrong type")
        
        self.assertEquals(mapper.PyDict_SetItemString(dictPtr, 'foo', mapper.Store('bar')), 0)
        self.assertEquals(mapper.PyDict_SetItem(dictPtr, mapper.Store('baz'), mapper.Store('qux')), 0)
        self.assertEquals(mapper.Retrieve(mapper.PyDict_GetItemString(dictPtr, 'foo')), 'bar')
        self.assertEquals(mapper.Retrieve(mapper.PyDict_GetItem(dictPtr, mapper.Store('baz'))), 'qux')
        self.assertEquals(klass.foo, 'bar')
        self.assertEquals(klass.baz, 'qux')
        self.assertEquals(mapper.PyDict_Size(dictPtr), len(klass.__dict__))
    
    
    @WithMapper
    def testPyDictProxy_New(self, mapper, _):
        d = {1: 2, 3: 4}
        dp = mapper.Retrieve(mapper.PyDictProxy_New(mapper.Store(d)))
        
        def Set(k, v):
            dp[k] = v
        self.assertRaises(TypeError, Set, 1, 5)
        self.assertRaises(TypeError, Set, 'foo', 'bar')
        
        self.assertEquals(dp[1], 2)
        self.assertEquals(dp[3], 4)
        self.assertEquals(len(dp), 2)
        
        for key in dp:
            self.assertTrue(key in d)
    

    @WithMapper
    def testPyDict_Size(self, mapper, _):
        dict0 = mapper.Store({})
        dict3 = mapper.Store({1:2, 3:4, 5:6})
        
        self.assertEquals(mapper.PyDict_Size(dict0), 0, "wrong")
        self.assertEquals(mapper.PyDict_Size(dict3), 3, "wrong")


    def testPyDict_GetItemStringSuccess(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({"abcde": 12345})
        
        itemPtr = mapper.PyDict_GetItemString(dictPtr, "abcde")
        self.assertEquals(mapper.Retrieve(itemPtr), 12345, "failed to get item")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "something is wrong")
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        self.assertEquals(itemPtr in frees, True)
        
        mapper.Dispose()
        deallocTypes()


    @WithMapper
    def testPyDict_GetItemStringFailure(self, mapper, _):
        dictPtr = mapper.Store({"abcde": 12345})
        
        itemPtr = mapper.PyDict_GetItemString(dictPtr, "bwahahaha!")
        self.assertEquals(itemPtr, IntPtr.Zero, "bad return for missing key")
        self.assertEquals(mapper.LastException, None, "should not set exception")


    def testPyDict_GetItemSuccess(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({12345: 67890})
        
        itemPtr = mapper.PyDict_GetItem(dictPtr, mapper.Store(12345))
        self.assertEquals(mapper.Retrieve(itemPtr), 67890, "failed to get item")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "something is wrong")
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        self.assertEquals(itemPtr in frees, True)
        
        mapper.Dispose()
        deallocTypes()


    @WithMapper
    def testPyDict_GetItemFailure(self, mapper, _):
        dictPtr = mapper.Store({12345: 67890})
        
        itemPtr = mapper.PyDict_GetItem(dictPtr, mapper.Store("something"))
        self.assertEquals(itemPtr, IntPtr.Zero, "bad return for missing key")
        self.assertEquals(mapper.LastException, None, "should not set exception")


    @WithMapper
    def testPyDict_SetItem(self, mapper, _):
        _dict = {}
        dictPtr = mapper.Store(_dict)
        keyPtr = mapper.Store(123)
        itemPtr = mapper.Store(456)
        self.assertEquals(mapper.PyDict_SetItem(dictPtr, keyPtr, itemPtr), 0, "reported failure")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "does not need to incref item")
        self.assertEquals(_dict, {123: 456}, "failed")


    @WithMapper
    def testPyDict_SetItem_Unhashable(self, mapper, _):
        _dict = {}
        dictPtr = mapper.Store(_dict)
        keyPtr = mapper.Store({})
        itemPtr = mapper.Store(456)
        self.assertEquals(mapper.PyDict_SetItem(dictPtr, keyPtr, itemPtr), -1, "failed to report failure")
        self.assertEquals(_dict, {}, 'dictionary changed')
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyDict_SetItemString(self, mapper, _):
        _dict = {}
        dictPtr = mapper.Store(_dict)
        itemPtr = mapper.Store(123)
        self.assertEquals(mapper.PyDict_SetItemString(dictPtr, 'blob', itemPtr), 0, "reported failure")
        self.assertEquals(mapper.RefCount(itemPtr), 1, "does not need to incref item")
        self.assertEquals(_dict, {'blob': 123}, "failed")


    @WithMapper
    def testPyDict_SetItemString_UnknownType(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        addToCleanUp(deallocType)
        
        _dict = {}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_SetItemString(dictPtr, 'klass', typePtr), 0, "reported failure")
        klass = _dict['klass']
        self.assertEquals(klass.__name__, 'klass', "failed")


    @WithMapper
    def testPyDict_DelItem_Exists(self, mapper, _):
        key = object()
        _dict = {key: 1}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_DelItem(dictPtr, mapper.Store(key)), 0)
        self.assertMapperHasError(mapper, None)
        self.assertEquals(_dict, {})


    @WithMapper
    def testPyDict_DelItem_ExistsNot(self, mapper, _):
        _dict = {}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_DelItem(dictPtr, mapper.Store(object())), -1)
        self.assertMapperHasError(mapper, None)
        self.assertEquals(_dict, {})


    @WithMapper
    def testPyDict_DelItem_Unhashable(self, mapper, _):
        _dict = {}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_DelItem(dictPtr, mapper.Store({})), -1)
        self.assertMapperHasError(mapper, TypeError)
        self.assertEquals(_dict, {})


    @WithMapper
    def testPyDict_DelItemString_Exists(self, mapper, _):
        _dict = {'clef': 1}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_DelItemString(dictPtr, 'clef'), 0)
        self.assertMapperHasError(mapper, None)
        self.assertEquals(_dict, {})


    @WithMapper
    def testPyDict_DelItemString_ExistsNot(self, mapper, _):
        _dict = {}
        dictPtr = mapper.Store(_dict)
        self.assertEquals(mapper.PyDict_DelItemString(dictPtr, 'clef'), -1)
        self.assertMapperHasError(mapper, None)
        self.assertEquals(_dict, {})


    @WithMapper
    def testPyDict_Values(self, mapper, _):
        _dict = {1: 2, 3: 4, 5: 6}
        dictPtr = mapper.Store(_dict)
        listPtr = mapper.PyDict_Values(dictPtr)
        self.assertEquals(set(mapper.Retrieve(listPtr)), set(_dict.values()))


    @WithMapper
    def testPyDict_Update(self, mapper, _):
        d1 = {1:2, 3:4}
        d2 = {1:5, 6:7}
        
        self.assertEquals(mapper.PyDict_Update(mapper.Store(d1), mapper.Store(d2)), 0)
        self.assertMapperHasError(mapper, None)
        self.assertEquals(d1, {1:5, 3:4, 6:7})
        
        self.assertEquals(mapper.PyDict_Update(mapper.Store(d1), mapper.Store(object)), -1)
        self.assertMapperHasError(mapper, TypeError)
    
    
    @WithMapper
    def testPyDict_Copy(self, mapper, _):
        d1 = {1:2, 3:4}
        d2 = mapper.Retrieve(mapper.PyDict_Copy(mapper.Store(d1)))
        self.assertEquals(d1, d2)
        d1[5] = 6
        self.assertEquals(d2, {1:2, 3:4})
        
        self.assertEquals(mapper.PyDict_Copy(mapper.Store(object())), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


class PyDict_Next_Test(TestCase):

    @WithMapper
    def testEmptyDict(self, mapper, addDealloc):
        posPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(posPtr))
        CPyMarshal.WriteInt(posPtr, 0)
        
        self.assertEquals(mapper.PyDict_Next(mapper.Store({}), posPtr, IntPtr.Zero, IntPtr.Zero), 0)
        self.assertMapperHasError(mapper, None)
    
    @WithMapper
    def testNotADict(self, mapper, addDealloc):
        posPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(posPtr))
        CPyMarshal.WriteInt(posPtr, 0)
        
        self.assertEquals(mapper.PyDict_Next(mapper.Store(object()), posPtr, IntPtr.Zero, IntPtr.Zero), 0)
        self.assertMapperHasError(mapper, TypeError)
    
    @WithMapper
    def testIteratesSuccessfully(self, mapper, addDealloc):
        posPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 3)
        keyPtrPtr = CPyMarshal.Offset(posPtr, CPyMarshal.PtrSize)
        valuePtrPtr = CPyMarshal.Offset(keyPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(posPtr))
        CPyMarshal.WriteInt(posPtr, 0)
        
        d = dict(a=1, b=2, c=3)
        dPtr = mapper.Store(d)
        result = {}
        while mapper.PyDict_Next(dPtr, posPtr, keyPtrPtr, valuePtrPtr) != 0:
            key = mapper.Retrieve(CPyMarshal.ReadPtr(keyPtrPtr))
            value = mapper.Retrieve(CPyMarshal.ReadPtr(valuePtrPtr))
            result[key] = value
        
        self.assertEquals(result, d)
          
    @WithMapper
    def testCanChangeValuesDuringIteration(self, mapper, addDealloc):
        posPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 3)
        keyPtrPtr = CPyMarshal.Offset(posPtr, CPyMarshal.PtrSize)
        valuePtrPtr = CPyMarshal.Offset(keyPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(posPtr))
        CPyMarshal.WriteInt(posPtr, 0)
        
        d = dict(a=1, b=2, c=3)
        dPtr = mapper.Store(d)
        while mapper.PyDict_Next(dPtr, posPtr, keyPtrPtr, valuePtrPtr) != 0:
            key = mapper.Retrieve(CPyMarshal.ReadPtr(keyPtrPtr))
            value = mapper.Retrieve(CPyMarshal.ReadPtr(valuePtrPtr))
            d[key] = value * 10
        
        self.assertEquals(d, dict(a=10, b=20, c=30))
          
    @WithMapper
    def testReferencesAreBorrowed(self, mapper, addDealloc):
        posPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 3)
        keyPtrPtr = CPyMarshal.Offset(posPtr, CPyMarshal.PtrSize)
        valuePtrPtr = CPyMarshal.Offset(keyPtrPtr, CPyMarshal.PtrSize)
        addDealloc(lambda: Marshal.FreeHGlobal(posPtr))
        CPyMarshal.WriteInt(posPtr, 0)
        
        d = dict(a=1)
        dPtr = mapper.Store(d)
        mapper.PyDict_Next(dPtr, posPtr, keyPtrPtr, valuePtrPtr)
        
        keyPtr = CPyMarshal.ReadPtr(keyPtrPtr)
        valuePtr = CPyMarshal.ReadPtr(valuePtrPtr)
        
        # grab extra references to retard spoilage
        mapper.IncRef(keyPtr)
        mapper.IncRef(valuePtr)
        
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        
        # check refcount has dropped back to 1
        self.assertEquals(mapper.RefCount(keyPtr), 1)
        self.assertEquals(mapper.RefCount(valuePtr), 1)





suite = makesuite(
    DictTest,
    PyDict_Next_Test,
)

if __name__ == '__main__':
    run(suite)
