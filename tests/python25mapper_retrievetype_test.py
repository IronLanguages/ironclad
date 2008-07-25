
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
EMPTY_KWARGS_PTR = IntPtr.Zero
RESULT_PTR = IntPtr(999)
ERROR_RESULT_PTR = IntPtr.Zero


Null_CPythonVarargsFunction = lambda _, __: IntPtr.Zero
Null_CPythonVarargsKwargsFunction = lambda _, __, ___: IntPtr.Zero


class Python25Mapper_DispatchTypeMethodsTest(TestCase):

    def assertAddTypeObject_withSingleMethod(self, mapper, methodDef, TestType):
        deallocTypes = CreateTypes(mapper)
        
        typeSpec = {
            "tp_name": "klass",
            "tp_methods": [methodDef]
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        _type = mapper.Retrieve(typePtr)
        TestType(_type)
        
        deallocType()
        deallocTypes()
            
            
    def testNoArgsMethod(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsFunction, METH.NOARGS)
        
        def TestType(_type):
            result = object()
            def dispatch(name, instancePtr):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                return result
            _type._dispatcher.method_noargs = dispatch
            instance = _type()
            self.assertEquals(instance.method(), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestType)
        mapper.Dispose()
        deallocMethod()


    def testObjArgMethod(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsFunction, METH.O)
        
        def TestType(_type):
            arg = object()
            result = object()
            def dispatch(name, instancePtr, dispatch_arg):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                self.assertEquals(dispatch_arg, arg, "called with wrong arg")
                return result
            _type._dispatcher.method_objarg = dispatch
            instance = _type()
            self.assertEquals(instance.method(arg), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestType)
        mapper.Dispose()
        deallocMethod()


    def testVarargsMethod(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsFunction, METH.VARARGS)
        
        def TestType(_type):
            args = ("for", "the", "horde")
            result = object()
            def dispatch(name, instancePtr, *dispatch_args):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                self.assertEquals(dispatch_args, args, "called with wrong args")
                return result
            _type._dispatcher.method_varargs = dispatch
            instance = _type()
            self.assertEquals(instance.method(*args), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestType)
        mapper.Dispose()
        deallocMethod()
        

    def testVarargsKwargsMethod(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsKwargsFunction, METH.VARARGS | METH.KEYWORDS)
        
        def TestType(_type):
            args = ("for", "the", "horde")
            kwargs = {"g1": "LM", "g2": "BS", "g3": "GM"}
            result = object()
            def dispatch(name, instancePtr, *dispatch_args, **dispatch_kwargs):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                self.assertEquals(dispatch_args, args, "called with wrong args")
                self.assertEquals(dispatch_kwargs, kwargs, "called with wrong args")
                return result
            _type._dispatcher.method_kwargs = dispatch
            instance = _type()
            self.assertEquals(instance.method(*args, **kwargs), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestType)
        mapper.Dispose()
        deallocMethod()


class Python25Mapper_DispatchIterTest(TestCase):

    def assertDispatchesToSelfTypeMethod(self, mapper, typeSpec, expectedKeyName,
                                         expectedMethodName, TestErrorHandler):
        deallocTypes = CreateTypes(mapper)
        
        typeSpec["tp_name"] = "klass"
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)

        result = object()
        instance = _type()
        def MockDispatchFunc(methodName, selfPtr, errorHandler=None):
            self.assertEquals(methodName, "klass." + expectedKeyName, "called wrong method")
            self.assertEquals(selfPtr, instance._instancePtr, "called method on wrong instance")
            TestErrorHandler(errorHandler)
            return result
        _type._dispatcher.method_selfarg = MockDispatchFunc
        
        self.assertEquals(getattr(instance, expectedMethodName)(), result, "bad return")
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


class Python25Mapper_DispatchTrickyMethodsTest(TestCase):

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
        table['klass.tp_dealloc'](IntPtr.Zero)
        self.assertEquals(calls, ['tp_new', 'tp_init', 'tp_dealloc'], "not hooked up somewhere")
        
        mapper.Dispose()
        deallocType()
        deallocTypes()


    def testNewInitDelDispatch(self):
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        # all methods should be patched out
        def Raise(msg):
            raise Exception(msg)
        typeSpec = {
            "tp_name": "klass",
            "tp_new": lambda _, __, ___: Raise("new unpatched"),
            "tp_init": lambda _, __, ___: Raise("init unpatched"),
            "tp_dealloc": lambda _: Raise("dealloc unpatched"),
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        ARGS = (1, "two")
        KWARGS = {"three": 4}
        instancePtr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(instancePtr, PyObject, 'ob_refcnt', 1)
        CPyMarshal.WritePtrField(instancePtr, PyObject, 'ob_type', mapper.PyBaseObject_Type)
        
        calls = []
        def test_tp_new(typePtr_new, argsPtr, kwargsPtr):
            calls.append("tp_new")
            self.assertEquals(typePtr_new, typePtr, "wrong type")
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS, "wrong args")
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS, "wrong kwargs")
            return instancePtr
        
        def test_tp_init(instancePtr_init, argsPtr, kwargsPtr):
            calls.append("tp_init")
            self.assertEquals(instancePtr_init, instancePtr, "wrong instance")
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS, "wrong args")
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS, "wrong kwargs")
            return 0
        
        def test_tp_dealloc(instancePtr_dealloc):
            calls.append("tp_dealloc")
            self.assertEquals(instancePtr_dealloc, instancePtr, "wrong instance")
            # finish the dealloc to avoid confusing mapper on shutdown
            mapper.PyObject_Free(instancePtr_dealloc)
            
        _type._dispatcher.table['klass.tp_new'] = Python25Api.PyType_GenericNew_Delegate(test_tp_new)
        _type._dispatcher.table['klass.tp_init'] = CPython_initproc_Delegate(test_tp_init)
        _type._dispatcher.table['klass.tp_dealloc'] = CPython_destructor_Delegate(test_tp_dealloc)
        
        instance = _type(*ARGS, **KWARGS)
        self.assertEquals(instance._instancePtr, instancePtr, "wrong instance,")
        self.assertEquals(calls, ['tp_new', 'tp_init'], 'wrong calls')
        
        del instance
        gcwait()
        self.assertEquals(calls, ['tp_new', 'tp_init', 'tp_dealloc'], 'wrong calls')
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    def testDeleteResurrect(self):
        # when an object is finalized, it checks for unmanaged references to itself
        # and resurrects itself (by calling mapper.Strengthen) if there are any. 
        # from that point, the object will become unkillable until we Weaken it again.
        # in the absence of any better ideas, we decided to check for undead objects
        # whenever we delete other potentially-undead objects, and let them live forever
        # otherwise.
        #
        # if this test passes, the previous paragraph is probably correct
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)

        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        _type = mapper.Retrieve(typePtr)
        
        obj1 = _type()
        obj1ref = WeakReference(obj1, True)
        obj2 = _type()
        
        # unmanaged code grabs a reference
        instancePtr = obj1._instancePtr
        CPyMarshal.WriteIntField(instancePtr, PyObject, 'ob_refcnt', 2)
        del obj1
        gcwait()
        self.assertEquals(obj1ref.IsAlive, True, "object died before its time")
        self.assertEquals(mapper.Retrieve(instancePtr), obj1ref.Target, "mapping broken")
        
        # unmanaged code forgets it
        CPyMarshal.WriteIntField(instancePtr, PyObject, 'ob_refcnt', 1)
        gcwait()
        # nothing has happened that would cause us to reexamine strong refs, 
        # so the object shouldn't just die on us
        self.assertEquals(obj1ref.IsAlive, True, "object died unexpectedly")
        self.assertEquals(mapper.Retrieve(instancePtr), obj1ref.Target, "mapping broken")
        
        del obj2
        gcwait()
        # the above should have made our reference to obj1 weak again, but
        # it shouldn't be collected until the next GC
        gcwait()
        self.assertEquals(obj1ref.IsAlive, False, "object didn't die")
        
        mapper.Dispose()
        deallocType()
        deallocTypes()


class Python25Mapper_PropertiesTest(TestCase):
    
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
            
            def Set():
                instance.boing = 'splat'
            self.assertRaises(AttributeError, Set)
        
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
            
            self.assertRaises(AttributeError, lambda: instance.boing)
            value = "see my vest, see my vest, made from real gorilla chest"
            instance.boing = value
            self.assertEquals(calls, [('Setter', ('klass.__set_boing', instance._instancePtr, value, IntPtr.Zero))])
            
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
            
        self.assertGetSet(mapper, "boing", get, set, TestType, closurePtr)
        mapper.Dispose()
        deallocTypes()


class Python25Mapper_MembersTest(TestCase):
    
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
            
            def Set():
                instance.boing = 54231
            self.assertRaises(AttributeError, Set)
            
            calls = []
            def Get(address):
                calls.append(('Get', (address,)))
                return 12345
            _type._dispatcher.get_member_int = Get
            
            self.assertEquals(instance.boing, 12345)
            self.assertEquals(calls, [
                ('Get', (fieldPtr,)),
            ])
            
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
        

class Python25Mapper_InheritanceTest(TestCase):
    
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
        



suite = makesuite(
    Python25Mapper_DispatchTypeMethodsTest,
    Python25Mapper_DispatchIterTest,
    Python25Mapper_DispatchTrickyMethodsTest,
    Python25Mapper_PropertiesTest,
    Python25Mapper_MembersTest,
    Python25Mapper_InheritanceTest,
)
if __name__ == '__main__':
    run(suite)