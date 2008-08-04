
from tests.utils.runtest import makesuite, run
    
from tests.utils.cpython import MakeGetSetDef, MakeMethodDef, MakeNumSeqMapMethods, MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase

import System
from System import IntPtr, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    CPyMarshal, CPython_destructor_Delegate, CPython_initproc_Delegate, HGlobalAllocator,
    Python25Api, Python25Mapper
)
from Ironclad.Structs import MemberT, METH, Py_TPFLAGS, PyMemberDef, PyNumberMethods, PyObject, PySequenceMethods, PyTypeObject


class BorkedException(System.Exception):
    pass


ARG1_PTR = IntPtr(111)
ARG2_PTR = IntPtr(222)
ARG3_PTR = IntPtr(333)
ARG1_SSIZE = 111111
RESULT_PTR = IntPtr(999)


class DispatchSetupTestCase(TestCase):

    def assertTypeSpec(self, typeSpec, TestType):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        _type = mapper.Retrieve(typePtr)
        TestType(_type, mapper)
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    def getUnaryFunc(self, result):
        calls = []
        def Unary(arg1):
            calls.append((arg1,))
            return result
        return Unary, calls
    
    def getBinaryFunc(self, result):
        calls = []
        def Binary(arg1, arg2):
            calls.append((arg1, arg2))
            return result
        return Binary, calls
    
    def getTernaryFunc(self, result):
        calls = []
        def Ternary(arg1, arg2, arg3):
            calls.append((arg1, arg2, arg3))
            return result
        return Ternary, calls

    def getQuarternaryFunc(self, result):
        calls = []
        def Quarternary(arg1, arg2, arg3, arg4):
            calls.append((arg1, arg2, arg3, arg4))
            return result
        return Quarternary, calls
        
    def getNaryFunc(self, result):
        calls = []
        def Nary(*args, **kwargs):
            calls.append((args, kwargs))
            return result
        return Nary, calls
        

    def getUnaryCFunc(self):
        return self.getUnaryFunc(RESULT_PTR)

    def getBinaryCFunc(self):
        return self.getBinaryFunc(RESULT_PTR)

    def getTernaryCFunc(self):
        return self.getTernaryFunc(RESULT_PTR)

    def getSsizeargCFunc(self):
        return self.getBinaryFunc(RESULT_PTR)

    def assertCalls(self, dgt, args, calls, expect_args, result):
        args, kwargs = args
        self.assertEquals(calls, [])
        self.assertEquals(dgt(*args, **kwargs), result)
        self.assertEquals(calls, [expect_args])
    
    def assertCallsUnaryCFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR,), {}), calls, (ARG1_PTR,), RESULT_PTR)
    
    def assertCallsBinaryCFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG2_PTR), {}), calls, (ARG1_PTR, ARG2_PTR), RESULT_PTR)
    
    def assertCallsTernaryCFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG2_PTR, ARG3_PTR), {}), calls, (ARG1_PTR, ARG2_PTR, ARG3_PTR), RESULT_PTR)
    
    def assertCallsSsizeargCFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG1_SSIZE), {}), calls, (ARG1_PTR, ARG1_SSIZE), RESULT_PTR)

class MethodsTest(DispatchSetupTestCase):

    def assertAddTypeObject_withSingleMethod(self, methodDef, TestType):
        typeSpec = {
            "tp_name": "klass",
            "tp_methods": [methodDef]
        }
        self.assertTypeSpec(typeSpec, TestType)

    def testNoArgsMethod(self):
        NoArgs, calls_cfunc = self.getBinaryCFunc()
        method, deallocMethod = MakeMethodDef("method", NoArgs, METH.NOARGS)
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_noargs = dispatch
            self.assertCalls(
                instance.method, (tuple(), {}), calls_dispatch, 
                ("klass.method", instance._instancePtr), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsBinaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


    def testObjArgMethod(self):
        ObjArg, calls_cfunc = self.getBinaryCFunc()
        method, deallocMethod = MakeMethodDef("method", ObjArg, METH.O)
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), object()
            _type._dispatcher.method_objarg = dispatch
            self.assertCalls(
                instance.method, ((arg,), {}), calls_dispatch, 
                ("klass.method", instance._instancePtr, arg), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsBinaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


    def testVarargsMethod(self):
        VarArgs, calls_cfunc = self.getBinaryCFunc()
        method, deallocMethod = MakeMethodDef("method", VarArgs, METH.VARARGS)
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, args = _type(), ("for", "the", "horde")
            _type._dispatcher.method_varargs = dispatch
            self.assertCalls(
                instance.method, (args, {}), calls_dispatch, 
                (("klass.method", instance._instancePtr) + args, {}), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsBinaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()
        

    def testVarargsKwargsMethod(self):
        Kwargs, calls_cfunc = self.getTernaryCFunc()
        method, deallocMethod = MakeMethodDef("method", Kwargs, METH.VARARGS | METH.KEYWORDS)
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, args, kwargs = _type(), ("for", "the", "horde"), {"g1": "LM", "g2": "BS", "g3": "GM"}
            _type._dispatcher.method_kwargs = dispatch
            self.assertCalls(
                instance.method, (args, kwargs), calls_dispatch,
                (("klass.method", instance._instancePtr) + args, kwargs), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsTernaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


class CallTest(DispatchSetupTestCase):
    
    def testCall(self):
        Call, calls_cfunc = self.getTernaryCFunc()
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, args, kwargs = _type(), ("for", "the", "horde"), {"g1": "LM", "g2": "BS", "g3": "GM"}
            _type._dispatcher.method_kwargs = dispatch
            self.assertCalls(
                instance, (args, kwargs), calls_dispatch,
                (("klass.__call__", instance._instancePtr) + args, kwargs), result)
            
            cfunc = _type._dispatcher.table["klass.__call__"]
            self.assertCallsTernaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()

        typeSpec = {
            "tp_name": "klass",
            "tp_call": Call,
        }
        self.assertTypeSpec(typeSpec, TestType)

class IterTest(DispatchSetupTestCase):

    def assertSelfTypeMethod(self, typeFlags, keyName, expectedMethodName, TestErrorHandler):
        func, calls_cfunc = self.getUnaryCFunc()
        typeSpec = {
            "tp_name": "klass",
            keyName: func,
            "tp_flags": typeFlags
        }
        
        def TestType(_type, mapper):
            result = object()
            calls_dispatch = []
            def dispatch(methodName, selfPtr, errorHandler=None):
                calls_dispatch.append((methodName, selfPtr))
                TestErrorHandler(errorHandler, mapper)
                return result
                
            instance = _type()
            _type._dispatcher.method_selfarg = dispatch
            self.assertEquals(getattr(instance, expectedMethodName)(), result, "bad return")
            self.assertEquals(calls_dispatch, [("klass." + keyName, instance._instancePtr)])
            
            cfunc = _type._dispatcher.table["klass." + keyName]
            self.assertCallsUnaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertTypeSpec(typeSpec, TestType)


    def test_tp_iter_MethodDispatch(self):
        def TestErrorHandler(errorHandler, _): 
            self.assertEquals(errorHandler, None, "no special error handling required")

        self.assertSelfTypeMethod(
            Py_TPFLAGS.HAVE_ITER, "tp_iter", "__iter__", TestErrorHandler)


    def test_tp_iternext_MethodDispatch(self):
        def TestErrorHandler(errorHandler, mapper): 
            errorHandler(IntPtr(12345))
            self.assertRaises(StopIteration, errorHandler, IntPtr.Zero)
            mapper.LastException = ValueError()
            errorHandler(IntPtr.Zero)
        
        self.assertSelfTypeMethod(
            Py_TPFLAGS.HAVE_ITER, "tp_iternext", "next", TestErrorHandler)
        

class NumberTest(DispatchSetupTestCase):
    
    def assertUnaryNumberMethod(self, slotName, methodName):
        func, calls_cfunc = self.getUnaryCFunc()
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {slotName: func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_selfarg = dispatch
            self.assertCalls(
                getattr(instance, methodName), (tuple(), {}), calls_dispatch, 
                ("klass." + methodName, instance._instancePtr), result)
            
            cfunc = _type._dispatcher.table["klass." + methodName]
            self.assertCallsUnaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()
    
    def assertBinaryNumberMethod(self, slotName, methodName):
        func, calls_cfunc = self.getBinaryCFunc()
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {slotName: func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), object()
            _type._dispatcher.method_objarg = dispatch
            self.assertCalls(
                getattr(instance, methodName), ((arg,), {}), calls_dispatch, 
                ("klass." + methodName, instance._instancePtr, arg), result)
            
            cfunc = _type._dispatcher.table["klass." + methodName]
            self.assertCallsBinaryCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()

    def testAbs(self):
        self.assertUnaryNumberMethod("nb_absolute", "__abs__")

    def testAdd(self):
        self.assertBinaryNumberMethod("nb_add", "__add__")

    def testSubtract(self):
        self.assertBinaryNumberMethod("nb_subtract", "__sub__")

    def testMultiply(self):
        self.assertBinaryNumberMethod("nb_multiply", "__mul__")

    def testDivide(self):
        self.assertBinaryNumberMethod("nb_divide", "__div__")


class SequenceTest(DispatchSetupTestCase):
    
    def testItem(self):
        func, calls_cfunc = self.getSsizeargCFunc()
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(PySequenceMethods, {"sq_item": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_sequence": sequencesPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), 123
            _type._dispatcher.method_ssizearg = dispatch
            self.assertCalls(
                getattr(instance, "__getitem__"), ((arg,), {}), calls_dispatch, 
                ("klass.__getitem__", instance._instancePtr, arg), result)
            
            cfunc = _type._dispatcher.table["klass.__getitem__"]
            self.assertCallsSsizeargCFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
        


class NewInitDelTest(TestCase):

    def testMethodTablePopulation(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        calls = []
        def test_tp_new(_, __, ___):
            calls.append("tp_new")
            return IntPtr(123)
        def test_tp_init(_, __, ___):
            calls.append("tp_init")
            return 0
        def test_tp_dealloc(_):
            calls.append("tp_dealloc")
            
        typeSpec = {
            "tp_name": "klass",
            "tp_new": test_tp_new,
            "tp_init": test_tp_init,
            "tp_dealloc": test_tp_dealloc,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        table = _type._dispatcher.table
        table['klass.tp_new'](IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
        table['klass.tp_init'](IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(calls, ['tp_new', 'tp_init'], "not hooked up somewhere")
        
        self.assertFalse(table.has_key('klass.tp_dealloc'), 
            "tp_dealloc should be called indirectly, by the final decref of an instance")
        
        mapper.Dispose()
        deallocType()
        deallocTypes()


    def testDispatch(self):
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        def tp_dealloc(instancePtr_dealloc):
            calls.append("tp_dealloc")
            self.assertEquals(instancePtr_dealloc, instancePtr, "wrong instance")
            # finish the dealloc to avoid confusing mapper on shutdown
            mapper.PyObject_Free(instancePtr_dealloc)
            
        # creation methods should be patched out
        def Raise(msg):
            raise Exception(msg)
        typeSpec = {
            "tp_name": "klass",
            "tp_new": lambda _, __, ___: Raise("new unpatched"),
            "tp_init": lambda _, __, ___: Raise("init unpatched"),
            "tp_dealloc": tp_dealloc,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        ARGS = (1, "two")
        KWARGS = {"three": 4}
        instancePtr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(instancePtr, PyObject, 'ob_refcnt', 1)
        CPyMarshal.WritePtrField(instancePtr, PyObject, 'ob_type', typePtr)
        
        calls = []
        def tp_new_test(typePtr_new, argsPtr, kwargsPtr):
            calls.append("tp_new")
            self.assertEquals(typePtr_new, typePtr)
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS)
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS)
            return instancePtr
        
        def tp_init_test(instancePtr_init, argsPtr, kwargsPtr):
            calls.append("tp_init")
            self.assertEquals(instancePtr_init, instancePtr)
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS)
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS)
            return 0
            
        _type._dispatcher.table['klass.tp_new'] = Python25Api.PyType_GenericNew_Delegate(tp_new_test)
        _type._dispatcher.table['klass.tp_init'] = CPython_initproc_Delegate(tp_init_test)
        
        instance = _type(*ARGS, **KWARGS)
        self.assertEquals(instance._instancePtr, instancePtr)
        self.assertEquals(calls, ['tp_new', 'tp_init'])
        
        mapper.CheckBridgePtrs()
        del instance
        gcwait()
        self.assertEquals(calls, ['tp_new', 'tp_init', 'tp_dealloc'])
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    def testLifetime(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)

        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        _type = mapper.Retrieve(typePtr)
        
        obj = _type()
        objref = WeakReference(obj, True)
        objptr = obj._instancePtr
        
        # for unmanaged code to mess with ob_refcnt, it must have been passed a reference
        # from managed code; this shouldn't happen without a Store (which will IncRef)
        self.assertEquals(mapper.Store(obj), objptr)
        self.assertEquals(mapper.RefCount(objptr), 2)
        
        # unmanaged code grabs a reference to obj
        CPyMarshal.WriteIntField(objptr, PyObject, 'ob_refcnt', 3)
        
        # control passes back to managed code; this should DecRef
        mapper.DecRef(objptr)
        self.assertEquals(mapper.RefCount(objptr), 2)
        
        # managed code forgets obj for a bit
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "object died before its time")
        self.assertEquals(mapper.Retrieve(objptr), objref.Target, "mapping broken")
        
        # unmanaged code forgets about obj too
        CPyMarshal.WriteIntField(objptr, PyObject, 'ob_refcnt', 1)
        
        # however, nothing happens to cause us to reexamine bridge ptrs
        gcwait()
        self.assertEquals(objref.IsAlive, True, "object died unexpectedly")
        self.assertEquals(mapper.Retrieve(objptr), objref.Target, "mapping broken")
        
        # now, another (imaginary) bridge object gets destroyed, causing us to reexamine
        mapper.CheckBridgePtrs()
        
        # and, after the next 2* GCs, objref disappears
        # * 1 to notice it's collectable, 1 to actually collect it
        gcwait()
        gcwait()
        self.assertEquals(objref.IsAlive, False, "object didn't die")
        
        mapper.Dispose()
        deallocType()
        deallocTypes()


class PropertiesTest(TestCase):
    
    def assertGetSet(self, attr, get, set, TestType, closure=IntPtr.Zero):
        doc = "take me to the airport, put me on a plane"
        getset, deallocGetset = MakeGetSetDef(attr, get, set, doc, closure)
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        typeSpec = {
            "tp_name": 'klass',
            "tp_getset": [getset],
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        self.assertEquals(getattr(_type, attr).__doc__, doc, "bad docstring")
        TestType(_type)
        
        deallocGetset()
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    def testGet(self):
        def get(_, __):
            self.fail("this should have been patched out in TestType")
        
        def TestType(_type):
            instance = _type()
            
            calls = []
            result = "see my loafers: former gophers"
            def Getter(name, instancePtr, closurePtr):
                calls.append(('Getter', (name, instancePtr, closurePtr)))
                return result
            _type._dispatcher.method_getter = Getter
            
            self.assertEquals(instance.boing, result, "bad result")
            self.assertEquals(calls, [('Getter', ('klass.__get_boing', instance._instancePtr, IntPtr.Zero))])
            
            try:
                # not using assertRaises because we can't del instance if it's referenced in nested scope
                instance.boing = 'splat'
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when setting get-only property")
            del instance
            gcwait()
        
        self.assertGetSet("boing", get, None, TestType)


    def testSet(self):
        def set(_, __, ___):
            self.fail("this should have been patched out in TestType")
        
        def TestType(_type):
            instance = _type()
            
            calls = []
            def Setter(name, instancePtr, value, closurePtr):
                calls.append(('Setter', (name, instancePtr, value, closurePtr)))
            _type._dispatcher.method_setter = Setter
            
            try:
                # not using assertRaises because we can't del instance if it's referenced in nested scope
                instance.splat
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when getting set-only property")
                
            value = "see my vest, see my vest, made from real gorilla chest"
            instance.splat = value
            self.assertEquals(calls, [('Setter', ('klass.__set_splat', instance._instancePtr, value, IntPtr.Zero))])
            del instance
            gcwait()
            
        self.assertGetSet("splat", None, set, TestType)
        

    def testClosure(self):
        def get(_, __):
            self.fail("this should have been patched out in TestType")
        def set(_, __, ___):
            self.fail("this should have been patched out in TestType")
        
        CLOSURE_PTR = IntPtr(12345)
        def TestType(_type):
            instance = _type()
            
            calls = []
            result = "They called me a PC thug!"
            def Getter(name, instancePtr, closurePtr):
                calls.append(('Getter', (name, instancePtr, closurePtr)))
                return result
            _type._dispatcher.method_getter = Getter
            
            def Setter(name, instancePtr, value, closurePtr):
                calls.append(('Setter', (name, instancePtr, value, closurePtr)))
            _type._dispatcher.method_setter = Setter
            
            self.assertEquals(instance.click, result, "wrong result")
            value = "I've been called a greasy thug too, and it never stops hurting."
            instance.click = value
            self.assertEquals(calls, 
                [('Getter', ('klass.__get_click', instance._instancePtr, CLOSURE_PTR)),
                 ('Setter', ('klass.__set_click', instance._instancePtr, value, CLOSURE_PTR))],
                "wrong calls")
                
            del instance
            gcwait()
            
        self.assertGetSet("click", get, set, TestType, CLOSURE_PTR)


class MembersTest(TestCase):
    
    def assertMember(self, mapper, attr, memberType, offset, flags, TestType, basicsize=32):
        doc = "hurry hurry hurry, before I go insane"
        typeSpec = {
            "tp_name": 'klass',
            "tp_members": [PyMemberDef(attr, memberType, offset, flags, doc)],
            "tp_basicsize": basicsize
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        self.assertEquals(getattr(_type, attr).__doc__, doc, "wrong docstring")
        TestType(_type)
        return deallocType
    
        
    def testReadOnlyMember(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        offset = 16
        def TestType(_type):
            instance = _type()
            fieldPtr = CPyMarshal.Offset(instance._instancePtr, offset)
            
            try:
                instance.boing = 54231
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when setting get-only property")
            
            calls = []
            def Get(address):
                calls.append(('Get', (address,)))
                return 12345
            _type._dispatcher.get_member_int = Get
            
            self.assertEquals(instance.boing, 12345)
            self.assertEquals(calls, [
                ('Get', (fieldPtr,)),
            ])
            del instance
            gcwait()
            
        deallocType = self.assertMember(mapper, 'boing', MemberT.INT, offset, 1, TestType)
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    def getGetSetTypeTest(self, attr, suffix, offset, value, result):
        def TestType(_type):
            instance = _type()
            fieldPtr = CPyMarshal.Offset(instance._instancePtr, offset)
            
            calls = []
            def Get(address):
                calls.append(('Get', (address,)))
                return result
            def Set(address, value):
                calls.append(('Set', (address, value)))
            setattr(_type._dispatcher, 'get_member_' + suffix, Get)
            setattr(_type._dispatcher, 'set_member_' + suffix, Set)
                
            self.assertEquals(getattr(instance, attr), result)
            setattr(instance, attr, value)
            
            self.assertEquals(calls, [
                ('Get', (fieldPtr,)),
                ('Set', (fieldPtr, value)),
            ])
            del instance
            gcwait()
        return TestType
    
    
    def assertTypeMember(self, name, value, result):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        attr = 'boing'
        offset = 16
        TestType = self.getGetSetTypeTest(attr, name, offset, value, result)
        deallocType = self.assertMember(mapper, attr, getattr(MemberT, name.upper()), offset, 0, TestType)
    
        mapper.Dispose()
        deallocType()
        deallocTypes()
        
        
    def testReadWriteIntMember(self):
        self.assertTypeMember('int', 12345, 54321)
        
    def testReadWriteCharMember(self):
        self.assertTypeMember('char', 'x', 'y')
        
    def testReadWriteUbyteMember(self):
        self.assertTypeMember('ubyte', 0, 255)
        
    def testReadWriteObjectMember(self):
        self.assertTypeMember('object', object(), object())


class InheritanceTest(TestCase):
    
    def testBaseClass(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr})
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(issubclass(klass, mapper.Retrieve(basePtr)), True, "didn't notice klass's base class")
        self.assertEquals(mapper.RefCount(mapper.PyType_Type), 3, "types did not keep references to TypeType")
        self.assertEquals(mapper.RefCount(basePtr), 3, "subtype did not keep reference to base")
        self.assertEquals(mapper.RefCount(mapper.PyBaseObject_Type), 2, "base type did not keep reference to its base (even if it wasn't set explicitly)")
        self.assertEquals(CPyMarshal.ReadPtrField(basePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type")
        
        mapper.Dispose()
        deallocType()
        deallocBase()
        deallocTypes()
    
    
    def testInheritsMethodTable(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr})

        klass = mapper.Retrieve(klassPtr)
        base = mapper.Retrieve(basePtr)
        for k, v in base._dispatcher.table.items():
            self.assertEquals(klass._dispatcher.table[k], v)

        mapper.Dispose()
        deallocType()
        deallocBase()
        deallocTypes()
    
    
    def testMultipleBases(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        base1Ptr, deallocBase1 = MakeTypePtr(mapper, {'tp_name': 'base1', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        base2Ptr, deallocBase2 = MakeTypePtr(mapper, {'tp_name': 'base2', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        bases = (mapper.Retrieve(base1Ptr,), mapper.Retrieve(base2Ptr))
        basesPtr = mapper.Store(bases)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': base1Ptr, 'tp_bases': basesPtr})
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(klass.__bases__, bases)
        self.assertEquals(mapper.RefCount(base1Ptr), 5, "subtype did not keep reference to bases")
        self.assertEquals(mapper.RefCount(base2Ptr), 4, "subtype did not keep reference to bases")
        self.assertEquals(CPyMarshal.ReadPtrField(base1Ptr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type 1")
        self.assertEquals(CPyMarshal.ReadPtrField(base2Ptr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type 2")

        mapper.Dispose()
        deallocType()
        deallocBase1()
        deallocBase2()
        deallocTypes()
    
    
    def testInheritMethodTableFromMultipleBases(self):
        "probably won't work quite right with identically-named base classes"
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        base1Ptr, deallocBase1 = MakeTypePtr(mapper, {'tp_name': 'base1', 'ob_type': mapper.PyType_Type})
        base2Ptr, deallocBase2 = MakeTypePtr(mapper, {'tp_name': 'base2', 'ob_type': mapper.PyType_Type})
        bases = (mapper.Retrieve(base1Ptr,), mapper.Retrieve(base2Ptr))
        basesPtr = mapper.Store(bases)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': base1Ptr, 'tp_bases': basesPtr})
        klass = mapper.Retrieve(klassPtr)

        for base in bases:
            for k, v in base._dispatcher.table.items():
                self.assertEquals(klass._dispatcher.table[k], v)

        mapper.Dispose()
        deallocType()
        deallocBase1()
        deallocBase2()
        deallocTypes()
        
    
    def testMultipleBasesIncludingBuiltin(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type})
        bases = (mapper.Retrieve(basePtr), int)
        basesPtr = mapper.Store(bases)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr, 'tp_bases': basesPtr})

        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(klass.__bases__, bases)

        mapper.Dispose()
        deallocType()
        deallocBase()
        deallocTypes()
        
    
    def testMetaclass(self):
        # this allocator is necessary because metaclass.tp_dealloc will use the mapper's allocator
        # to dealloc klass, and will complain if it wasn't allocated in the first place. this is 
        # probably not going to work in the long term
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        metaclassPtr, deallocMC = MakeTypePtr(mapper, {'tp_name': 'metaclass'})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': metaclassPtr}, allocator)
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(type(klass), mapper.Retrieve(metaclassPtr), "didn't notice klass's type")
        
        mapper.Dispose()
        deallocType()
        deallocMC()
        deallocTypes()
    
    
    def testInheritMethodTableFromMetaclass(self):
        "probably won't work quite right with identically-named metaclass"
        # this allocator is necessary because metaclass.tp_dealloc will use the mapper's allocator
        # to dealloc klass, and will complain if it wasn't allocated in the first place. this is 
        # probably not going to work in the long term
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        metaclassPtr, deallocMC = MakeTypePtr(mapper, {'tp_name': 'metaclass'})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': metaclassPtr}, allocator)

        klass = mapper.Retrieve(klassPtr)
        metaclass = mapper.Retrieve(metaclassPtr)
        for k, v in metaclass._dispatcher.table.items():
            self.assertEquals(klass._dispatcher.table[k], v)

        mapper.Dispose()
        deallocType()
        deallocMC()
        deallocTypes()


class TypeDictTest(TestCase):
    
    def testRetrieveAssignsDictTo_tp_dict(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": "klass"})
        
        _type = mapper.Retrieve(typePtr)
        _typeDictPtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict")
        self.assertEquals(mapper.Retrieve(_typeDictPtr), _type.__dict__)
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
        

suite = makesuite(
    MethodsTest,
    CallTest,
    IterTest,
    NumberTest,
    SequenceTest,
    NewInitDelTest,
    PropertiesTest,
    MembersTest,
    InheritanceTest,
    TypeDictTest,
)
if __name__ == '__main__':
    run(suite)
