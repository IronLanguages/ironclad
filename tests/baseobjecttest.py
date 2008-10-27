
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Api, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject

    
    
class ObjectFunctionsTest(TestCase):
    
    def testPyObject_Call(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        kallablePtr = mapper.Store(lambda x, y=2: x * y)
        argsPtr = mapper.Store((4,))
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(resultPtr), 8, "didn't call")
        
        kwargsPtr = mapper.Store({'y': 4})
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, kwargsPtr)
        self.assertEquals(mapper.Retrieve(resultPtr), 16, "didn't call with kwargs")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyObject_Call_noargs(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        kallablePtr = mapper.Store(lambda: 2)
        resultPtr = mapper.PyObject_Call(kallablePtr, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(resultPtr), 2, "didn't call")
            
        mapper.Dispose()
        deallocTypes()


    def testPyCallable_Check(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        callables = map(mapper.Store, [float, len, lambda: None])
        notCallables = map(mapper.Store, ["hullo", 33, ])
        
        for x in callables:
            self.assertEquals(mapper.PyCallable_Check(x), 1, "reported not callable")
        for x in notCallables:
            self.assertEquals(mapper.PyCallable_Check(x), 0, "reported callable")
                
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "bob")
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "ben")
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, according to spec")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttr(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("bob"))
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("ben"))
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, assuming this matches GetAttrString")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), 0)
        self.assertEquals(obj.bob, 123)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttrString_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        objPtr = mapper.Store(object())
        self.assertEquals(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), -1)
        self.assertMapperHasError(mapper, AttributeError)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttr(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.PyObject_SetAttr(objPtr, mapper.Store("bob"), mapper.Store(123)), 0)
        self.assertEquals(obj.bob, 123)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttr_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertEquals(mapper.PyObject_SetAttr(mapper.Store(object()), mapper.Store("bob"), mapper.Store(123)), -1)
        self.assertMapperHasError(mapper, AttributeError)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_HasAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        self.assertEquals(mapper.PyObject_HasAttrString(objPtr, "bob"), 1)
        self.assertEquals(mapper.PyObject_HasAttrString(objPtr, "jim"), 0)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetItem(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        result = object()
        class Subscriptable(object):
            def __getitem__(self, key):
                return result
        
        objPtr = mapper.Store(Subscriptable())
        keyPtr = mapper.Store(object())
        resultPtr = mapper.Store(result)
        
        self.assertEquals(mapper.PyObject_GetItem(objPtr, keyPtr), resultPtr)
        self.assertEquals(mapper.RefCount(resultPtr), 2, "failed to incref return value")
        
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetItem_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        obj = object()
        objPtr = mapper.Store(obj)
        
        self.assertEquals(mapper.PyObject_GetItem(objPtr, mapper.Store(1)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        mapper.Dispose()
        deallocTypes()


    def testPyObject_IsTrue(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for trueval in ("hullo", 33, -1.5, True, [0], (0,), {1:2}, object()):
            ptr = mapper.Store(trueval)
            self.assertEquals(mapper.PyObject_IsTrue(ptr), 1)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
        
        for falseval in ('', 0, 0.0, False, [], tuple(), {}):
            ptr = mapper.Store(falseval)
            self.assertEquals(mapper.PyObject_IsTrue(ptr), 0)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
            
        class MyError(Exception):
            pass
        class ErrorBool(object):
            def __len__(self):
                raise MyError()
                
        ptr = mapper.Store(ErrorBool())
        self.assertEquals(mapper.PyObject_IsTrue(ptr), -1)
        self.assertMapperHasError(mapper, MyError)
        mapper.DecRef(ptr)
        
        mapper.Dispose()
        deallocTypes()


    def testPyObject_Size(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for okval in ("hullo", [0, 3, 5], (0,), {1:2}, set([1, 2])):
            ptr = mapper.Store(okval)
            self.assertEquals(mapper.PyObject_Size(ptr), len(okval))
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
        
        for badval in (0, 0.0, False, object, object()):
            ptr = mapper.Store(badval)
            mapper.LastException = None
            self.assertEquals(mapper.PyObject_Size(ptr), -1)
            self.assertMapperHasError(mapper, TypeError)
            mapper.DecRef(ptr)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_StrRepr(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for okval in ("hullo", [0, 3, 5], (0,), {1:2}, set([1, 2])):
            ptr = mapper.Store(okval)
            strptr = mapper.PyObject_Str(ptr)
            self.assertEquals(mapper.Retrieve(strptr), str(okval))
            self.assertEquals(mapper.LastException, None)
            reprptr = mapper.PyObject_Repr(ptr)
            self.assertEquals(mapper.Retrieve(reprptr), repr(okval))
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
            mapper.DecRef(strptr)
            mapper.DecRef(reprptr)
        
        class BadStr(object):
            def __str__(self):
                raise TypeError('this object cannot be represented in your puny alphabet')
            def __repr__(self):
                raise TypeError('this object cannot be represented in your puny alphabet')
        
        badptr = mapper.Store(BadStr())
        self.assertEquals(mapper.PyObject_Str(badptr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        self.assertEquals(mapper.PyObject_Repr(badptr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        mapper.DecRef(ptr)
            
        mapper.Dispose()
        deallocTypes()
        
    
    
class PyBaseObject_Type_Test(TypeTestCase):

    def testPyBaseObject_Type_fields(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        def AssertPtrField(name, value):
            field = CPyMarshal.ReadPtrField(mapper.PyBaseObject_Type, PyTypeObject, name)
            self.assertNotEquals(field, IntPtr.Zero)
            self.assertEquals(field, value)
        
        AssertPtrField("tp_new", mapper.GetAddress("PyType_GenericNew"))
        AssertPtrField("tp_alloc", mapper.GetAddress("PyType_GenericAlloc"))
        AssertPtrField("tp_init", mapper.GetAddress("PyBaseObject_Init"))
        AssertPtrField("tp_dealloc", mapper.GetAddress("PyBaseObject_Dealloc"))
        AssertPtrField("tp_free", mapper.GetAddress("PyObject_Free"))
        
        AssertPtrField("tp_str", mapper.GetAddress("PyObject_Str"))
        
        mapper.Dispose()
        deallocTypes()


    def testPyBaseObject_Type_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyBaseObject_Type")


    def testPyBaseObject_Type_tp_free(self):
        self.assertUsual_tp_free("PyBaseObject_Type")
            
    
    def testPyBaseObject_TypeDeallocCallsObjTypesFreeFunction(self):
        calls = []
        def Some_FreeFunc(objPtr):
            calls.append(objPtr)
        self.freeDgt = Python25Api.PyObject_Free_Delegate(Some_FreeFunc)
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        baseObjTypeBlock = mapper.PyBaseObject_Type
        objTypeBlock = mapper.PyDict_Type # type not actually important
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        
        CPyMarshal.WriteFunctionPtrField(objTypeBlock, PyTypeObject, "tp_free", self.freeDgt)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", objTypeBlock)
        gcwait() # this should make the function pointers invalid if we forgot to store references to the delegates

        mapper.PyBaseObject_Dealloc(objPtr)
        self.assertEquals(calls, [objPtr], "wrong calls")
            
        mapper.Dispose()
        deallocTypes()
        Marshal.FreeHGlobal(objPtr)


class NewInitFunctionsTest(TestCase):
    
    def testPyObject_Init(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'FooType'})
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        
        self.assertEquals(mapper.PyObject_Init(objPtr, typePtr), objPtr, 'did not return the "new instance"')
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type"), typePtr, "wrong type")
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PyObject, "ob_refcnt"), 1, "wrong refcount")
        self.assertEquals(mapper.HasPtr(objPtr), False)
        
        mapper.Dispose()
        Marshal.FreeHGlobal(objPtr)
        deallocType()
        deallocTypes()


    def testPyBaseObject_Init(self):
        "this function shouldn't do anything..."
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertEquals(mapper.PyBaseObject_Init(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero), 0)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def test_PyObject_New(self):
        allocs = []
        allocator = GetAllocatingTestAllocator(allocs, [])
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        typeObjSize = Marshal.SizeOf(PyTypeObject)
        typePtr = Marshal.AllocHGlobal(typeObjSize)
        CPyMarshal.Zero(typePtr, typeObjSize)
        CPyMarshal.WriteIntField(typePtr, PyTypeObject, "ob_size", 31337)
        
        del allocs[:]
        objPtr = mapper._PyObject_New(typePtr)
        self.assertEquals(allocs, [(objPtr, 31337)])
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PyObject, 'ob_type'), typePtr)
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PyObject, 'ob_refcnt'), 1)
        self.assertEquals(mapper.HasPtr(objPtr), False)
        
        mapper.Dispose()
        deallocTypes()
        

suite = makesuite(
    ObjectFunctionsTest,
    PyBaseObject_Type_Test,
    NewInitFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
