
import operator

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr, UInt32
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, PythonApi, PythonMapper
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
        self.assertEqual(mapper.Retrieve(resultPtr), 8, "didn't call")
        
        kwargsPtr = mapper.Store({'y': 4})
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, kwargsPtr)
        self.assertEqual(mapper.Retrieve(resultPtr), 16, "didn't call with kwargs")
    
    @WithMapper
    def testPyObject_Call_Error(self, mapper, _):
        def Blam(*_, **__):
            raise ValueError('arrgh!')
        kallablePtr = mapper.Store(Blam)
        
        self.assertEqual(mapper.PyObject_Call(kallablePtr, IntPtr.Zero, IntPtr.Zero), IntPtr.Zero)
        self.assertMapperHasError(mapper, ValueError)


    @WithMapper
    def testPyObject_Call_noargs(self, mapper, _):
        kallablePtr = mapper.Store(lambda: 2)
        resultPtr = mapper.PyObject_Call(kallablePtr, IntPtr.Zero, IntPtr.Zero)
        self.assertEqual(mapper.Retrieve(resultPtr), 2, "didn't call")


    @WithMapper
    def testPyCallable_Check(self, mapper, _):
        callables = map(mapper.Store, [float, len, lambda: None])
        notCallables = map(mapper.Store, ["hullo", 33, ])
        
        for x in callables:
            self.assertEqual(mapper.PyCallable_Check(x), 1, "reported not callable")
        for x in notCallables:
            self.assertEqual(mapper.PyCallable_Check(x), 0, "reported callable")


    def assertRichCmp(self, mapper, opid, ob1, ob2):
        op = COMPARISONS[opid]
        expectint = -1
        error = None
        try:
            expectint = op(ob1, ob2)
        except Exception as e:
            error = e.__class__

        resultint = mapper.PyObject_RichCompareBool(mapper.Store(ob1), mapper.Store(ob2), int(opid))
        self.assertEqual(resultint, expectint, "%r: %r %r" % (op.__name__, ob1, ob2))
        self.assertMapperHasError(mapper, error)

        resultptr = mapper.PyObject_RichCompare(mapper.Store(ob1), mapper.Store(ob2), int(opid))
        self.assertMapperHasError(mapper, error)
        if error:
            self.assertEqual(resultptr, IntPtr.Zero)
        else:
            self.assertEqual(mapper.Retrieve(resultptr), expectint, "%r: %r %r" % (op.__name__, ob1, ob2))

    @WithMapper
    def testPyObject_RichCompare(self, mapper, _):
        class BadComparer(object):
            def borked(self, other):
                raise Exception("no!")
            __lt__ = __le__ = __eq__ = __ne__ = __gt__ = __ge__ = borked
        objects = (1, 1, 1.0, -1, 3.4e5, object, object(), 'hello', [1], (2,), {3: 'four'}, BadComparer, BadComparer())
        
        for opid in COMPARISONS:
            for ob1 in objects:
                for ob2 in objects:
                    self.assertRichCmp(mapper, opid, ob1, ob2)


    @WithMapper
    def testPyObject_RichCompare_StrangeReturnValue(self, mapper, _):
        class StrangeComparer(object):
            def returnSomethingFalse(self, _):
                return []
            def returnSomethingTrue(self, _):
                return [False]
            __lt__ = __le__ = __eq__ = returnSomethingFalse
            __ne__ = __gt__ = __ge__ = returnSomethingTrue
        
        obj = StrangeComparer()
        objPtr = mapper.Store(obj)
        for opid in COMPARISONS:
            expectobj = COMPARISONS[opid](obj, obj)
            expectint = int(bool(expectobj))
            self.assertEqual(mapper.PyObject_RichCompareBool(objPtr, objPtr, int(opid)), expectint)
            self.assertEqual(mapper.Retrieve(mapper.PyObject_RichCompare(objPtr, objPtr, int(opid))), expectobj)
        
 

    @WithMapper
    def testPyObject_GetAttrString(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "bob")
        self.assertEqual(mapper.Retrieve(resultPtr), "Poe", "wrong")


    @WithMapper
    def testPyObject_GetAttrStringFailure(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "ben")
        self.assertEqual(resultPtr, IntPtr.Zero, "wrong")
        self.assertEqual(mapper.LastException, None, "no need to set exception, according to spec")


    @WithMapper
    def testPyObject_GetAttr(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("bob"))
        self.assertEqual(mapper.Retrieve(resultPtr), "Poe", "wrong")


    @WithMapper
    def testPyObject_GetAttrStringFailure(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("ben"))
        self.assertEqual(resultPtr, IntPtr.Zero, "wrong")
        self.assertEqual(mapper.LastException, None, "no need to set exception, assuming this matches GetAttrString")


    @WithMapper
    def testPyObject_SetAttrString(self, mapper, _):
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEqual(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), 0)
        self.assertEqual(obj.bob, 123)


    @WithMapper
    def testPyObject_SetAttrString_Failure(self, mapper, _):
        objPtr = mapper.Store(object())
        self.assertEqual(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), -1)
        self.assertMapperHasError(mapper, AttributeError)


    @WithMapper
    def testPyObject_SetAttr(self, mapper, _):
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEqual(mapper.PyObject_SetAttr(objPtr, mapper.Store("bob"), mapper.Store(123)), 0)
        self.assertEqual(obj.bob, 123)


    @WithMapper
    def testPyObject_SetAttr_Failure(self, mapper, _):
        self.assertEqual(mapper.PyObject_SetAttr(mapper.Store(object()), mapper.Store("bob"), mapper.Store(123)), -1)
        self.assertMapperHasError(mapper, AttributeError)


    @WithMapper
    def testPyObject_HasAttr_HasAttrString(self, mapper, _):
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        self.assertEqual(mapper.PyObject_HasAttrString(objPtr, "bob"), 1)
        self.assertEqual(mapper.PyObject_HasAttr(objPtr, mapper.Store("bob")), 1)
        self.assertEqual(mapper.PyObject_HasAttrString(objPtr, "jim"), 0)
        self.assertEqual(mapper.PyObject_HasAttr(objPtr, mapper.Store("jim")), 0)


    @WithMapper
    def testPyObject_GetItem(self, mapper, _):
        result = object()
        class Subscriptable(object):
            def __getitem__(self, key):
                return result
        
        objPtr = mapper.Store(Subscriptable())
        keyPtr = mapper.Store(object())
        resultPtr = mapper.Store(result)
        
        self.assertEqual(mapper.PyObject_GetItem(objPtr, keyPtr), resultPtr)
        self.assertEqual(mapper.RefCount(resultPtr), 2, "failed to incref return value")


    @WithMapper
    def testPyObject_GetItem_Failure(self, mapper, _):
        obj = object()
        objPtr = mapper.Store(obj)
        
        self.assertEqual(mapper.PyObject_GetItem(objPtr, mapper.Store(1)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyObject_SetItem(self, mapper, _):
        result = object()
        sets = {}
        class Subscriptable(object):
            def __setitem__(self, key, value):
                sets[key] = value
        
        objPtr = mapper.Store(Subscriptable())
        key, value = object(), object()
        keyPtr = mapper.Store(key)
        valuePtr = mapper.Store(value)
        
        self.assertEqual(mapper.PyObject_SetItem(objPtr, keyPtr, valuePtr), 0)
        self.assertEqual(sets, {key: value})


    @WithMapper
    def testPyObject_SetItem_Failure(self, mapper, _):
        obj = object()
        objPtr = mapper.Store(obj)
        
        self.assertEqual(mapper.PyObject_SetItem(objPtr, mapper.Store(1), mapper.Store(2)), -1)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyObject_DelItemString(self, mapper, _):
        result = object()
        contents = {'foo': 1}
        class Subscriptable(object):
            def __delitem__(self, key):
                del contents[key]
        
        objPtr = mapper.Store(Subscriptable())
        self.assertEqual(mapper.PyObject_DelItemString(objPtr, "foo"), 0)
        self.assertMapperHasError(mapper, None)
        self.assertEqual(contents, {})
        
        self.assertEqual(mapper.PyObject_DelItemString(objPtr, "foo"), -1)
        self.assertMapperHasError(mapper, KeyError)
        

    @WithMapper
    def testPyObject_Hash(self, mapper, _):
        self.assertEqual(mapper.PyObject_Hash(mapper.Store("fooble")), hash("fooble"))
        self.assertMapperHasError(mapper, None)
        
        self.assertEqual(mapper.PyObject_Hash(mapper.Store({})), -1)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyObject_IsTrue(self, mapper, _):
        for trueval in ("hullo", 33, -1.5, True, [0], (0,), {1:2}, object()):
            ptr = mapper.Store(trueval)
            self.assertEqual(mapper.PyObject_IsTrue(ptr), 1)
            self.assertEqual(mapper.LastException, None)
            mapper.DecRef(ptr)
        
        for falseval in ('', 0, 0.0, False, [], tuple(), {}):
            ptr = mapper.Store(falseval)
            self.assertEqual(mapper.PyObject_IsTrue(ptr), 0)
            self.assertEqual(mapper.LastException, None)
            mapper.DecRef(ptr)
            
        class MyError(Exception):
            pass
        class ErrorBool(object):
            def __len__(self):
                raise MyError()
                
        ptr = mapper.Store(ErrorBool())
        self.assertEqual(mapper.PyObject_IsTrue(ptr), -1)
        self.assertMapperHasError(mapper, MyError)
        mapper.DecRef(ptr)


    @WithMapper
    def testPyObject_Size(self, mapper, _):
        for okval in ("hullo", [0, 3, 5], (0,), {1:2}, set([1, 2])):
            ptr = mapper.Store(okval)
            self.assertEqual(mapper.PyObject_Size(ptr), len(okval))
            self.assertEqual(mapper.LastException, None)
            mapper.DecRef(ptr)
        
        for badval in (0, 0.0, False, object, object()):
            ptr = mapper.Store(badval)
            mapper.LastException = None
            self.assertEqual(mapper.PyObject_Size(ptr), -1)
            self.assertMapperHasError(mapper, TypeError)
            mapper.DecRef(ptr)


    @WithMapper
    def testPyObject_StrRepr(self, mapper, _):
        for okval in ("hullo", [0, 3, 5], (0,), {1:2}, set([1, 2])):
            ptr = mapper.Store(okval)
            strptr = mapper.PyObject_Str(ptr)
            self.assertEqual(mapper.Retrieve(strptr), str(okval))
            self.assertEqual(mapper.LastException, None)
            reprptr = mapper.PyObject_Repr(ptr)
            self.assertEqual(mapper.Retrieve(reprptr), repr(okval))
            self.assertEqual(mapper.LastException, None)
            mapper.DecRef(ptr)
            mapper.DecRef(strptr)
            mapper.DecRef(reprptr)
        
        class BadStr(object):
            def __str__(self):
                raise TypeError('this object cannot be represented in your puny alphabet')
            def __repr__(self):
                raise TypeError('this object cannot be represented in your puny alphabet')
        
        badptr = mapper.Store(BadStr())
        self.assertEqual(mapper.PyObject_Str(badptr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        self.assertEqual(mapper.PyObject_Repr(badptr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        mapper.DecRef(badptr)


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
            except Exception as e:
                expectException = type(e)
            
            instPtr = mapper.Store(inst)
            clsPtr = mapper.Store(cls)
            self.assertEqual(mapper.PyObject_IsInstance(instPtr, clsPtr), expectResult)
            self.assertMapperHasError(mapper, expectException)
            mapper.DecRef(instPtr)
            mapper.DecRef(clsPtr)


    @WithMapper
    def testPyObject_IsSubclass(self, mapper, _):
        class C(object): pass
        class D(C): pass
        class E: pass
        class F(E): pass
        
        data = (
            (C, C),
            (C, D),
            (D, C),
            (D, D),
            (E, E),
            (E, F),
            (F, E),
            (F, F),
            (object, object),
            (int, object),
            (object, str),
            (TypeError, TypeError),
            (TypeError, Exception),
            (Exception, TypeError),
            (1, 2),
        )
        for (sub, cls) in data:
            expectResult = -1
            expectException = None
            try:
                expectResult = int(issubclass(sub, cls))
            except Exception as e:
                expectException = type(e)
            
            subPtr = mapper.Store(sub)
            clsPtr = mapper.Store(cls)
            self.assertEqual(mapper.PyObject_IsSubclass(subPtr, clsPtr), expectResult)
            self.assertMapperHasError(mapper, expectException)
            mapper.DecRef(subPtr)
            mapper.DecRef(clsPtr)
        

    
class PyBaseObject_Type_Test(TypeTestCase):

    @WithMapper
    def testPyBaseObject_Type_fields(self, mapper, _):
        def AssertPtrField(name, value):
            field = CPyMarshal.ReadPtrField(mapper.PyBaseObject_Type, PyTypeObject, name)
            self.assertNotEqual(field, IntPtr.Zero)
            self.assertEqual(field, value)
        
        AssertPtrField("tp_new", mapper.GetFuncPtr("PyType_GenericNew"))
        AssertPtrField("tp_alloc", mapper.GetFuncPtr("PyType_GenericAlloc"))
        AssertPtrField("tp_init", mapper.GetFuncPtr("IC_PyBaseObject_Init"))
        AssertPtrField("tp_dealloc", mapper.GetFuncPtr("IC_PyBaseObject_Dealloc"))
        AssertPtrField("tp_free", mapper.GetFuncPtr("PyObject_Free"))
        
        AssertPtrField("tp_str", mapper.GetFuncPtr("PyObject_Str"))


    def testPyBaseObject_Type_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyBaseObject_Type")


    def testPyBaseObject_Type_tp_free(self):
        self.assertUsual_tp_free("PyBaseObject_Type")
            
    
    @WithMapper
    def testPyBaseObject_TypeDeallocCallsObjTypesFreeFunction(self, mapper, addToCleanUp):
        calls = []
        def Some_FreeFunc(objPtr):
            calls.append(objPtr)
        self.freeDgt = dgt_void_ptr(Some_FreeFunc)
        
        baseObjTypeBlock = mapper.PyBaseObject_Type
        objTypeBlock = mapper.PyDict_Type # type not actually important
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject()))
        addToCleanUp(lambda: Marshal.FreeHGlobal(objPtr))

        CPyMarshal.WriteFunctionPtrField(objTypeBlock, PyTypeObject, "tp_free", self.freeDgt)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", objTypeBlock)
        gcwait() # this should make the function pointers invalid if we forgot to store references to the delegates

        mapper.IC_PyBaseObject_Dealloc(objPtr)
        self.assertEqual(calls, [objPtr], "wrong calls")


class NewInitFunctionsTest(TestCase):
    
    @WithMapper
    def testPyObject_Init(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'FooType'})
        addToCleanUp(deallocType)

        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject()))
        addToCleanUp(lambda: Marshal.FreeHGlobal(objPtr))
        
        self.assertEqual(mapper.PyObject_Init(objPtr, typePtr), objPtr, 'did not return the "new instance"')
        self.assertEqual(CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type"), typePtr, "wrong type")
        self.assertEqual(CPyMarshal.ReadIntField(objPtr, PyObject, "ob_refcnt"), 1, "wrong refcount")
        self.assertEqual(mapper.HasPtr(objPtr), False)
        

    @WithMapper
    def testIC_PyBaseObject_Init(self, mapper, _):
        "this function shouldn't do anything..."
        with PythonMapper() as mapper:
            deallocTypes = CreateTypes(mapper)
            
            self.assertEqual(mapper.IC_PyBaseObject_Init(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero), 0)
            
        deallocTypes()

    
    def test_PyObject_New(self):
        allocs = []
        allocator = GetAllocatingTestAllocator(allocs, [])
        with PythonMapper(allocator) as mapper:
            deallocTypes = CreateTypes(mapper)
            
            typeObjSize = Marshal.SizeOf(PyTypeObject())
            typePtr = Marshal.AllocHGlobal(typeObjSize)
            CPyMarshal.Zero(typePtr, typeObjSize)
            CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_basicsize", 31337)
            
            del allocs[:]
            objPtr = mapper._PyObject_New(typePtr)
            self.assertEqual(allocs, [(objPtr, 31337)])
            self.assertEqual(CPyMarshal.ReadPtrField(objPtr, PyObject, 'ob_type'), typePtr)
            self.assertEqual(CPyMarshal.ReadPtrField(objPtr, PyObject, 'ob_refcnt'), 1)
            self.assertEqual(mapper.HasPtr(objPtr), False)
        
        deallocTypes()

    
    def test_PyObject_NewVar(self):
        allocs = []
        allocator = GetAllocatingTestAllocator(allocs, [])
        with PythonMapper(allocator) as mapper:
            deallocTypes = CreateTypes(mapper)
            
            typeObjSize = Marshal.SizeOf(PyTypeObject())
            typePtr = Marshal.AllocHGlobal(typeObjSize)
            CPyMarshal.Zero(typePtr, typeObjSize)
            CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_basicsize", 31337)
            CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_itemsize", 1337)
            
            del allocs[:]
            objPtr = mapper._PyObject_NewVar(typePtr, IntPtr(123))
            self.assertEqual(allocs, [(objPtr, 31337 + (1337 * 123))])
            self.assertEqual(CPyMarshal.ReadPtrField(objPtr, PyObject, 'ob_type'), typePtr)
            self.assertEqual(CPyMarshal.ReadPtrField(objPtr, PyObject, 'ob_refcnt'), 1)
            self.assertEqual(mapper.HasPtr(objPtr), False)
            
        deallocTypes()
        

suite = makesuite(
    ObjectFunctionsTest,
    PyBaseObject_Type_Test,
    NewInitFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
