import os
import sys

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes, PtrToStructure
from tests.utils.pythonmapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase, WithMapper

from System import Int32, IntPtr, InvalidOperationException, NullReferenceException, Type, WeakReference
from System.Collections.Generic import Stack, List
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    BadRefCountException, CannotInterpretException, CPyMarshal, dgt_void_ptr, dgt_void_void,
    HGlobalAllocator, PythonMapper, Unmanaged, UnmanagedDataMarker
)
from Ironclad.Structs import PyObject, PyTypeObject

PYTHON_DLL = "python34.dll"
DLL_PATH = os.path.join("build", "ironclad", PYTHON_DLL)

class PythonMapper_CreateDestroy_Test(TestCase):
    
    def testCreateDestroy(self):
        mapper = PythonMapper()
        self.assertEqual(mapper.Alive, True)
        mapper.Dispose()
        self.assertEqual(mapper.Alive, False)
        mapper.Dispose()
        # jolly good, didn't crash
        
    
    def testLoadsStubWhenPassedPathAndUnloadsOnDispose(self):
        mapper = PythonMapper(DLL_PATH)
        try:
            self.assertNotEqual(Unmanaged.GetModuleHandle(PYTHON_DLL), IntPtr.Zero,
                                 "library not mapped by construction")
            self.assertNotEqual(PythonMapper._Py_NoneStruct, IntPtr.Zero,
                                 "mapping not set up")

            # weak side-effect test to hopefully prove that ReadyBuiltinTypes has been called
            self.assertEqual(CPyMarshal.ReadPtrField(mapper.PyLong_Type, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)

            mapper.Dispose()
            self.assertEqual(Unmanaged.GetModuleHandle(PYTHON_DLL), IntPtr.Zero,
                              "library not unmapped by Dispose")
        finally:
            mapper.Dispose()
        
    
    def testLoadsModuleAndUnloadsOnDispose(self):
        mapper = PythonMapper(DLL_PATH)
        try:
            origcwd = os.getcwd()
            mapper.LoadModule(os.path.join("tests", "data", "setvalue.pyd"), "some.module")
            self.assertEqual(os.getcwd(), origcwd, "failed to restore working directory")
            self.assertNotEqual(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                                 "library not mapped by construction")

            mapper.Dispose()
            self.assertEqual(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                              "library not unmapped by Dispose")
            self.assertEqual(Unmanaged.GetModuleHandle(PYTHON_DLL), IntPtr.Zero,
                              "library not unmapped by Dispose")
        finally:
            mapper.Dispose()
    
    
    def testRemovesMmapOnDispose(self):
        mapper = PythonMapper(DLL_PATH)
        try:
            sys.modules['csv'] = object()
            mapper.Dispose()
            self.assertFalse('mmap' in sys.modules)
            self.assertFalse('_csv' in sys.modules)
            self.assertFalse('csv' in sys.modules)
        finally:
            mapper.Dispose()
    
    
    def testFreesObjectsOnDispose(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        
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
        
        mapper = PythonMapper()
        self.assertEqual(mapper.Py_AtExit(MangleCall('foo')), 0)
        self.assertEqual(mapper.Py_AtExit(MangleCall('bar')), 0)
        self.assertEqual(calls, [])
        mapper.Dispose()
        self.assertEqual(calls, ['bar', 'foo'])
    
    
    def testDestroysObjectsOfUnmanagedTypesFirst(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
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
        self.assertEqual(frees.index(hardptr) < frees.index(easyptr), True, "failed to dealloc in correct order")
        self.assertEqual(calls, [('del', hardptr)], "failed to clean up klass instance")
        
        deallocType()
        deallocTypes()
    
    
    def testIgnoresBridgeObjectsNotAllocatedByAllocator(self):
        obj = object()
        ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject()))
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        
        mapper = PythonMapper()
        mapper.StoreBridge(ptr, obj)
        mapper.Dispose()
        # attempting to free ptr would have failed


class PythonMapper_References_Test(TestCase):

    def testBasicStoreRetrieveFree(self):
        frees = []
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        obj1 = object()
        ptr = mapper.Store(obj1)
        self.assertEqual(len(allocs), 1, "unexpected number of allocations")
        self.assertEqual(allocs[0], (ptr, Marshal.SizeOf(PyObject())), "unexpected result")
        self.assertNotEqual(ptr, IntPtr.Zero, "did not store reference")
        self.assertEqual(mapper.RefCount(ptr), 1, "unexpected refcount")
        self.assertEqual(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), 
                          mapper.PyBaseObject_Type, 
                          "nearly-opaque pointer had wrong type")

        obj2 = mapper.Retrieve(ptr)
        self.assertTrue(obj1 is obj2, "retrieved wrong object")

        self.assertEqual(frees, [], "unexpected deallocations")
        mapper.PyObject_Free(ptr)
        self.assertEqual(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))
        
        mapper.Dispose()
        deallocTypes()


    def testCanFreeWithRefCount0(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        
        objPtr = mapper.Store(object())
        CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 0)
        
        mapper.PyObject_Free(objPtr)
        self.assertEqual(frees, [objPtr], "didn't actually release memory")
        mapper.Dispose()
        

    def testStoreSameObjectIncRefsOriginal(self):
        frees = []
        allocs = []
        mapper = PythonMapper(GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
        del allocs[:]
        obj1 = object()
        result1 = mapper.Store(obj1)
        result2 = mapper.Store(obj1)
        
        self.assertEqual(allocs, [(result1, Marshal.SizeOf(PyObject()))], "unexpected result")
        self.assertEqual(result1, result2, "did not return same ptr")
        self.assertEqual(mapper.RefCount(result1), 2, "did not incref")
        
        mapper.DecRef(result1)
        
        del frees[:]
        mapper.DecRef(result1)
        self.assertEqual(frees, [result1], "did not free memory")
        
        result3 = mapper.Store(obj1)
        self.assertEqual(allocs, 
                          [(result1, Marshal.SizeOf(PyObject())), (result3, Marshal.SizeOf(PyObject()))], 
                          "unexpected result -- failed to clear reverse mapping?")
        mapper.Dispose()
        deallocTypes()
        

    @WithMapper
    def testStoreEqualObjectStoresSeparately(self, mapper, _):
        result1 = mapper.Store([1, 2, 3])
        result2 = mapper.Store([1, 2, 3])
        
        self.assertNotEqual(result1, result2, "confused separate objects")
        self.assertEqual(mapper.RefCount(result1), 1, "wrong")
        self.assertEqual(mapper.RefCount(result2), 1, "wrong")


    @WithMapper
    def testEqualFloatsIntsStoredSeparately(self, mapper, _):
        result1 = mapper.Store(0)
        result2 = mapper.Store(0.0)
        
        self.assertNotEqual(result1, result2, "confused separate objects")
        self.assertEqual(mapper.RefCount(result1), 1, "wrong")
        self.assertEqual(mapper.RefCount(result2), 1, "wrong")


    def testDecRefObjectWithZeroRefCountFails(self):
        allocator = HGlobalAllocator()
        mapper = PythonMapper(allocator)
        deallocTypes = CreateTypes(mapper)

        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        objPtr = allocator.Alloc(IntPtr(Marshal.SizeOf(PyObject())))
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_refcnt", 0)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", mapper.PyBaseObject_Type)
        mapper.StoreBridge(objPtr, object())

        self.assertRaisesClr(BadRefCountException, lambda: mapper.DecRef(objPtr))
        mapper.Dispose()
        deallocTypes()


    @WithMapper
    def testFinalDecRefOfObjectWithTypeCalls_tp_dealloc(self, mapper, _):
        calls = []
        def TypeDealloc(ptr):
            calls.append(ptr)
        deallocDgt = dgt_void_ptr(TypeDealloc)
        deallocFP = Marshal.GetFunctionPointerForDelegate(deallocDgt)
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        deallocPtr = CPyMarshal.Offset(typePtr, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
        CPyMarshal.WritePtr(deallocPtr, deallocFP)
        
        obj = object()
        objPtr = mapper.Store(obj)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)
        
        mapper.IncRef(objPtr)
        mapper.DecRef(objPtr)
        self.assertEqual(calls, [], "called prematurely")
        mapper.DecRef(objPtr)
        self.assertEqual(calls, [objPtr], "not called when refcount hit 0")


    def testFinalDecRefComplainsAboutMissing_tp_dealloc(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)

        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_dealloc", IntPtr.Zero)

        obj = object()
        objPtr = mapper.Store(obj)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)

        mapper.IncRef(objPtr)

        del frees [:]
        mapper.DecRef(objPtr)
        self.assertEqual(frees, [], "freed prematurely")
        self.assertRaisesClr(CannotInterpretException, mapper.DecRef, objPtr)

        mapper.Dispose()
        deallocTypes()


    def testStoreBridge(self):
        allocator = HGlobalAllocator()
        mapper = PythonMapper(allocator)
        deallocTypes = CreateTypes(mapper)
        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(IntPtr(Marshal.SizeOf(PyObject())))
        
        try:
            def do():
                # see NOTE in interestingptrmaptest
                obj = object()
                ref = WeakReference(obj)
                CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
                CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
                mapper.StoreBridge(ptr, obj)

                self.assertEqual(mapper.Retrieve(ptr), obj, "object not stored")
                self.assertEqual(mapper.Store(obj), ptr, "object not reverse-mapped")

                mapper.Weaken(obj)
                CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)

                mapper.IncRef(ptr)
                del obj
                return ref
            ref = do()
            gcwait()
            self.assertEqual(ref.IsAlive, True, "was not strengthened by IncRef")

            mapper.DecRef(ptr)
            gcwait()
            self.assertEqual(ref.IsAlive, False, "was not weakened by DecRef")

        finally:
            # need to dealloc ptr ourselves, it doesn't happen automatically
            # except for objects with Dispatchers
            mapper.IC_PyBaseObject_Dealloc(ptr)
            mapper.Dispose()
            deallocTypes()
    

    def testStrengthenWeakenUnmanagedInstance(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = PythonMapper(allocator)
        deallocTypes = CreateTypes(mapper)

        # need to use same allocator as mapper, otherwise it gets upset on shutdown
        ptr = allocator.Alloc(IntPtr(Marshal.SizeOf(PyObject())))
        
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
            self.assertEqual(ref.IsAlive, True, "was not strongly referenced")

            def do2():
                obj = ref.Target
                mapper.Weaken(obj)
                del obj
            do2()
            gcwait()
            self.assertRaisesClr(NullReferenceException, mapper.Retrieve, ptr)
        
        finally:
            # need to dealloc ptr ourselves, it doesn't hapen automatically
            # except for objects with Dispatchers
            mapper.IC_PyBaseObject_Dealloc(ptr)
            mapper.Dispose()
            deallocTypes()


    def testReleaseGILChecksBridgePtrs(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = PythonMapper(allocator)
        deallocTypes = CreateTypes(mapper)

        # force no throttling of cleanup
        mapper.GCThreshold = 0

        def do1():
            obj = object()
            ref = WeakReference(obj)
            # need to use same allocator as mapper, otherwise it gets upset on shutdown
            ptr = allocator.Alloc(IntPtr(Marshal.SizeOf(PyObject())))
            CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 2)
            CPyMarshal.WritePtrField(ptr, PyObject, "ob_type", mapper.PyBaseObject_Type)
            mapper.StoreBridge(ptr, obj)

            # refcount > 1 means ref should have been strengthened
            del obj
            return ref, ptr
        ref, ptr = do1()
        gcwait()
        self.assertEqual(ref.IsAlive, True, "was reaped unexpectedly (refcount was 2)")

        CPyMarshal.WriteIntField(ptr, PyObject, "ob_refcnt", 1)
        mapper.EnsureGIL()
        mapper.ReleaseGIL()

        # refcount < 2 should have been weakened
        gcwait()
        self.assertRaisesClr(NullReferenceException, mapper.Retrieve, ptr)

        # need to dealloc ptr ourselves, it doesn't hapen automatically
        # except for objects with Dispatchers
        mapper.IC_PyBaseObject_Dealloc(ptr)
        mapper.Dispose()
        deallocTypes()


    @WithMapper
    def testCannotStoreUnmanagedDataMarker(self, mapper, _):
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyBytesObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyTupleObject))
        self.assertRaises(TypeError, lambda: mapper.Store(UnmanagedDataMarker.PyListObject))


    def testRefCountIncRefDecRef(self):
        frees = []
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = PythonMapper(allocator)
        deallocTypes = CreateTypes(mapper)

        obj1 = object()
        ptr = mapper.Store(obj1)
        self.assertEqual(mapper.HasPtr(ptr), True)

        mapper.IncRef(ptr)
        self.assertEqual(mapper.RefCount(ptr), 2, "unexpected refcount")
        self.assertEqual(mapper.HasPtr(ptr), True)

        del frees[:]
        mapper.DecRef(ptr)
        self.assertEqual(mapper.RefCount(ptr), 1, "unexpected refcount")
        self.assertEqual(mapper.HasPtr(ptr), True)
        self.assertEqual(frees, [], "unexpected deallocations")

        mapper.DecRef(ptr)
        self.assertEqual(mapper.HasPtr(ptr), False)
        self.assertEqual(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.PyObject_Free(ptr))

        mapper.Dispose()
        deallocTypes()


    def testNullPointers(self):
        allocator = GetDoNothingTestAllocator([])
        mapper = PythonMapper(allocator)
        self.assertEqual(mapper.HasPtr(IntPtr.Zero), False)
        self.assertRaisesClr(CannotInterpretException, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaisesClr(CannotInterpretException, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaisesClr(CannotInterpretException, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaisesClr(CannotInterpretException, lambda: mapper.RefCount(IntPtr.Zero))
        mapper.Dispose()


    @WithMapper
    def testRememberAndFreeTempObjects(self, mapper, _):
        tempObject1 = mapper.Store(1)
        tempObject2 = mapper.Store(2)

        mapper.DecRefLater(tempObject1)
        mapper.DecRefLater(tempObject2)

        self.assertEqual(mapper.RefCount(tempObject1), 1,
                          "DecRefLater should not change refcnt")
        self.assertEqual(mapper.RefCount(tempObject2), 1,
                          "DecRefLater should not change refcnt")

        mapper.IncRef(tempObject1)
        mapper.IncRef(tempObject2)

        mapper.ReleaseGIL()
        self.assertEqual(mapper.RefCount(tempObject1), 1,
                          "ReleaseGIL should decref temp objects rather than freeing them")
        self.assertEqual(mapper.RefCount(tempObject2), 1,
                          "ReleaseGIL should decref temp objects rather than freeing them")
                          
        mapper.EnsureGIL()
        mapper.ReleaseGIL()
        self.assertEqual(mapper.RefCount(tempObject1), 1,
                          "ReleaseGIL should clear list once called")
        self.assertEqual(mapper.RefCount(tempObject2), 1,
                          "ReleaseGIL should clear list once called")
        mapper.EnsureGIL()


    def testReleaseGilDoesntExplodeIfTempObjectsEmpty(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        mapper.tempObjects = Stack[List[IntPtr]]()
        try:
            mapper.ReleaseGIL()
        except InvalidOperationException:
            self.fail('ReleaseGIL should not throw StackEmpty if tempObjects is empty')
        except Exception:
            pass
        finally:
            mapper.Dispose()


    def testReleaseGilDoesntExplodeIfTempObjectsContainsNull(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        mapper.tempObjects = Stack[List[IntPtr]]()
        mapper.tempObjects.Push(None)
        try:
            mapper.ReleaseGIL()
        except SystemError:
            self.fail('ReleaseGIL should not throw NullReference if tempObjects contains None')
        except Exception:
            pass
        finally:
            mapper.Dispose()


    def testDecRefLaterSurvivesEmptyStack(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        mapper.tempObjects = Stack[List[IntPtr]]()
        try:
            mapper.DecRefLater(IntPtr.Zero)
        except InvalidOperationException:
            self.fail('DecRefLater should not throw StackEmpty if tempObjects is empty')
        finally:
            mapper.Dispose()


    def testDecRefLaterSurvivesNoneOnStack(self):
        frees = []
        mapper = PythonMapper(GetAllocatingTestAllocator([], frees))
        mapper.tempObjects = Stack[List[IntPtr]]()
        mapper.tempObjects.Push(None)
        try:
            mapper.DecRefLater(IntPtr.Zero)
        except SystemError:
            self.fail('DecRefLater should not throw NullReference if tempObjects contains None')
        finally:
            mapper.Dispose()


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
        for i in range(100000):
            obj = GetObject(i)
            ptr = mapper.Store(obj)
            ptrs[ptr] = obj
        
        for k, v in ptrs.items():
            self.assertEqual(mapper.Retrieve(k), v, "failed to retrieve")
            mapper.DecRef(k)



class PythonMapper_GetFuncPtr_NonApi_Test(TestCase):
    
    @WithMapper
    def assertGetFuncPtrWorks(self, name, mapper, _):
        fp1 = mapper.GetFuncPtr(name)
        fp2 = mapper.GetFuncPtr(name)
        self.assertNotEqual(fp1, IntPtr.Zero, "did not get address")
        self.assertEqual(fp1, fp2, "did not remember func ptrs")


    def testMethods(self):
        methods = (
            "IC_PyFloat_New",
            "IC_PyType_New",
            
            "IC_PyBaseObject_Init",
            "IC_PyDict_Init",
            
            "IC_PyBytes_Str",
            "IC_PyBytes_Concat_Core",
            
            "IC_PyBaseObject_Dealloc",
            "IC_PyList_Dealloc",
            "IC_PySlice_Dealloc",
            "IC_PyTuple_Dealloc",
        )
        for method in methods:
            self.assertGetFuncPtrWorks(method)


class PythonMapper_NoneTest(TestCase):
    
    @WithMapper
    def testFillNone(self, mapper, _):
        nonePtr = mapper._Py_NoneStruct
        noneStruct = PtrToStructure(nonePtr, PyObject)
        self.assertEqual(noneStruct.ob_refcnt, 1, "bad refcount")
        self.assertEqual(noneStruct.ob_type, mapper._PyNone_Type, "unexpected type")


    @WithMapper
    def testStoreNone(self, mapper, _):
        resultPtr = mapper.Store(None)
        self.assertEqual(resultPtr, mapper._Py_NoneStruct, "wrong")
        self.assertEqual(mapper.RefCount(resultPtr), 2, "did not incref")
        self.assertEqual(mapper.Retrieve(resultPtr), None, "not mapped properly")


class PythonMapper_NotImplementedTest(TestCase):
    
    @WithMapper
    def testFillNotImplemented(self, mapper, _):
        niPtr = mapper._Py_NotImplementedStruct
        niStruct = PtrToStructure(niPtr, PyObject)
        self.assertEqual(niStruct.ob_refcnt, 1, "bad refcount")
        self.assertEqual(niStruct.ob_type, mapper._PyNotImplemented_Type, "unexpected type")


    @WithMapper
    def testStoreNotImplemented(self, mapper, _):
        resultPtr = mapper.Store(NotImplemented)
        self.assertEqual(resultPtr, mapper._Py_NotImplementedStruct, "wrong")
        self.assertEqual(mapper.RefCount(resultPtr), 2, "did not incref")
        self.assertEqual(mapper.Retrieve(resultPtr), NotImplemented, "not mapped properly")



class PythonMapper_Py_OptimizeFlag_Test(TestCase):

    @WithMapper
    def testFills(self, mapper, addToCleanUp):
        # TODO: if we set a lower value, numpy will crash inside arr_add_docstring
        # I consider docstrings to be low-priority-enough that it's OK to fudge this
        # for now. also, fixing it would be hard ;).
        flagPtr = Marshal.AllocHGlobal(Marshal.SizeOf(Int32()))
        addToCleanUp(lambda: Marshal.FreeHGlobal(flagPtr))
        mapper.RegisterData("Py_OptimizeFlag", flagPtr)
        
        self.assertEqual(CPyMarshal.ReadInt(flagPtr), 2)



suite = makesuite(
    PythonMapper_CreateDestroy_Test,
    PythonMapper_References_Test,
    PythonMapper_GetFuncPtr_NonApi_Test,
    PythonMapper_NoneTest,
    PythonMapper_NotImplementedTest,
    PythonMapper_Py_OptimizeFlag_Test,
)

if __name__ == '__main__':
    run(suite)
