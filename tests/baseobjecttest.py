
import operator

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Api, Python25Mapper
from Ironclad.Structs import CMP, PyObject, PyTypeObject


COMPARISONS = {
    CMP.Py_LT: operator.lt,
    CMP.Py_LE: operator.le,
    CMP.Py_EQ: operator.eq,
    CMP.Py_NE: operator.ne,
    CMP.Py_GT: operator.gt,
    CMP.Py_GE: operator.ge
}
    
class ObjectFunctionsTest(TestCase):
    
    @WithMapper
    def testPyObject_Call(self, mapper, _):
        kallablePtr = mapper.Store(lambda x, y=2: x * y)
        argsPtr = mapper.Store((4,))
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(resultPtr), 8, "didn't call")
        
        kwargsPtr = mapper.Store({'y': 4})
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, kwargsPtr)
        self.assertEquals(mapper.Retrieve(resultPtr), 16, "didn't call with kwargs")


    @WithMapper
    def testPyObject_Call_noargs(self, mapper, _):
        kallablePtr = mapper.Store(lambda: 2)
        resultPtr = mapper.PyObject_Call(kallablePtr, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(resultPtr), 2, "didn't call")


    @WithMapper
    def testPyCallable_Check(self, mapper, _):
        callables = map(mapper.Store, [float, len, lambda: None])
        notCallables = map(mapper.Store, ["hullo", 33, ])
        
        for x in callables:
            self.assertEquals(mapper.PyCallable_Check(x), 1, "reported not callable")
        for x in notCallables:
            self.assertEquals(mapper.PyCallable_Check(x), 0, "reported callable")


    @WithMapper
    def testPyObject_Compare(self, mapper, _):
        objects = (1, 1, 1.0, -1, 3.4e5, object, object(), 'hello', [1], (2,), {3: 'four'})
        
        for obj1 in objects:
            for obj2 in objects:
                self.assertEquals(mapper.PyObject_Compare(mapper.Store(obj1), mapper.Store(obj2)),
                                  cmp(obj1, obj2), "%r, %r" % (obj1, obj2))


    def assertRichCmp(self, mapper, opid, ob1, ob2):
        op = COMPARISONS[opid]
        expect = -1
        error = None
        try:
            expect = op(ob1, ob2)
        except Exception, e:
            error = e.__class__

        result = mapper.PyObject_RichCompareBool(mapper.Store(ob1), mapper.Store(ob2), int(opid))
        self.assertEquals(result, expect, "%r: %r %r" % (op.__name__, ob1, ob2))
        self.assertMapperHasError(mapper, error)
        

    @WithMapper
    def testPyObject_RichCompareBool(self, mapper, _):
        class BadComparer(object):
            def borked(self, other):
                raise Exception("no!")
            __lt__ = __le__ = __eq__ = __ne__ = __gt__ = __ge__ = borked
        objects = (1, 1, 1.0, -1, 3.4e5, object, object(), 'hello', [1], (2,), {3: 'four'}, BadComparer)
        
        for opid in COMPARISONS:
            for ob1 in objects:
                for ob2 in objects:
                    self.assertRichCmp(mapper, opid, ob1, ob2)
                       

    @WithMapper
    def testPyObject_GetAttrString(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "bob")
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")


    @WithMapper
    def testPyObject_GetAttrStringFailure(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "ben")
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, according to spec")


    @WithMapper
    def testPyObject_GetAttr(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("bob"))
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")


    @WithMapper
    def testPyObject_GetAttrStringFailure(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("ben"))
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, assuming this matches GetAttrString")


    @WithMapper
    def testPyObject_SetAttrString(self, mapper, _):
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), 0)
        self.assertEquals(obj.bob, 123)


    @WithMapper
    def testPyObject_SetAttrString_Failure(self, mapper, _):
        objPtr = mapper.Store(object())
        self.assertEquals(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), -1)
        self.assertMapperHasError(mapper, AttributeError)


    @WithMapper
    def testPyObject_SetAttr(self, mapper, _):
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.PyObject_SetAttr(objPtr, mapper.Store("bob"), mapper.Store(123)), 0)
        self.assertEquals(obj.bob, 123)


    @WithMapper
    def testPyObject_SetAttr_Failure(self, mapper, _):
        self.assertEquals(mapper.PyObject_SetAttr(mapper.Store(object()), mapper.Store("bob"), mapper.Store(123)), -1)
        self.assertMapperHasError(mapper, AttributeError)


    @WithMapper
    def testPyObject_HasAttrString(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        self.assertEquals(mapper.PyObject_HasAttrString(objPtr, "bob"), 1)
        self.assertEquals(mapper.PyObject_HasAttrString(objPtr, "jim"), 0)


    @WithMapper
    def testPyObject_GetItem(self, mapper, _):
        result = object()
        class Subscriptable(object):
            def __getitem__(self, key):
                return result
        
        objPtr = mapper.Store(Subscriptable())
        keyPtr = mapper.Store(object())
        resultPtr = mapper.Store(result)
        
        self.assertEquals(mapper.PyObject_GetItem(objPtr, keyPtr), resultPtr)
        self.assertEquals(mapper.RefCount(resultPtr), 2, "failed to incref return value")


    @WithMapper
    def testPyObject_GetItem_Failure(self, mapper, _):
        obj = object()
        objPtr = mapper.Store(obj)
        
        self.assertEquals(mapper.PyObject_GetItem(objPtr, mapper.Store(1)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyObject_IsTrue(self, mapper, _):
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


    @WithMapper
    def testPyObject_Size(self, mapper, _):
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


    @WithMapper
    def testPyObject_StrRepr(self, mapper, _):
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


    @WithMapper
    def testPyObject_IsInstance(self, mapper, _):
        class Custom(object):
            pass
        
        data = (
            (object(), object), # true
            ('hello', str),
            (123, (str, object)),
            (Custom(), Custom),
            (Custom, type),
            
            (123, str), # false
            ('foo', list),
            (Custom, Custom),
            
            ('foo', 'bar'), # error
            (Custom, Custom()),
        )
        
        for (inst, cls) in data:
            expectResult = -1
            expectException = None
            try:
                expectResult = int(isinstance(inst, cls))
            except Exception, e:
                expectException = type(e)
            
            instPtr = mapper.Store(inst)
            clsPtr = mapper.Store(cls)
            self.assertEquals(mapper.PyObject_IsInstance(instPtr, clsPtr), expectResult)
            self.assertMapperHasError(mapper, expectException)
            mapper.DecRef(instPtr)
            mapper.DecRef(clsPtr)
        

    
class PyBaseObject_Type_Test(TypeTestCase):

    @WithMapper
    def testPyBaseObject_Type_fields(self, mapper, _):
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


    def testPyBaseObject_Type_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyBaseObject_Type")


    def testPyBaseObject_Type_tp_free(self):
        self.assertUsual_tp_free("PyBaseObject_Type")
            
    
    @WithMapper
    def testPyBaseObject_TypeDeallocCallsObjTypesFreeFunction(self, mapper, addToCleanUp):
        calls = []
        def Some_FreeFunc(objPtr):
            calls.append(objPtr)
        self.freeDgt = Python25Api.PyObject_Free_Delegate(Some_FreeFunc)
        
        baseObjTypeBlock = mapper.PyBaseObject_Type
        objTypeBlock = mapper.PyDict_Type # type not actually important
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(objPtr))

        CPyMarshal.WriteFunctionPtrField(objTypeBlock, PyTypeObject, "tp_free", self.freeDgt)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", objTypeBlock)
        gcwait() # this should make the function pointers invalid if we forgot to store references to the delegates

        mapper.PyBaseObject_Dealloc(objPtr)
        self.assertEquals(calls, [objPtr], "wrong calls")


class NewInitFunctionsTest(TestCase):
    
    @WithMapper
    def testPyObject_Init(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'FooType'})
        addToCleanUp(deallocType)

        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(objPtr))
        
        self.assertEquals(mapper.PyObject_Init(objPtr, typePtr), objPtr, 'did not return the "new instance"')
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type"), typePtr, "wrong type")
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PyObject, "ob_refcnt"), 1, "wrong refcount")
        self.assertEquals(mapper.HasPtr(objPtr), False)
        

    @WithMapper
    def testPyBaseObject_Init(self, mapper, _):
        "this function shouldn't do anything..."
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertEquals(mapper.PyBaseObject_Init(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero), 0)

    
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
