import os
import sys
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase, WithMapper

from System import Int32, IntPtr, NullReferenceException, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    BadRefCountException, CannotInterpretException, CPyMarshal, dgt_void_ptr, dgt_void_void,
    HGlobalAllocator, Python25Mapper, Unmanaged, UnmanagedDataMarker
)
from Ironclad.Structs import PyObject, PyTypeObject


class Python25Mapper_CreateDestroy_Test(TestCase):
    
    def testCreateDestroy(self):
        mapper = Python25Mapper()
        self.assertEquals(mapper.Alive, True)
        mapper.Dispose()
        self.assertEquals(mapper.Alive, False)
        mapper.Dispose()
        # jolly good, didn't crash
        
    
    def testLoadsStubWhenPassedPathAndUnloadsOnDispose(self):
        mapper = Python25Mapper(os.path.join("build", "ironclad", "python26.dll"))
        self.assertNotEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
                             "library not mapped by construction")
        self.assertNotEquals(Python25Mapper._Py_NoneStruct, IntPtr.Zero,
                             "mapping not set up")
        
        # weak side-effect test to hopefully prove that ReadyBuiltinTypes has been called
        self.assertEquals(CPyMarshal.ReadPtrField(mapper.PyLong_Type, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        
        mapper.Dispose()
        self.assertEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
                          "library not unmapped by Dispose")
        
    
    def testLoadsModuleAndUnloadsOnDispose(self):
        mapper = Python25Mapper(os.path.join("build", "ironclad", "python26.dll"))
        origcwd = os.getcwd()
        mapper.LoadModule(os.path.join("tests", "data", "setvalue.pyd"), "some.module")
        self.assertEquals(os.getcwd(), origcwd, "failed to restore working directory")
        self.assertNotEquals(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                             "library not mapped by construction")
        
        mapper.Dispose()
        self.assertEquals(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                          "library not unmapped by Dispose")
    
    
    def testRemovesMmapOnDispose(self):
        mapper = Python25Mapper(os.path.join("build", "ironclad", "python26.dll"))
        sys.modules['csv'] = object()
        mapper.Dispose()
        self.assertFalse('mmap' in sys.modules)
        self.assertFalse('_csv' in sys.modules)
        self.assertFalse('csv' in sys.modules)
    
    
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
    
    
    def testCallsAtExitFunctionsOnDispose(self):
        calls = []
        def MangleCall(arg):
            return Marshal.GetFunctionPointerForDelegate(
                dgt_void_void(lambda: calls.append(arg)))
        
        mapper = Python25Mapper()
        self.assertEquals(mapper.Py_AtExit(MangleCall('foo')), 0)
        self.assertEquals(mapper.Py_AtExit(MangleCall('bar')), 0)
        self.assertEquals(calls, [])
        mapper.Dispose()
        self.assertEquals(calls, ['bar', 'foo'])
    
    
    def testDestroysObjectsOfUnmanagedTypesFirst(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        calls = []
        def Del(instancePtr):
            calls.append(("del", instancePtr))
            mapper.PyObject_Free(instancePtr)
        typeSpec = {
            'tp_name': 'klass',
            'tp_dealloc': Del
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        mapper.PyModule_AddObject(modulePtr, 'klass', typePtr)
        
        easyptr = mapper.Store(123)
        instance1 = module.klass()
        hardptr = mapper.Store(instance1)
        instance2 = module.klass()
        brokenptr = mapper.Store(instance2)
        CPyMarshal.WritePtrField(brokenptr, PyObject, 'ob_type', IntPtr.Zero)
        
        mapper.Dispose()
        self.assertEquals(frees.index(hardptr) < frees.index(easyptr), True, "failed to dealloc in correct order")
        self.assertEquals(calls, [('del', hardptr)], "failed to clean up klass instance")
        
        deallocType()
        deallocTypes()
    
    
    def testIgnoresBridgeObjectsNotAllocatedByAllocator(self):
        obj = object()
        ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        
        mapper = Python25Mapper()
        mapper.StoreBridge(ptr, obj)
        mapper.Dispose()
        # attempting to free ptr would have failed


class Python25Mapper_References_Test(TestCase):

    def testBasicStoreRetrieveFree(self):
        frees = []
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        obj1 = object()
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
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        obj1 = object()
        result1 = mapper.Store(obj1)
        result2 = mapper.Store(obj1)
        
        self.assertEquals(allocs, [(result1, Marshal.SizeOf(PyObject))], "unexpected result")
        self.assertEquals(result1, result2, "did not return same ptr")
        self.assertEquals(mapper.RefCount(result1), 2, "did not incref")
        
        mapper.DecRef(result1)
        
        del frees[:]
        mapper.DecRef(result1)
        self.assertEquals(frees, [result1], "did not free memory")
        
        result3 = mapper.Store(obj1)
        self.assertEquals(allocs, 
                          [(result1, Marshal.SizeOf(PyObject)), (result3, Marshal.SizeOf(PyObject))], 
                          "unexpected result -- failed to clear reverse mapping?")
        mapper.Dispose()
        deallocTypes()
        

    @WithMapper
    def testStoreEqualObjectStoresSeparately(self, mapper, _):
        result1 = mapper.Store([1, 2, 3])
        result2 = mapper.Store([1, 2, 3])
        
        self.assertNotEquals(result1, result2, "confused separate objects")
        self.assertEquals(mapper.RefCount(result1), 1, "wrong")
        self.assertEquals(mapper.RefCount(result2), 1, "wrong")


    @WithMapper
    def testEqualFloatsIntsStoredSeparately(self, mapper, _):
        result1 = mapper.Store(0)
        result2 = mapper.Store(0.0)
        
        self.assertNotEquals(result1, result2, "confused separate objects")
        self.assertEquals(mapper.RefCount(result1), 1, "wrong")
        self.assertEquals(mapper.RefCount(result2), 1, "wrong")


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
        mapper.Dispose()
        deallocTypes()


    @WithMapper
    def testFinalDecRefOfObjectWithTypeCalls_tp_dealloc(self, mapper, _):
        calls = []
        def TypeDealloc(ptr):
            calls.append(ptr)
        deallocDgt = dgt_void_ptr(TypeDealloc)
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


    def testFinalDecRefComplainsAboutMissing_tp_dealloc(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_dealloc", IntPtr.Zero)
        
        obj = object()
        objPtr = mapper.Store(obj)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)
        
        mapper.IncRef(objPtr)
        
        del frees [:]
        mapper.DecRef(objPtr)
        self.assertEquals(frees, [], "freed prematurely")
        self.assertRaises(CannotInterpretException, mapper.DecRef, objPtr)
        
        mapper.Dispose()
        deallocTypes()
    

    def testStoreBridge(self):
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(Marshal.SizeOf(PyObject))
        
        try:
            def do():
                # see NOTE in interestingptrmaptest
                obj = object()
                ref = WeakReference(obj)
                CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
                CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
                mapper.StoreBridge(ptr, obj)

                self.assertEquals(mapper.Retrieve(ptr), obj, "object not stored")
                self.assertEquals(mapper.Store(obj), ptr, "object not reverse-mapped")

                mapper.Weaken(obj)
                CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)

                mapper.IncRef(ptr)
                del obj
                return ref
            ref = do()
            gcwait()
            self.assertEquals(ref.IsAlive, True, "was not strengthened by IncRef")

            mapper.DecRef(ptr)
            gcwait()
            self.assertEquals(ref.IsAlive, False, "was not weakened by DecRef")

        finally:
            # need to dealloc ptr ourselves, it doesn't hapen automatically
            # except for objects with Dispatchers
            mapper.IC_PyBaseObject_Dealloc(ptr)
            mapper.Dispose()
            deallocTypes()
    

    def testStrengthenWeakenUnmanagedInstance(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)

        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(Marshal.SizeOf(PyObject))
        
        try:
            def do1():
                # see NOTE in interestingptrmaptest
                obj = object()
                ref = WeakReference(obj)
                CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
                CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
                mapper.StoreBridge(ptr, obj)
                del obj
                return ref
            ref = do1()
            gcwait()
            self.assertEquals(ref.IsAlive, True, "was not strongly referenced")

            def do2():
                obj = ref.Target
                mapper.Weaken(obj)
                del obj
            do2()
            gcwait()
            self.assertRaises(NullReferenceException, mapper.Retrieve, ptr)
        
        finally:
            # need to dealloc ptr ourselves, it doesn't hapen automatically
            # except for objects with Dispatchers
            mapper.IC_PyBaseObject_Dealloc(ptr)
            mapper.Dispose()
            deallocTypes()


    def testReleaseGILChecksBridgePtrs(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)

        # force no throttling of cleanup
        mapper.GCThreshold = 0
        
        def do1():
            obj = object()
            ref = WeakReference(obj)
            # need to use same allocator as mapper, otherwise it gets upset on shutdown
            ptr = allocator.Alloc(Marshal.SizeOf(PyObject))
            CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 2)
            CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
            mapper.StoreBridge(ptr, obj)

            # refcount > 1 means ref should have been strengthened
            del obj
            return ref, ptr
        ref, ptr = do1()
        gcwait()
        self.assertEquals(ref.IsAlive, True, "was reaped unexpectedly (refcount was 2)")
        
        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        
        # refcount < 2 should have been weakened
        gcwait()
        self.assertRaises(NullReferenceException, mapper.Retrieve, ptr)
        
        # need to dealloc ptr ourselves, it doesn't hapen automatically
        # except for objects with Dispatchers
        mapper.IC_PyBaseObject_Dealloc(ptr)
        mapper.Dispose()
        deallocTypes()


    @WithMapper
    def testCannotStoreUnmanagedDataMarker(self, mapper, _):
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyStringObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyTupleObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyListObject))


    def testRefCountIncRefDecRef(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)

        obj1 = object()
        ptr = mapper.Store(obj1)
        self.assertEquals(mapper.HasPtr(ptr), True)
        
        mapper.IncRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 2, "unexpected refcount")
        self.assertEquals(mapper.HasPtr(ptr), True)

        del frees[:]
        mapper.DecRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")
        self.assertEquals(mapper.HasPtr(ptr), True)
        self.assertEquals(frees, [], "unexpected deallocations")
        
        mapper.DecRef(ptr)
        self.assertEquals(mapper.HasPtr(ptr), False)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        
        mapper.Dispose()
        deallocTypes()


    def testNullPointers(self):
        allocator = GetDoNothingTestAllocator([])
        mapper = Python25Mapper(allocator)

        self.assertEquals(mapper.HasPtr(IntPtr.Zero), False)
        self.assertRaises(CannotInterpretException, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(CannotInterpretException, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(CannotInterpretException, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(CannotInterpretException, lambda: mapper.RefCount(IntPtr.Zero))
        mapper.Dispose()


    @WithMapper
    def testRememberAndFreeTempObjects(self, mapper, _):
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

        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "ReleaseGIL should decref temp objects rather than freeing them")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "ReleaseGIL should decref temp objects rather than freeing them")
                          
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "ReleaseGIL should clear list once called")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "ReleaseGIL should clear list once called")


    @WithMapper
    def testStoreRetrieveDeleteAbsurdNumbersOfObjects(self, mapper, _):
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



class Python25Mapper_GetAddress_NonApi_Test(TestCase):
    
    @WithMapper
    def assertGetAddressWorks(self, name, mapper, _):
        fp1 = mapper.GetAddress(name)
        fp2 = mapper.GetAddress(name)
        self.assertNotEquals(fp1, IntPtr.Zero, "did not get address")
        self.assertEquals(fp1, fp2, "did not remember func ptrs")


    def testMethods(self):
        methods = (
            "IC_PyFloat_New",
            "IC_PyInt_New",
            "IC_PyType_New",
            
            "IC_PyBaseObject_Init",
            "IC_PyDict_Init",
            
            "IC_PyString_Str",
            "IC_PyString_Concat_Core",
            
            "IC_PyBaseObject_Dealloc",
            "IC_PyList_Dealloc",
            "IC_PySlice_Dealloc",
            "IC_PyTuple_Dealloc",
            "IC_PyInstance_Dealloc",
        )
        for method in methods:
            self.assertGetAddressWorks(method)


class Python25Mapper_NoneTest(TestCase):
    
    @WithMapper
    def testFillNone(self, mapper, _):
        nonePtr = mapper._Py_NoneStruct
        noneStruct = Marshal.PtrToStructure(nonePtr, PyObject)
        self.assertEquals(noneStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(noneStruct.ob_type, mapper.PyNone_Type, "unexpected type")


    @WithMapper
    def testStoreNone(self, mapper, _):
        resultPtr = mapper.Store(None)
        self.assertEquals(resultPtr, mapper._Py_NoneStruct, "wrong")
        self.assertEquals(mapper.RefCount(resultPtr), 2, "did not incref")
        self.assertEquals(mapper.Retrieve(resultPtr), None, "not mapped properly")


class Python25Mapper_NotImplementedTest(TestCase):
    
    @WithMapper
    def testFillNotImplemented(self, mapper, _):
        niPtr = mapper._Py_NotImplementedStruct
        niStruct = Marshal.PtrToStructure(niPtr, PyObject)
        self.assertEquals(niStruct.ob_refcnt, 1, "bad refcount")
        self.assertEquals(niStruct.ob_type, mapper.PyNotImplemented_Type, "unexpected type")


    @WithMapper
    def testStoreNotImplemented(self, mapper, _):
        resultPtr = mapper.Store(NotImplemented)
        self.assertEquals(resultPtr, mapper._Py_NotImplementedStruct, "wrong")
        self.assertEquals(mapper.RefCount(resultPtr), 2, "did not incref")
        self.assertEquals(mapper.Retrieve(resultPtr), NotImplemented, "not mapped properly")



class Python25Mapper_Py_OptimizeFlag_Test(TestCase):

    @WithMapper
    def testFills(self, mapper, addToCleanUp):
        # TODO: if we set a lower value, numpy will crash inside arr_add_docstring
        # I consider docstrings to be low-priority-enough that it's OK to fudge this
        # for now. also, fixing it would be hard ;).
        flagPtr = Marshal.AllocHGlobal(Marshal.SizeOf(Int32))
        addToCleanUp(lambda: Marshal.FreeHGlobal(flagPtr))
        mapper.SetData("Py_OptimizeFlag", flagPtr)
        
        self.assertEquals(CPyMarshal.ReadInt(flagPtr), 2)



suite = makesuite(
    Python25Mapper_CreateDestroy_Test,
    Python25Mapper_References_Test,
    Python25Mapper_GetAddress_NonApi_Test,
    Python25Mapper_NoneTest,
    Python25Mapper_NotImplementedTest,
    Python25Mapper_Py_OptimizeFlag_Test,
)

if __name__ == '__main__':
    run(suite)
