
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.memory import CreateTypes

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import BadRefCountException, CPyMarshal, CPython_destructor_Delegate, Python25Mapper, UnmanagedDataMarker
from Ironclad.Structs import PyObject, PyTypeObject


class Python25MapperTest(unittest.TestCase):

    def testBasicStoreRetrieveFree(self):
        frees = []
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
        try:
            obj1 = object()
            self.assertEquals(allocs, [], "unexpected allocations")
            ptr = mapper.Store(obj1)
            self.assertEquals(len(allocs), 1, "unexpected number of allocations")
            self.assertEquals(allocs[0], (ptr, Marshal.SizeOf(PyObject)), "unexpected result")
            self.assertNotEquals(ptr, IntPtr.Zero, "did not store reference")
            self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), 
                              mapper.PyBaseObject_Type, 
                              "nearly-opaque pointer had wrong type")

            obj2 = mapper.Retrieve(ptr)
            self.assertTrue(obj1 is obj2, "retrieved wrong object")

            self.assertEquals(frees, [], "unexpected deallocations")
            mapper.PyObject_Free(ptr)
            self.assertEquals(frees, [ptr], "unexpected deallocations")
            self.assertRaises(KeyError, lambda: mapper.RefCount(ptr))
            self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
            self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        finally:
            deallocTypes()


    def testCanFreeWithRefCount0(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 0)
        mapper.StoreUnmanagedData(objPtr, object())
        mapper.PyObject_Free(objPtr)
        self.assertEquals(frees, [objPtr], "didn't actually release memory")
        

    def testStoreSameObjectIncRefsOriginal(self):
        frees = []
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        
        obj1 = object()
        result1 = mapper.Store(obj1)
        result2 = mapper.Store(obj1)
        
        self.assertEquals(allocs, [(result1, Marshal.SizeOf(PyObject))], "unexpected result")
        self.assertEquals(result1, result2, "did not return same ptr")
        self.assertEquals(mapper.RefCount(result1), 2, "did not incref")
        
        mapper.DecRef(result1)
        mapper.DecRef(result1)
        
        self.assertEquals(frees, [result1], "did not free memory")
        
        result3 = mapper.Store(obj1)
        self.assertEquals(allocs, 
                          [(result1, Marshal.SizeOf(PyObject)), (result3, Marshal.SizeOf(PyObject))], 
                          "unexpected result -- failed to clear reverse mapping?")
        mapper.DecRef(result3)
        

    def testStoreEqualObjectStoresSeparately(self):
        mapper = Python25Mapper()
        
        result1 = mapper.Store([1, 2, 3])
        result2 = mapper.Store([1, 2, 3])
        
        self.assertNotEquals(result1, result2, "confused separate objects")
        self.assertEquals(mapper.RefCount(result1), 1, "wrong")
        self.assertEquals(mapper.RefCount(result2), 1, "wrong")
        
        mapper.DecRef(result1)
        mapper.DecRef(result2)


    def testDecRefObjectWithZeroRefCountFails(self):
        mapper = Python25Mapper()
        
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 0)
        mapper.StoreUnmanagedData(objPtr, object())
        self.assertRaises(BadRefCountException, lambda: mapper.DecRef(objPtr))
        Marshal.FreeHGlobal(objPtr)


    def testFinalDecRefOfObjectWithTypeCalls_tp_dealloc(self):
        mapper = Python25Mapper()
        
        calls = []
        def TypeDealloc(ptr):
            calls.append(ptr)
        deallocDgt = CPython_destructor_Delegate(TypeDealloc)
        deallocFP = Marshal.GetFunctionPointerForDelegate(deallocDgt)
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        deallocPtr = CPyMarshal.Offset(typePtr, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
        CPyMarshal.WritePtr(deallocPtr, deallocFP)
        
        obj = object()
        objPtr = mapper.Store(obj)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)
        
        mapper.IncRef(objPtr)
        mapper.DecRef(objPtr)
        self.assertEquals(calls, [], "called prematurely")
        mapper.DecRef(objPtr)
        self.assertEquals(calls, [objPtr], "not called when refcount hit 0")
    
    
    def testFinalDecRefDoesNotCallNull_tp_dealloc_ButDoesFreeMemory(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_dealloc", IntPtr.Zero)
        
        obj = object()
        objPtr = mapper.Store(obj)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)
        
        mapper.IncRef(objPtr)
        mapper.DecRef(objPtr)
        self.assertEquals(frees, [], "freed prematurely")
        mapper.DecRef(objPtr)
        self.assertEquals(frees, [objPtr], "not freed when refcount hit 0")
    

    def testStoreUnmanagedData(self):
        mapper = Python25Mapper()

        o = object()
        ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.StoreUnmanagedData(ptr, o)

        self.assertEquals(mapper.Retrieve(ptr), o, "object not stored")
        self.assertEquals(mapper.Store(o), ptr, "object not reverse-mapped")


    def testCannotStoreUnmanagedDataMarker(self):
        mapper = Python25Mapper()
        
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyStringObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyTupleObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyListObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.None))


    def testRefCountIncRefDecRef(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)

        obj1 = object()
        ptr = mapper.Store(obj1)
        mapper.IncRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 2, "unexpected refcount")

        mapper.DecRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")

        self.assertEquals(frees, [], "unexpected deallocations")
        mapper.DecRef(ptr)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr(1)))


    def testNullPointers(self):
        allocator = GetDoNothingTestAllocator([])
        mapper = Python25Mapper(allocator)

        self.assertRaises(KeyError, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr.Zero))


    def testRememberAndFreeTempObjects(self):
        mapper = Python25Mapper()

        tempObject1 = mapper.Store(1)
        tempObject2 = mapper.Store(2)

        mapper.RememberTempObject(tempObject1)
        mapper.RememberTempObject(tempObject2)

        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "RememberTempObject should not incref")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "RememberTempObject should not incref")

        mapper.IncRef(tempObject1)
        mapper.IncRef(tempObject2)

        mapper.FreeTemps()

        try:
            self.assertEquals(mapper.RefCount(tempObject1), 1,
                              "FreeTemps should decref objects rather than freeing them")
            self.assertEquals(mapper.RefCount(tempObject2), 1,
                              "FreeTemps should decref objects rather than freeing them")

            mapper.FreeTemps()
            self.assertEquals(mapper.RefCount(tempObject1), 1,
                              "FreeTemps should clear list once called")
            self.assertEquals(mapper.RefCount(tempObject2), 1,
                              "FreeTemps should clear list once called")
        finally:
            mapper.DecRef(tempObject1)
            mapper.DecRef(tempObject2)
    

class Python25Mapper_GetMethodFP_Test(unittest.TestCase):
    
    def assertGetMethodFPWorks(self, name):
        mapper = Python25Mapper()
        
        fp1 = mapper.GetMethodFP(name)
        fp2 = mapper.GetMethodFP(name)
        self.assertEquals(fp1, fp2, "did not remember func ptrs")
        
    
    def testMethods(self):
        methods = (
            "PyBaseObject_Dealloc",
            "PyTuple_Dealloc",
            "PyList_Dealloc",
        )
        for method in methods:
            self.assertGetMethodFPWorks(method)

    
class Python25Mapper_NoneTest(unittest.TestCase):
    
    def testFillNone(self):
        mapper = Python25Mapper()
        
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.Fill__Py_NoneStruct(nonePtr)
        noneStruct = Marshal.PtrToStructure(nonePtr, PyObject)
        self.assertEquals(noneStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(noneStruct.ob_type, IntPtr.Zero, "unexpected type")
        Marshal.FreeHGlobal(nonePtr)
    
    
    def testStoreNone(self):
        mapper = Python25Mapper()
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.SetData("_Py_NoneStruct", nonePtr)
        
        # if the following line fails, we probably have a public Store overload taking something
        # more specific than 'object', which is therefore called in preference to the 'object'
        # version of Store. (IronPython None becomes C# null, which is of every type. Sort of.)
        resultPtr = mapper.Store(None)
        self.assertEquals(resultPtr, nonePtr, "wrong")
        self.assertEquals(mapper.RefCount(nonePtr), 2, "did not incref")
        
        self.assertEquals(mapper.Retrieve(nonePtr), None, "not mapped properly")

        Marshal.FreeHGlobal(nonePtr)


suite = makesuite(
    Python25MapperTest,
    Python25Mapper_GetMethodFP_Test,
    Python25Mapper_NoneTest,
)

if __name__ == '__main__':
    run(suite)