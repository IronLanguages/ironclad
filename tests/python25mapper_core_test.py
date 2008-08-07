import os
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase

from System import Int32, IntPtr, NullReferenceException, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    BadRefCountException, CPyMarshal, CPython_destructor_Delegate, HGlobalAllocator, Python25Mapper, 
    Unmanaged, UnmanagedDataMarker
)
from Ironclad.Structs import PyObject, PyTypeObject



class Python25Mapper_CreateDestroy_Test(TestCase):
    
    def testCreateDestroy(self):
        mapper = Python25Mapper()
        self.assertEquals(mapper.Alive, True)
        mapper.Dispose()
        self.assertEquals(mapper.Alive, False)
        
    
    def testLoadsStubWhenPassedPathAndUnloadsOnDispose(self):
        mapper = Python25Mapper(os.path.join("build", "python25.dll"))
        self.assertNotEquals(Unmanaged.GetModuleHandle("python25.dll"), IntPtr.Zero,
                             "library not mapped by construction")
        self.assertNotEquals(Python25Mapper._Py_NoneStruct, IntPtr.Zero,
                             "mapping not set up")
        
        # weak side-effect test to hopefully prove that ReadyBuiltinTypes has been called
        self.assertEquals(CPyMarshal.ReadPtrField(mapper.PyLong_Type, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        
        mapper.Dispose()
        self.assertEquals(Unmanaged.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library not unmapped by Dispose")
        
    
    def testLoadsModuleAndUnloadsOnDispose(self):
        mapper = Python25Mapper(os.path.join("build", "python25.dll"))
        mapper.LoadModule(os.path.join("tests", "data", "setvalue.pyd"), "some.module")
        self.assertNotEquals(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                             "library not mapped by construction")
        
        mapper.Dispose()
        self.assertEquals(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                          "library not unmapped by Dispose")
    
    
    def testFreesObjectsOnDispose(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        ptrs = []
        ptrs.append(mapper.Store('hullo'))
        ptrs.append(mapper.Store(123))
        ptrs.append(mapper.Store(object()))
        
        mapper.Dispose()
        for ptr in ptrs:
            self.assertTrue(ptr in frees, "ptr not freed")
        
    
    def testDestroysObjectsOfUnmanagedTypesFirst(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        calls = []
        def Del(instancePtr):
            calls.append("del")
            mapper.PyObject_Free(instancePtr)
        typeSpec = {
            'tp_name': 'klass',
            'tp_dealloc': Del
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        mapper.PyModule_AddObject(modulePtr, 'klass', typePtr)
        
        easyptr = mapper.Store(123)
        instance = module.klass()
        hardptr = instance._instancePtr
        
        mapper.Dispose()
        self.assertEquals(frees.index(hardptr) < frees.index(easyptr), True, "failed to dealloc in correct order")
        self.assertEquals(calls, ['del'], "failed to clean up klass instance")
        
        deallocType()
        deallocTypes()
        


class Python25Mapper_References_Test(TestCase):

    def testBasicStoreRetrieveFree(self):
        frees = []
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
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
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        
        mapper.Dispose()
        deallocTypes()


    def testCanFreeWithRefCount0(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        
        objPtr = mapper.Store(object())
        CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 0)
        
        mapper.PyObject_Free(objPtr)
        self.assertEquals(frees, [objPtr], "didn't actually release memory")
        mapper.Dispose()
        

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
        mapper.Dispose()
        

    def testStoreEqualObjectStoresSeparately(self):
        mapper = Python25Mapper()
        
        result1 = mapper.Store([1, 2, 3])
        result2 = mapper.Store([1, 2, 3])
        
        self.assertNotEquals(result1, result2, "confused separate objects")
        self.assertEquals(mapper.RefCount(result1), 1, "wrong")
        self.assertEquals(mapper.RefCount(result2), 1, "wrong")
        
        mapper.Dispose()


    def testEqualFloatsIntsStoredSeparately(self):
        mapper = Python25Mapper()
        
        result1 = mapper.Store(0)
        result2 = mapper.Store(0.0)
        
        self.assertNotEquals(result1, result2, "confused separate objects")
        self.assertEquals(mapper.RefCount(result1), 1, "wrong")
        self.assertEquals(mapper.RefCount(result2), 1, "wrong")
        
        mapper.Dispose()
        


    def testDecRefObjectWithZeroRefCountFails(self):
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        objPtr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 0)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", mapper.PyBaseObject_Type)
        mapper.StoreBridge(objPtr, object())
        
        self.assertRaises(BadRefCountException, lambda: mapper.DecRef(objPtr))
        
        # need to dealloc ptr ourselves, it doesn't hapen automatically
        # except for objects with Dispatchers
        mapper.PyBaseObject_Dealloc(objPtr)
        mapper.Dispose()
        deallocTypes()


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
        mapper.Dispose()
    
    
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
        mapper.Dispose()
    

    def testStoreBridge(self):
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)

        obj = object()
        objref = WeakReference(obj)
        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
        mapper.StoreBridge(ptr, obj)

        self.assertEquals(mapper.Retrieve(ptr), obj, "object not stored")
        self.assertEquals(mapper.Store(obj), ptr, "object not reverse-mapped")
        
        mapper.Weaken(obj)
        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
        
        mapper.IncRef(ptr)
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "was not strengthened by IncRef")
        
        obj = mapper.Retrieve(ptr)
        mapper.DecRef(ptr)
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, False, "was not weakened by DecRef")
        
        # need to dealloc ptr ourselves, it doesn't hapen automatically
        # except for objects with Dispatchers
        mapper.PyBaseObject_Dealloc(ptr)
        mapper.Dispose()
        deallocTypes()
    

    def testStrengthenWeakenUnmanagedInstance(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)

        obj = object()
        objref = WeakReference(obj)
        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
        mapper.StoreBridge(ptr, obj)
        mapper.Strengthen(obj)
        
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "was not strengthened")
        
        sameobj = objref.Target
        mapper.Weaken(sameobj)
        del sameobj
        gcwait()
        self.assertRaises(NullReferenceException, mapper.Retrieve, ptr)
        
        # need to dealloc ptr ourselves, it doesn't hapen automatically
        # except for objects with Dispatchers
        mapper.PyBaseObject_Dealloc(ptr)
        mapper.Dispose()
        deallocTypes()


    def testCheckBridgePtrs(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)

        obj = object()
        objref = WeakReference(obj)
        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 2)
        CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
        mapper.StoreBridge(ptr, obj)
        mapper.CheckBridgePtrs()
        
        # refcount > 1 means ref should have been strengthened
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "was reaped unexpectedly (refcount was 2)")
        
        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
        mapper.CheckBridgePtrs()
        
        # refcount < 2 should have been weakened
        obj = objref.Target
        del obj
        gcwait()
        self.assertRaises(NullReferenceException, mapper.Retrieve, ptr)
        
        # need to dealloc ptr ourselves, it doesn't hapen automatically
        # except for objects with Dispatchers
        mapper.PyBaseObject_Dealloc(ptr)
        mapper.Dispose()
        deallocTypes()
        


    def testCannotStoreUnmanagedDataMarker(self):
        mapper = Python25Mapper()
        
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyStringObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyTupleObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyListObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.None))
        mapper.Dispose()


    def testRefCountIncRefDecRef(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)

        obj1 = object()
        ptr = mapper.Store(obj1)
        self.assertEquals(mapper.HasPtr(ptr), True)
        
        mapper.IncRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 2, "unexpected refcount")
        self.assertEquals(mapper.HasPtr(ptr), True)

        mapper.DecRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")
        self.assertEquals(mapper.HasPtr(ptr), True)
        self.assertEquals(frees, [], "unexpected deallocations")
        
        mapper.DecRef(ptr)
        self.assertEquals(mapper.HasPtr(ptr), False)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        mapper.Dispose()


    def testNullPointers(self):
        allocator = GetDoNothingTestAllocator([])
        mapper = Python25Mapper(allocator)

        self.assertRaises(KeyError, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr.Zero))
        self.assertEquals(mapper.HasPtr(IntPtr.Zero), False)
        mapper.Dispose()


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

        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "FreeTemps should decref objects rather than freeing them")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "FreeTemps should decref objects rather than freeing them")

        mapper.FreeTemps()
        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "FreeTemps should clear list once called")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "FreeTemps should clear list once called")
                          
        mapper.Dispose()
    
    
    def testStoreRetrieveDeleteAbsurdNumbersOfObjects(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.SetData("_Py_NoneStruct", nonePtr)
        
        def GetObject(i):
            if not i % 2:
                return i
            if not i % 3:
                return 'x' * (i % 1001)
            if not i % 5:
                return object()
            if not i % 7:
                return (i, object())
            if not i % 11:
                return [object(), i]
            if not i % 13:
                return dict([(i, object())])
            return None
        
        ptrs = {}
        for i in xrange(1000000):
            obj = GetObject(i)
            ptr = mapper.Store(obj)
            ptrs[ptr] = obj
        
        for k, v in ptrs.iteritems():
            self.assertEquals(mapper.Retrieve(k), v, "failed to retrieve")
            mapper.DecRef(k)
        
        mapper.Dispose()
        deallocTypes()
        Marshal.FreeHGlobal(nonePtr)
        
    

class Python25Mapper_GetAddress_NonApi_Test(TestCase):
    
    def assertGetAddressWorks(self, name):
        mapper = Python25Mapper()
        
        fp1 = mapper.GetAddress(name)
        fp2 = mapper.GetAddress(name)
        self.assertNotEquals(fp1, IntPtr.Zero, "did not get address")
        self.assertEquals(fp1, fp2, "did not remember func ptrs")
        mapper.Dispose()
        
    
    def testMethods(self):
        methods = (
            "PyBaseObject_Dealloc",
            "PyBaseObject_Init",
            "PyTuple_Dealloc",
            "PyList_Dealloc",
        )
        for method in methods:
            self.assertGetAddressWorks(method)


class Python25Mapper_NoneTest(TestCase):
    
    def testFillNone(self):
        mapper = Python25Mapper()
        
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.Fill__Py_NoneStruct(nonePtr)
        noneStruct = Marshal.PtrToStructure(nonePtr, PyObject)
        self.assertEquals(noneStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(noneStruct.ob_type, IntPtr.Zero, "unexpected type")
        mapper.Dispose()
        Marshal.FreeHGlobal(nonePtr)
    
    
    def testStoreNone(self):
        mapper = Python25Mapper()
        nonePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.SetData("_Py_NoneStruct", nonePtr)
        
        resultPtr = mapper.Store(None)
        self.assertEquals(resultPtr, nonePtr, "wrong")
        self.assertEquals(mapper.RefCount(nonePtr), 2, "did not incref")
        
        self.assertEquals(mapper.Retrieve(nonePtr), None, "not mapped properly")
        
        mapper.Dispose()
        Marshal.FreeHGlobal(nonePtr)


class Python25Mapper_Py_OptimizeFlag_Test(TestCase):

    def testFills(self):
        # TODO: if we set a lower value, numpy will crash inside arr_add_docstring
        # I consider docstrings to be low-priority-enough that it's OK to fudge this
        # for now
        mapper = Python25Mapper()
        flagPtr = Marshal.AllocHGlobal(Marshal.SizeOf(Int32))
        mapper.SetData("Py_OptimizeFlag", flagPtr)
        
        self.assertEquals(CPyMarshal.ReadInt(flagPtr), 2)
        
        mapper.Dispose()
        Marshal.FreeHGlobal(flagPtr)
    


suite = makesuite(
    Python25Mapper_CreateDestroy_Test,
    Python25Mapper_References_Test,
    Python25Mapper_GetAddress_NonApi_Test,
    Python25Mapper_NoneTest,
    Python25Mapper_Py_OptimizeFlag_Test,
)

if __name__ == '__main__':
    run(suite)
