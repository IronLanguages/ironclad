
from tests.utils.runtest import makesuite, run
    
from tests.utils.cpython import MakeGetSetDef, MakeMethodDef, MakeTypePtr
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
from Ironclad.Structs import MemberT, METH, Py_TPFLAGS, PyMemberDef, PyObject, PyTypeObject


class BorkedException(System.Exception):
    pass


INSTANCE_PTR = IntPtr(111)
ARGS_PTR = IntPtr(222)
KWARGS_PTR = IntPtr(333)
RESULT_PTR = IntPtr(999)


Null_CPythonVarargsFunction = lambda _, __: IntPtr.Zero
Null_CPythonVarargsKwargsFunction = lambda _, __, ___: IntPtr.Zero

def GetVarargsDispatchFunction(result, calls):
    def dispatch(name, instancePtr):
        calls.append((name, instancePtr))
        return result
    return dispatch

def GetKwargsDispatchFunction(result, calls):
    def dispatch(name, instancePtr):
        calls.append((name, instancePtr))
        return result
    return dispatch


class DispatchSetupTestCase(TestCase):

    def assertTypeSpec(self, typeSpec, TestType):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        _type = mapper.Retrieve(typePtr)
        TestType(_type)
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
        
    def assertVarargsDelegate(self, dgt, calls):
        self.assertEquals(calls, [])
        self.assertEquals(dgt(INSTANCE_PTR, ARGS_PTR), RESULT_PTR, "wrong function in table")
        self.assertEquals(calls, [(INSTANCE_PTR, ARGS_PTR)], "wrong function in table")

    def assertKwargsDelegate(self, dgt, calls):
        self.assertEquals(calls, [])
        self.assertEquals(dgt(INSTANCE_PTR, ARGS_PTR, KWARGS_PTR), RESULT_PTR, "wrong function in table")
        self.assertEquals(calls, [(INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)], "wrong function in table")
    


class DispatchTypeMethodsTest(DispatchSetupTestCase):

    def assertAddTypeObject_withSingleMethod(self, methodDef, TestType):
        typeSpec = {
            "tp_name": "klass",
            "tp_methods": [methodDef]
        }
        self.assertTypeSpec(typeSpec, TestType)

    def testNoArgsMethod(self):
        calls = []
        def NoArgs(selfPtr, argsPtr):
            calls.append((selfPtr, argsPtr))
            return RESULT_PTR
        method, deallocMethod = MakeMethodDef("method", NoArgs, METH.NOARGS)
        
        result = object()
        dispatchCalls = []
        def dispatch(name, instancePtr):
            dispatchCalls.append((name, instancePtr))
            return result
        
        def TestType(_type):
            instance = _type()
            _type._dispatcher.method_noargs = dispatch
            self.assertEquals(instance.method(), result, "didn't use correct _dispatcher method")
            self.assertEquals(dispatchCalls, [("klass.method", instance._instancePtr)], "called _dispatcher method wrong")
            self.assertVarargsDelegate(_type._dispatcher.table["klass.method"], calls)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


    def testObjArgMethod(self):
        calls = []
        def ObjArg(selfPtr, argsPtr):
            calls.append((selfPtr, argsPtr))
            return RESULT_PTR
        method, deallocMethod = MakeMethodDef("method", ObjArg, METH.O)
        
        result = object()
        dispatchCalls = []
        def dispatch(name, instancePtr, arg):
            dispatchCalls.append((name, instancePtr, arg))
            return result
        
        def TestType(_type):
            arg = object()
            instance = _type()
            _type._dispatcher.method_objarg = dispatch
            self.assertEquals(instance.method(arg), result, "didn't use correct _dispatcher method")
            self.assertEquals(dispatchCalls, [("klass.method", instance._instancePtr, arg)], "called _dispatcher method wrong")
            self.assertVarargsDelegate(_type._dispatcher.table["klass.method"], calls)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


    def testVarargsMethod(self):
        calls = []
        def VarArgs(selfPtr, argsPtr):
            calls.append((selfPtr, argsPtr))
            return RESULT_PTR
        method, deallocMethod = MakeMethodDef("method", VarArgs, METH.VARARGS)
        
        result = object()
        dispatchCalls = []
        dispatchCalls = []
        def dispatch(name, instancePtr, *args):
            dispatchCalls.append((name, instancePtr, args))
            return result
        
        def TestType(_type):
            args = ("for", "the", "horde")
            instance = _type()
            _type._dispatcher.method_varargs = dispatch
            self.assertEquals(instance.method(*args), result, "didn't use correct _dispatcher method")
            self.assertEquals(dispatchCalls, [("klass.method", instance._instancePtr, args)], "called _dispatcher method wrong")
            self.assertVarargsDelegate(_type._dispatcher.table["klass.method"], calls)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()
        

    def testVarargsKwargsMethod(self):
        calls = []
        def Kwargs(selfPtr, argsPtr, kwargsPtr):
            calls.append((selfPtr, argsPtr, kwargsPtr))
            return RESULT_PTR
        method, deallocMethod = MakeMethodDef("method", Kwargs, METH.VARARGS | METH.KEYWORDS)
        
        result = object()
        dispatchCalls = []
        def dispatch(name, instancePtr, *args, **kwargs):
            dispatchCalls.append((name, instancePtr, args, kwargs))
            return result
        
        def TestType(_type):
            args = ("for", "the", "horde")
            kwargs = {"g1": "LM", "g2": "BS", "g3": "GM"}
            instance = _type()
            _type._dispatcher.method_kwargs = dispatch
            self.assertEquals(instance.method(*args, **kwargs), result, "didn't use correct _dispatcher method")
            self.assertEquals(dispatchCalls, [("klass.method", instance._instancePtr, args, kwargs)], "called _dispatcher method wrong")
            self.assertKwargsDelegate(_type._dispatcher.table["klass.method"], calls)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


class DispatchCallTest(DispatchSetupTestCase):
    
    def testCall(self):
        calls = []
        def Call(selfPtr, argsPtr, kwargsPtr):
            calls.append((selfPtr, argsPtr, kwargsPtr))
            return RESULT_PTR
        
        result = object()
        dispatchCalls = []
        def dispatch(name, instancePtr, *args, **kwargs):
            dispatchCalls.append((name, instancePtr, args, kwargs))
            return result
        
        def TestType(_type):
            args = ("for", "the", "horde")
            kwargs = {"g1": "LM", "g2": "BS", "g3": "GM"}
            instance = _type()
            _type._dispatcher.method_kwargs = dispatch
            self.assertEquals(instance(*args, **kwargs), result)
            self.assertEquals(dispatchCalls, [("klass.__call__", instance._instancePtr, args, kwargs)])
            self.assertKwargsDelegate(_type._dispatcher.table["klass.__call__"], calls)
            
            del instance
            gcwait()

        typeSpec = {
            "tp_name": "klass",
            "tp_call": Call,
        }
        self.assertTypeSpec(typeSpec, TestType)

class DispatchIterTest(TestCase):

    def assertDispatchesToSelfTypeMethod(self, mapper, typeSpec, expectedKeyName,
                                         expectedMethodName, TestErrorHandler):
        deallocTypes = CreateTypes(mapper)
        
        typeSpec["tp_name"] = "klass"
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        result = object()
        instance = _type()
        expectedInstancePtr = instance._instancePtr

        def MockDispatchFunc(methodName, selfPtr, errorHandler=None):
            self.assertEquals(methodName, "klass." + expectedKeyName, "called wrong method")
            self.assertEquals(selfPtr, expectedInstancePtr, "called method on wrong instance")
            TestErrorHandler(errorHandler)
            return result
        _type._dispatcher.method_selfarg = MockDispatchFunc
        
        self.assertEquals(getattr(instance, expectedMethodName)(), result, "bad return")
        
        del instance
        gcwait()
        deallocType()
        deallocTypes()


    def test_tp_iter_MethodDispatch(self):
        mapper = Python25Mapper()
        
        def TestErrorHandler(errorHandler): 
            self.assertEquals(errorHandler, None, "no special error handling required")

        typeSpec = {
            "tp_iter": lambda _: IntPtr.Zero,
            "tp_flags": Py_TPFLAGS.HAVE_ITER
        }
        self.assertDispatchesToSelfTypeMethod(
            mapper, typeSpec, "tp_iter", "__iter__", TestErrorHandler)
        mapper.Dispose()


    def test_tp_iternext_MethodDispatch(self):
        mapper = Python25Mapper()
        
        def TestErrorHandler(errorHandler): 
            errorHandler(IntPtr(12345))
            self.assertRaises(StopIteration, errorHandler, IntPtr.Zero)
            mapper.LastException = ValueError()
            errorHandler(IntPtr.Zero)

        typeKwargs = {
            "tp_iternext": lambda _: IntPtr.Zero,
            "tp_flags": Py_TPFLAGS.HAVE_ITER
        }
        
        self.assertDispatchesToSelfTypeMethod(
            mapper, typeKwargs, "tp_iternext", "next", TestErrorHandler)
        mapper.Dispose()


class DispatchTrickyMethodsTest(TestCase):

    def testNewInitDelTablePopulation(self):
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


    def testNewInitDelDispatch(self):
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
        def test_tp_new(typePtr_new, argsPtr, kwargsPtr):
            calls.append("tp_new")
            self.assertEquals(typePtr_new, typePtr)
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS)
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS)
            return instancePtr
        
        def test_tp_init(instancePtr_init, argsPtr, kwargsPtr):
            calls.append("tp_init")
            self.assertEquals(instancePtr_init, instancePtr)
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS)
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS)
            return 0
            
        _type._dispatcher.table['klass.tp_new'] = Python25Api.PyType_GenericNew_Delegate(test_tp_new)
        _type._dispatcher.table['klass.tp_init'] = CPython_initproc_Delegate(test_tp_init)
        
        instance = _type(*ARGS, **KWARGS)
        self.assertEquals(instance._instancePtr, instancePtr)
        self.assertEquals(calls, ['tp_new', 'tp_init'])
        
        del instance
        gcwait()
        self.assertEquals(calls, ['tp_new', 'tp_init', 'tp_dealloc'])
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    def testDeleteOnlyWhenAppropriate(self):
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
        
        # now, another bridge object gets destroyed, causing us to reexamine
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
    
    def assertGetSet(self, mapper, attr, get, set, TestType, closure=IntPtr.Zero):
        doc = "take me to the airport, put me on a plane"
        getset, deallocGetset = MakeGetSetDef(attr, get, set, doc, closure)
        
        typeSpec = {
            "tp_name": 'klass',
            "tp_getset": [getset],
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        self.assertEquals(_type.boing.__doc__, doc, "bad docstring")
        TestType(_type)
        
        deallocGetset()
        deallocType()
    
    
    def testGet(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
        
        self.assertGetSet(mapper, "boing", get, None, TestType)
        mapper.Dispose()
        deallocTypes()


    def testSet(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
                instance.boing
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when getting set-only property")
                
            value = "see my vest, see my vest, made from real gorilla chest"
            instance.boing = value
            self.assertEquals(calls, [('Setter', ('klass.__set_boing', instance._instancePtr, value, IntPtr.Zero))])
            del instance
            gcwait()
            
        self.assertGetSet(mapper, "boing", None, set, TestType)
        mapper.Dispose()
        deallocTypes()
        

    def testClosure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        closurePtr = IntPtr(12345)
        
        def get(_, __):
            self.fail("this should have been patched out in TestType")
        def set(_, __, ___):
            self.fail("this should have been patched out in TestType")
        
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
            
            self.assertEquals(instance.boing, result, "wrong result")
            value = "I've been called a greasy thug too, and it never stops hurting."
            instance.boing = value
            self.assertEquals(calls, 
                [('Getter', ('klass.__get_boing', instance._instancePtr, closurePtr)),
                 ('Setter', ('klass.__set_boing', instance._instancePtr, value, closurePtr))],
                "wrong calls")
            del instance
            gcwait()
            
        self.assertGetSet(mapper, "boing", get, set, TestType, closurePtr)
        mapper.Dispose()
        deallocTypes()


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
        deallocType()
    
        
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
            
        self.assertMember(mapper, 'boing', MemberT.INT, offset, 1, TestType)
        mapper.Dispose()
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
        self.assertMember(mapper, attr, getattr(MemberT, name.upper()), offset, 0, TestType)
    
        mapper.Dispose()
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
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        metaclassPtr, deallocMC = MakeTypePtr(mapper, {'tp_name': 'metaclass'})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': metaclassPtr})
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(type(klass), mapper.Retrieve(metaclassPtr), "didn't notice klass's type")
        
        mapper.Dispose()
        deallocType()
        deallocMC()
        deallocTypes()
    
    
    def testInheritMethodTableFromMetaclass(self):
        "probably won't work quite right with identically-named metaclass"
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        metaclassPtr, deallocMC = MakeTypePtr(mapper, {'tp_name': 'metaclass'})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': metaclassPtr})

        klass = mapper.Retrieve(klassPtr)
        metaclass = mapper.Retrieve(metaclassPtr)
        for k, v in metaclass._dispatcher.table.items():
            self.assertEquals(klass._dispatcher.table[k], v)

        del klass
        gcwait()

        mapper.Dispose()
        deallocType()
        deallocMC()
        deallocTypes()


suite = makesuite(
    DispatchTypeMethodsTest,
    DispatchCallTest,
    DispatchIterTest,
    DispatchTrickyMethodsTest,
    PropertiesTest,
    MembersTest,
    InheritanceTest,
)
if __name__ == '__main__':
    run(suite)
