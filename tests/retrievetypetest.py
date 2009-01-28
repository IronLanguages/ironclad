
from tests.utils.runtest import automakesuite, run
    
from tests.utils.cpython import MakeGetSetDef, MakeMethodDef, MakeNumSeqMapMethods, MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, HGlobalAllocator, Python25Mapper
from Ironclad.Structs import (
    MemberT, METH, PyMemberDef, PyNumberMethods, PyStringObject, 
    PyIntObject, PyObject, PyMappingMethods, PySequenceMethods, PyTypeObject
)
   
def Raise(*_):
    raise Exception('should never have called this')     
        
class LifetimeTest(TestCase):
    
    @WithMapper
    def testObjectSurvives(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        addToCleanUp(deallocType)
        
        _type = mapper.Retrieve(typePtr)
        
        obj = _type()
        objref = WeakReference(obj, True)
        
        # for unmanaged code to mess with ob_refcnt, it must have been passed a reference
        # from managed code; this shouldn't happen without a Store (which will IncRef)
        objptr = mapper.Store(obj)
        self.assertEquals(mapper.RefCount(objptr), 2)
        CPyMarshal.WriteIntField(objptr, PyObject, 'ob_refcnt', 3)
        mapper.DecRef(objptr)
        
        # managed code forgets obj for a while, while unmanaged code still holds a reference
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "object died before its time")
        self.assertEquals(mapper.Retrieve(objptr), objref.Target, "mapping broken")


    @WithMapper
    def testObjectDies(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        _type = mapper.Retrieve(typePtr)
        addToCleanUp(deallocType)
        
        obj = _type()
        objref = WeakReference(obj, True)
        
        # for unmanaged code to mess with ob_refcnt, it must have been passed a reference
        # from managed code; this shouldn't happen without a Store (which will IncRef)
        objptr = mapper.Store(obj)
        self.assertEquals(mapper.RefCount(objptr), 2)
        mapper.DecRef(objptr)
        
        # managed code forgets obj, no refs from unmanaged code
        del obj
        gcwait()
        gcwait()
        self.assertEquals(objref.IsAlive, False, "object didn't die")


class InheritanceTest(TestCase):
    
    @WithMapper
    def testBaseClass(self, mapper, addToCleanUp):
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        addToCleanUp(deallocBase)

        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr})
        addToCleanUp(deallocType)
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(issubclass(klass, mapper.Retrieve(basePtr)), True, "didn't notice klass's base class")
        self.assertEquals(mapper.RefCount(mapper.PyType_Type), 3, "types did not keep references to TypeType")
        self.assertEquals(mapper.RefCount(basePtr), 3, "subtype did not keep reference to base")
        self.assertEquals(mapper.RefCount(mapper.PyBaseObject_Type), 2, "base type did not keep reference to its base (even if it wasn't set explicitly)")
        self.assertEquals(CPyMarshal.ReadPtrField(basePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type")

    
    @WithMapper
    def testInheritsMethodTable(self, mapper, addToCleanUp):
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr})
        addToCleanUp(deallocType)

        klass = mapper.Retrieve(klassPtr)
        base = mapper.Retrieve(basePtr)
        for k, v in base._dispatcher.table.items():
            self.assertEquals(klass._dispatcher.table[k], v)

    
    @WithMapper
    def testMultipleBases(self, mapper, addToCleanUp):
        base1Ptr, deallocBase1 = MakeTypePtr(mapper, {'tp_name': 'base1', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        addToCleanUp(deallocBase1)

        base2Ptr, deallocBase2 = MakeTypePtr(mapper, {'tp_name': 'base2', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        addToCleanUp(deallocBase2)

        bases = (mapper.Retrieve(base1Ptr,), mapper.Retrieve(base2Ptr))
        basesPtr = mapper.Store(bases)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': base1Ptr, 'tp_bases': basesPtr})
        addToCleanUp(deallocType)
        
        klass = mapper.Retrieve(klassPtr)
        for base in bases:
            self.assertEquals(issubclass(klass, base), True)
        self.assertEquals(mapper.RefCount(base1Ptr), 5, "subtype did not keep reference to bases")
        self.assertEquals(mapper.RefCount(base2Ptr), 4, "subtype did not keep reference to bases")
        self.assertEquals(CPyMarshal.ReadPtrField(base1Ptr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type 1")
        self.assertEquals(CPyMarshal.ReadPtrField(base2Ptr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type 2")
    
    
    @WithMapper
    def testInheritMethodTableFromMultipleBases(self, mapper, addToCleanUp):
        "probably won't work quite right with identically-named base classes"
        base1Ptr, deallocBase1 = MakeTypePtr(mapper, {'tp_name': 'base1', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase1)

        base2Ptr, deallocBase2 = MakeTypePtr(mapper, {'tp_name': 'base2', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase2)

        bases = (mapper.Retrieve(base1Ptr,), mapper.Retrieve(base2Ptr))
        basesPtr = mapper.Store(bases)

        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': base1Ptr, 'tp_bases': basesPtr})
        addToCleanUp(deallocType)
        klass = mapper.Retrieve(klassPtr)

        for base in bases:
            for k, v in base._dispatcher.table.items():
                self.assertEquals(klass._dispatcher.table[k], v)

    
    @WithMapper
    def testMultipleBasesIncludingBuiltin(self, mapper, addToCleanUp):
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase)

        bases = (mapper.Retrieve(basePtr), int)
        basesPtr = mapper.Store(bases)
        typeSpec = {
            'tp_name': 'klass',
            'ob_type': mapper.PyType_Type,
            'tp_base': basePtr,
            'tp_bases': basesPtr
        }
        klassPtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)

        klass = mapper.Retrieve(klassPtr)
        for base in bases:
            self.assertEquals(issubclass(klass, base), True)

        unknownInstancePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(unknownInstancePtr))

        CPyMarshal.WriteIntField(unknownInstancePtr, PyObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(unknownInstancePtr, PyObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(unknownInstancePtr, PyIntObject, "ob_ival", 123)
        unknownInstance = mapper.Retrieve(unknownInstancePtr)
        self.assertEquals(isinstance(unknownInstance, klass), True)

    
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


class BuiltinSubclassHorrorTest(TestCase):
    
    @WithMapper
    def testRetrievedIntsHaveCorrectValue(self, mapper, deallocLater):
        # this is the only way I can tell what the underlying 'int' value is
        # (as opposed to the value returned from __int__, which does not get called
        # when passed into __getslice__)
        calls = []
        class SequenceLike(object):
            def __getslice__(self, i, j):
                calls.append(('__getslice__', i, j))
                return []

        typeSpec = {
            'tp_name': 'klass',
            'tp_base': mapper.PyInt_Type,
            'tp_basicsize': Marshal.SizeOf(PyIntObject)
        }
        klassPtr, deallocType = MakeTypePtr(mapper, typeSpec)
        deallocLater(deallocType)
        
        _12Ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        deallocLater(lambda: Marshal.FreeHGlobal(_12Ptr))
        CPyMarshal.WriteIntField(_12Ptr, PyIntObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(_12Ptr, PyIntObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(_12Ptr, PyIntObject, "ob_ival", 12)
        
        _44Ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        deallocLater(lambda: Marshal.FreeHGlobal(_44Ptr))
        CPyMarshal.WriteIntField(_44Ptr, PyIntObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(_44Ptr, PyIntObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(_44Ptr, PyIntObject, "ob_ival", 44)
        
        SequenceLike()[mapper.Retrieve(_12Ptr):mapper.Retrieve(_44Ptr)]
        self.assertEquals(calls, [('__getslice__', 12, 44)])
        self.assertEquals(map(type, calls[0]), [str, int, int])
    
    
    @WithMapper
    def testRetrievedStringsHaveCorrectValue(self, mapper, deallocLater):
        typeSpec = {
            'tp_name': 'klass',
            'tp_base': mapper.PyString_Type,
            'tp_basicsize': Marshal.SizeOf(PyStringObject) - 1,
            'tp_itemsize': 1,
        }
        klassPtr, deallocType = MakeTypePtr(mapper, typeSpec)
        deallocLater(deallocType)
        
        _f0oSize = Marshal.SizeOf(PyStringObject) + 3
        _f0oPtr = Marshal.AllocHGlobal(_f0oSize)
        CPyMarshal.Zero(_f0oPtr, _f0oSize)
        deallocLater(lambda: Marshal.FreeHGlobal(_f0oPtr))
        CPyMarshal.WriteIntField(_f0oPtr, PyStringObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(_f0oPtr, PyStringObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(_f0oPtr, PyStringObject, "ob_size", 3)
        dataPtr = CPyMarshal.Offset(_f0oPtr, Marshal.OffsetOf(PyStringObject, "ob_sval"))
        for char in 'f\0o\0':
            CPyMarshal.WriteByte(dataPtr, ord(char))
            dataPtr = CPyMarshal.Offset(dataPtr, 1)
            
        _f0o = mapper.Retrieve(_f0oPtr)
        self.assertEquals(_f0o == 'f\0o', True)
        self.assertEquals('f\0o' == _f0o, True)
        

class TypeDictTest(TestCase):
    
    @WithMapper
    def testRetrieveAssignsDictTo_tp_dict(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": "klass"})
        addToCleanUp(deallocType)
        
        _type = mapper.Retrieve(typePtr)
        _typeDictPtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict")
        self.assertEquals(mapper.Retrieve(_typeDictPtr), _type.__dict__)


OFFSET = 32
BIG_ENOUGH = 64
def MakeInstanceWithField(type_, readonly, mapper, addToCleanUp):
    member = PyMemberDef('attr', type_, OFFSET, readonly, "doc")
    typeSpec = {
        'tp_basicsize': BIG_ENOUGH,
        'tp_members': [member],
    }
    typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
    addToCleanUp(deallocType)
    
    instance = mapper.Retrieve(typePtr)()
    instancePtr = mapper.Store(instance)
    fieldPtr = CPyMarshal.Offset(instancePtr, OFFSET)
    return instance, fieldPtr
    
class FieldsTest(TestCase):
    
    @WithMapper
    def testIntFieldReadOnly(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.INT, 1, mapper, addToCleanUp)
        
        def Set():
            instance.attr = 1234567
        self.assertRaises(AttributeError, Set)
        
        CPyMarshal.WriteInt(fieldPtr, -54321)
        self.assertEquals(instance.attr, -54321)
        
    @WithMapper
    def testIntFieldReadWrite(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.INT, 0, mapper, addToCleanUp)
        
        instance.attr = 1234567
        self.assertEquals(CPyMarshal.ReadInt(fieldPtr), 1234567)
        
        CPyMarshal.WriteInt(fieldPtr, -54321)
        self.assertEquals(instance.attr, -54321)
    
    @WithMapper
    def testDoubleFieldReadOnly(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.DOUBLE, 1, mapper, addToCleanUp)
        
        def Set():
            instance.attr = 1234.567
        self.assertRaises(AttributeError, Set)
        
        CPyMarshal.WriteDouble(fieldPtr, -54.321)
        self.assertEquals(instance.attr, -54.321)
        
    @WithMapper
    def testIntFieldReadWrite(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.DOUBLE, 0, mapper, addToCleanUp)
        
        instance.attr = 1234.567
        self.assertEquals(CPyMarshal.ReadDouble(fieldPtr), 1234.567)
        
        CPyMarshal.WriteDouble(fieldPtr, -54.321)
        self.assertEquals(instance.attr, -54.321)
    
    @WithMapper
    def testCharFieldReadOnly(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.CHAR, 1, mapper, addToCleanUp)
        
        def Set():
            instance.attr = 'X'
        self.assertRaises(AttributeError, Set)
        
        CPyMarshal.WriteByte(fieldPtr, ord('Y'))
        self.assertEquals(instance.attr, 'Y')
        
    @WithMapper
    def testCharFieldReadWrite(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.CHAR, 0, mapper, addToCleanUp)
        
        instance.attr = 'A'
        self.assertEquals(CPyMarshal.ReadByte(fieldPtr), ord('A'))
        
        CPyMarshal.WriteByte(fieldPtr, ord('B'))
        self.assertEquals(instance.attr, 'B')
    
    
    @WithMapper
    def testUbyteFieldReadOnly(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.UBYTE, 1, mapper, addToCleanUp)
        
        def Set():
            instance.attr = 135
        self.assertRaises(AttributeError, Set)
        
        CPyMarshal.WriteByte(fieldPtr, 192)
        self.assertEquals(instance.attr, 192)
        
    @WithMapper
    def testUbyteFieldReadWrite(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.UBYTE, 0, mapper, addToCleanUp)
        
        instance.attr = 135
        self.assertEquals(CPyMarshal.ReadByte(fieldPtr), 135)
        
        CPyMarshal.WriteByte(fieldPtr, 222)
        self.assertEquals(instance.attr, 222)
    
    
    @WithMapper
    def testObjectFieldReadOnly(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.OBJECT, 1, mapper, addToCleanUp)
        
        def Set():
            instance.attr = object()
        self.assertRaises(AttributeError, Set)
        
        CPyMarshal.WritePtr(fieldPtr, IntPtr.Zero)
        self.assertEquals(instance.attr, None)
        
        value = object()
        valuePtr = mapper.Store(value)
        refcnt = mapper.RefCount(valuePtr)
        
        CPyMarshal.WritePtr(fieldPtr, valuePtr)
        self.assertEquals(instance.attr, value)
        self.assertEquals(mapper.RefCount(valuePtr), refcnt)
    
    
    @WithMapper
    def testObjectFieldReadWrite(self, mapper, addToCleanUp):
        instance, fieldPtr = MakeInstanceWithField(MemberT.OBJECT, 0, mapper, addToCleanUp)
        
        CPyMarshal.WritePtr(fieldPtr, IntPtr.Zero)
        value = object()
        valuePtr = mapper.Store(value)
        refcnt = mapper.RefCount(valuePtr)
        
        instance.attr = value
        self.assertEquals(instance.attr, value)
        self.assertEquals(CPyMarshal.ReadPtr(fieldPtr), valuePtr)
        self.assertEquals(mapper.RefCount(valuePtr), refcnt + 1)
        
        instance.attr = None # should this set fieldPtr to NULL, perhaps?
        self.assertEquals(CPyMarshal.ReadPtr(fieldPtr), mapper.Store(None))
        self.assertEquals(mapper.RefCount(valuePtr), refcnt)
        
        

class MethodConnectionTestCase(TestCase):

    @WithMapper
    def assertTypeMethodCall(self, typeSpec, methodName, args, kwargs, result, mapper, addToCleanUp):
        self.mapper = mapper
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        self.instance = mapper.Retrieve(typePtr)()
        method = getattr(self.instance, methodName)
        self.assertEquals(method(*args, **kwargs), result)

    @WithMapper
    def assertTypeMethodRaises(self, typeSpec, methodName, args, kwargs, error, mapper, addToCleanUp):
        self.mapper = mapper
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        self.instance = mapper.Retrieve(typePtr)()
        method = getattr(self.instance, methodName)
        self.assertRaises(error, lambda: method(*args, **kwargs))

    @WithMapper
    def assertGetCall(self, typeSpec, attrName, result, mapper, addToCleanUp):
        self.mapper = mapper
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        self.instance = mapper.Retrieve(typePtr)()
        self.assertEquals(getattr(self.instance, attrName), result)

    @WithMapper
    def assertSetCall(self, typeSpec, attrName, value, mapper, addToCleanUp):
        self.mapper = mapper
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        self.instance = mapper.Retrieve(typePtr)()
        setattr(self.instance, attrName, value)


class MethodsTest(MethodConnectionTestCase):

    def testNoArgsMethod(self):
        result = object()
        def NoArgs(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(p2, IntPtr.Zero)
            return self.mapper.Store(result)
        
        methodDef, deallocMethod = MakeMethodDef("method", NoArgs, METH.NOARGS)
        typeSpec = {"tp_methods": [methodDef]}
        self.assertTypeMethodCall(typeSpec, "method", (), {}, result)
        deallocMethod()
    

    def testObjArgMethod(self):
        result = object()
        arg = object()
        def ObjArg(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), arg)
            return self.mapper.Store(result)
        
        methodDef, deallocMethod = MakeMethodDef("method", ObjArg, METH.O)
        typeSpec = {"tp_methods": [methodDef]}
        self.assertTypeMethodCall(typeSpec, "method", (arg,), {}, result)
        deallocMethod()
    

    def testVarArgsMethod(self):
        result = object()
        args = (object(), object(), object())
        def VarArgs(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), args)
            return self.mapper.Store(result)
        
        methodDef, deallocMethod = MakeMethodDef("method", VarArgs, METH.VARARGS)
        typeSpec = {"tp_methods": [methodDef]}
        self.assertTypeMethodCall(typeSpec, "method", args, {}, result)
        deallocMethod()
    

    def testKwargsMethod(self):
        result = object()
        args = (object(), object(), object())
        kwargs = {'x': object(), 'y': object()}
        def Kwargs(p1, p2, p3):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), args)
            self.assertEquals(self.mapper.Retrieve(p3), kwargs)
            return self.mapper.Store(result)
        
        methodDef, deallocMethod = MakeMethodDef("method", Kwargs, METH.VARARGS | METH.KEYWORDS)
        typeSpec = {"tp_methods": [methodDef]}
        self.assertTypeMethodCall(typeSpec, "method", args, kwargs, result)
        deallocMethod()


MAGIC_CLOSURE_PTR = IntPtr(12345)
class GetsetsTest(MethodConnectionTestCase):

    def testGet(self):
        result = object()
        def Getter(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(p2, MAGIC_CLOSURE_PTR)
            return self.mapper.Store(result)
        
        getsetDef, deallocGetset = MakeGetSetDef("attr", Getter, None, "doc", MAGIC_CLOSURE_PTR)
        typeSpec = {"tp_getset": [getsetDef]}
        self.assertGetCall(typeSpec, "attr", result)
        self.assertRaises(AttributeError, self.assertSetCall, typeSpec, "attr", object())
        deallocGetset()

    def testSet(self):
        value = object()
        def Setter(p1, p2, p3):
            self.didCall = True
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), value)
            self.assertEquals(p3, MAGIC_CLOSURE_PTR)
            return self.result
        
        getsetDef, deallocGetset = MakeGetSetDef("attr", None, Setter, "doc", MAGIC_CLOSURE_PTR)
        typeSpec = {"tp_getset": [getsetDef]}
        
        self.result = 0
        self.didCall = False
        self.assertSetCall(typeSpec, "attr", value)
        self.assertEquals(self.didCall, True)
        
        self.result = -1
        self.didCall = False
        self.assertRaises(Exception, self.assertSetCall, typeSpec, "attr", value)
        self.assertEquals(self.didCall, True)
        
        deallocGetset()


class TypeMethodsTest(MethodConnectionTestCase):

    def testCall(self):
        result = object()
        args = (object(), object(), object())
        kwargs = {'x': object(), 'y': object()}
        def Call(p1, p2, p3):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), args)
            self.assertEquals(self.mapper.Retrieve(p3), kwargs)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_call": Call}
        self.assertTypeMethodCall(typeSpec, "__call__", args, kwargs, result)

    def testInit(self):
        args = (object(), object(), object())
        kwargs = {'x': object(), 'y': object()}
        def Init(p1, p2, p3):
            if self.firstCall:
                self.firstCall = False
                return 0
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), args)
            self.assertEquals(self.mapper.Retrieve(p3), kwargs)
            return 0
        
        typeSpec = {"tp_init": Init}
        self.firstCall = True
        self.assertTypeMethodCall(typeSpec, "__init__", args, kwargs, 0)

    def testInitUnknownError(self):
        def Init(p1, p2, p3):
            if self.firstCall:
                self.firstCall = False
                return 0
            return -1
        
        typeSpec = {"tp_init": Init}
        self.firstCall = True
        self.assertTypeMethodRaises(typeSpec, "__init__", (), {}, Exception)

    def testInitSpecificError(self):
        class BorkedException(Exception):
            pass
        def Init(p1, p2, p3):
            if self.firstCall:
                self.firstCall = False
                return 0
            self.mapper.LastException = BorkedException('omgwtfbbq')
            return -1
        
        typeSpec = {"tp_init": Init}
        self.firstCall = True
        self.assertTypeMethodRaises(typeSpec, "__init__", (), {}, BorkedException)
        
    def testStr(self):
        result = object()
        def Call(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_str": Call}
        self.assertTypeMethodCall(typeSpec, "__str__", (), {}, result)

    def testRepr(self):
        result = object()
        def Call(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_repr": Call}
        self.assertTypeMethodCall(typeSpec, "__repr__", (), {}, result)
    
    def testCompare(self):
        arg = object()
        def Compare(p1, p2):
            # note: assertEquals inside __cmp__ causes stack overflow
            self.assertEquals(self.mapper.Retrieve(p1) is self.instance, True)
            self.assertEquals(self.mapper.Retrieve(p2), arg)
            return 0
        
        typeSpec = {"tp_compare": Compare}
        self.assertTypeMethodCall(typeSpec, "__cmp__", (arg,), {}, 0)
        
    def testRichCompare(self):
        arg = object()
        result = object()
        def RichCompare(p1, p2, i1):
            # note: assertEquals inside __eq__ causes stack overflow
            self.assertEquals(self.mapper.Retrieve(p1) is self.instance, True)
            self.assertEquals(self.mapper.Retrieve(p2), arg)
            self.assertEquals(i1, self.expectCode)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_richcompare": RichCompare}
        richcmp_methods = ['__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',]
        for (code, method) in enumerate(richcmp_methods):        
            self.expectCode = code
            self.assertTypeMethodCall(typeSpec, method, (arg,), {}, result)

    def testHash(self):
        def Hash(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return -1
        
        typeSpec = {"tp_hash": Hash}
        self.assertTypeMethodCall(typeSpec, "__hash__", (), {}, -1)

    def testGetattr(self):
        arg = "hugs_tiem"
        result = object()
        def Getattr(p1, str1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(str1, arg)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_getattr": Getattr}
        self.assertTypeMethodCall(typeSpec, "__getattr__", (arg,), {}, result)

    def testIter(self):
        result = object()
        def Iter(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_iter": Iter}
        self.assertTypeMethodCall(typeSpec, "__iter__", (), {}, result)

    def testIternext(self):
        result = object()
        def Iternext(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return self.mapper.Store(result)
        
        typeSpec = {"tp_iternext": Iternext}
        self.assertTypeMethodCall(typeSpec, "next", (), {}, result)

    def testIternext_Finished(self):
        def Iternext(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return IntPtr.Zero
        
        typeSpec = {"tp_iternext": Iternext}
        self.assertTypeMethodRaises(typeSpec, "next", (), {}, StopIteration)


class NumberMethodsTest(MethodConnectionTestCase):
    
    def assertUnaryFunc(self, cpyname, ipyname):
        result = object()
        def Unary(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return self.mapper.Store(result)
        
        numbers, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {cpyname: Unary})
        typeSpec = {"tp_as_number": numbers}
        self.assertTypeMethodCall(typeSpec, ipyname, (), {}, result)
        deallocNumbers()
    
    def testUnary(self):
        self.assertUnaryFunc('nb_negative', '__neg__')
        self.assertUnaryFunc('nb_positive', '__pos__')
        self.assertUnaryFunc('nb_absolute', '__abs__')
        self.assertUnaryFunc('nb_invert', '__invert__')
        self.assertUnaryFunc('nb_int', '__int__')
        self.assertUnaryFunc('nb_long', '__long__')
        self.assertUnaryFunc('nb_float', '__float__')
        self.assertUnaryFunc('nb_oct', '__oct__')
        self.assertUnaryFunc('nb_hex', '__hex__')
        self.assertUnaryFunc('nb_index', '__index__')
    
    def assertBinaryFunc(self, cpyname, ipyname, swapped=None):
        arg = object()
        result = object()
        def Binary(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), arg)
            return self.mapper.Store(result)
        
        numbers, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {cpyname: Binary})
        typeSpec = {"tp_as_number": numbers}
        self.assertTypeMethodCall(typeSpec, ipyname, (arg,), {}, result)
        deallocNumbers()
        
        if swapped:
            self.assertSwappedBinaryFunc(cpyname, swapped)
    
    def assertSwappedBinaryFunc(self, cpyname, ipyname):
        arg = object()
        result = object()
        def Binary(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), arg)
            self.assertEquals(self.mapper.Retrieve(p2), self.instance)
            return self.mapper.Store(result)
        
        numbers, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {cpyname: Binary})
        typeSpec = {"tp_as_number": numbers}
        self.assertTypeMethodCall(typeSpec, ipyname, (arg,), {}, result)
        deallocNumbers()
    
    def testBinary(self):
        self.assertBinaryFunc('nb_add', '__add__', '__radd__')
        self.assertBinaryFunc('nb_subtract', '__sub__', '__rsub__')
        self.assertBinaryFunc('nb_multiply', '__mul__', '__rmul__')
        self.assertBinaryFunc('nb_divide', '__div__', '__rdiv__')
        self.assertBinaryFunc('nb_remainder', '__mod__', '__rmod__')
        self.assertBinaryFunc('nb_divmod', '__divmod__', '__rdivmod__')
        
        self.assertBinaryFunc('nb_lshift', '__lshift__', '__rlshift__')
        self.assertBinaryFunc('nb_rshift', '__rshift__', '__rrshift__')
        self.assertBinaryFunc('nb_and', '__and__', '__rand__')
        self.assertBinaryFunc('nb_xor', '__xor__', '__rxor__')
        self.assertBinaryFunc('nb_or', '__or__', '__ror__')
        
        self.assertBinaryFunc('nb_inplace_add', '__iadd__')
        self.assertBinaryFunc('nb_inplace_subtract', '__isub__')
        self.assertBinaryFunc('nb_inplace_multiply', '__imul__')
        self.assertBinaryFunc('nb_inplace_divide', '__idiv__')
        self.assertBinaryFunc('nb_inplace_remainder', '__imod__')
        self.assertBinaryFunc('nb_inplace_lshift', '__ilshift__')
        self.assertBinaryFunc('nb_inplace_rshift', '__irshift__')
        self.assertBinaryFunc('nb_inplace_and', '__iand__')
        self.assertBinaryFunc('nb_inplace_xor', '__ixor__')
        self.assertBinaryFunc('nb_inplace_or', '__ior__')
        
        self.assertBinaryFunc('nb_floor_divide', '__floordiv__', '__rfloordiv__')
        self.assertBinaryFunc('nb_true_divide', '__truediv__', '__rtruediv__')
        self.assertBinaryFunc('nb_inplace_floor_divide', '__ifloordiv__')
        self.assertBinaryFunc('nb_inplace_true_divide', '__itruediv__')
    
    def testNonzero(self):
        result = 0
        def Nonzero(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return result
        
        numbers, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {'nb_nonzero': Nonzero})
        typeSpec = {"tp_as_number": numbers}
        self.assertTypeMethodCall(typeSpec, "__nonzero__", (), {}, result)
        deallocNumbers()
        
    def assertPowerFunc(self, cpyname, ipyname):
        arg = object()
        modulus = object()
        result = object()
        def Ternary(p1, p2, p3):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), arg)
            self.assertEquals(self.mapper.Retrieve(p3), self.expectModulus)
            return self.mapper.Store(result)
        
        numbers, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {cpyname: Ternary})
        typeSpec = {"tp_as_number": numbers}
        
        self.expectModulus = None
        self.assertTypeMethodCall(typeSpec, ipyname, (arg,), {}, result)
        
        self.expectModulus = modulus
        self.assertTypeMethodCall(typeSpec, ipyname, (arg, modulus), {}, result)

        deallocNumbers()
        
    def testPower(self):
        self.assertPowerFunc('nb_power', '__pow__')
        self.assertPowerFunc('nb_inplace_power', '__ipow__')
    
    def testPowerSwapped(self):
        arg = object()
        result = object()
        def Ternary(p1, p2, p3):
            self.assertEquals(self.mapper.Retrieve(p1), arg)
            self.assertEquals(self.mapper.Retrieve(p2), self.instance)
            self.assertEquals(self.mapper.Retrieve(p3), None)
            return self.mapper.Store(result)
        
        numbers, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {'nb_power': Ternary})
        typeSpec = {"tp_as_number": numbers}
        self.assertTypeMethodCall(typeSpec, '__rpow__', (arg,), {}, result)
        deallocNumbers()

    @WithMapper
    def testComplex(self, mapper, addToCleanUp):
        get_real = lambda *_: mapper.Store(123.0)
        get_imag = lambda *_: mapper.Store(456.0)
        
        getsets = []
        for (name, impl) in (('real', get_real), ('imag', get_imag)):
            getsetDef, deallocGetset = MakeGetSetDef(name, impl, None, '', IntPtr.Zero)
            getsets.append(getsetDef)
            addToCleanUp(deallocGetset)
        
        typeSpec = {
            'tp_getset': getsets
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        instance = mapper.Retrieve(typePtr)()
        self.assertEquals(instance.__complex__(), 123+456j)


class SequenceMethodsTest(MethodConnectionTestCase):

    def testLength(self):
        result = 0
        def Length(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return result
        
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_length': Length})
        typeSpec = {"tp_as_sequence": seq}
        self.assertTypeMethodCall(typeSpec, "__len__", (), {}, result)
        deallocSeq()


    def testConcat(self):
        # hey! if you're hooking up __iadd__, __radd__, __mul__, 
        # __imul__ or __rmul__, please add tests for those to 
        # CollisionsTest (below)
        arg = object()
        result = object()
        def Concat(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), arg)
            return self.mapper.Store(result)
        
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_concat': Concat})
        typeSpec = {"tp_as_sequence": seq}
        self.assertTypeMethodCall(typeSpec, "__add__", (arg,), {}, result)
        deallocSeq()


    def testGetitem(self):
        idx = 123
        result = object()
        def Getitem(p1, s1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(s1, idx)
            return self.mapper.Store(result)
        
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_item': Getitem})
        typeSpec = {"tp_as_sequence": seq}
        self.assertTypeMethodCall(typeSpec, "__getitem__", (idx,), {}, result)
        deallocSeq()


    def testSetitem(self):
        idx = 123
        value = object()
        def Setitem(p1, s1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(s1, idx)
            self.assertEquals(self.mapper.Retrieve(p2), value)
            return self.result
        
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_ass_item': Setitem})
        typeSpec = {"tp_as_sequence": seq}

        self.result = 0
        self.assertTypeMethodCall(typeSpec, "__setitem__", (idx, value,), {}, self.result)

        self.result = -1
        self.assertTypeMethodRaises(typeSpec, "__setitem__", (idx, value,), {}, Exception)

        deallocSeq()


    def testGetslice(self):
        start_ = 123
        stop_ = 456
        result = object()
        def Getslice(p1, s1, s2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(s1, start_)
            self.assertEquals(s2, stop_)
            return self.mapper.Store(result)
        
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_slice': Getslice})
        typeSpec = {"tp_as_sequence": seq}
        self.assertTypeMethodCall(typeSpec, "__getslice__", (start_, stop_), {}, result)
        deallocSeq()


    def testSetslice(self):
        start_ = 123
        stop_ = 456
        value = object()
        def Setslice(p1, s1, s2, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(s1, start_)
            self.assertEquals(s2, stop_)
            self.assertEquals(self.mapper.Retrieve(p2), value)
            return self.result
        
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_ass_slice': Setslice})
        typeSpec = {"tp_as_sequence": seq}

        self.result = 0
        self.assertTypeMethodCall(typeSpec, "__setslice__", (start_, stop_, value,), {}, self.result)

        self.result = -1
        self.assertTypeMethodRaises(typeSpec, "__setslice__", (start_, stop_, value,), {}, Exception)

        deallocSeq()


class MappingMethodsTest(MethodConnectionTestCase):

    def testLength(self):
        result = 0
        def Length(p1):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            return result
        
        mapping, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {'mp_length': Length})
        typeSpec = {"tp_as_mapping": mapping}
        self.assertTypeMethodCall(typeSpec, "__len__", (), {}, result)
        deallocMapping()


    def testGetitem(self):
        key = object()
        result = object()
        def Getitem(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), key)
            return self.mapper.Store(result)
        
        mapping, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {'mp_subscript': Getitem})
        typeSpec = {"tp_as_mapping": mapping}
        self.assertTypeMethodCall(typeSpec, "__getitem__", (key,), {}, result)
        deallocMapping()


    def testSetitem(self):
        key = object()
        value = object()
        def Setitem(p1, p2, p3):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(self.mapper.Retrieve(p2), key)
            self.assertEquals(self.mapper.Retrieve(p3), value)
            return self.result
        
        mapping, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {'mp_ass_subscript': Setitem})
        typeSpec = {"tp_as_mapping": mapping}

        self.result = 0
        self.assertTypeMethodCall(typeSpec, "__setitem__", (key, value,), {}, self.result)

        self.result = -1
        self.assertTypeMethodRaises(typeSpec, "__setitem__", (key, value,), {}, Exception)

        deallocMapping()


class CollisionsTest(TestCase):
    
    @WithMapper
    def testMappingBeatsSequence(self, mapper, addToDeallocs):
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {
            'sq_length': Raise, 'sq_item': Raise, 'sq_ass_item': Raise})
        addToDeallocs(deallocSeq)
        
        mapping, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {
            'mp_length': lambda *_: 123, 
            'mp_subscript': lambda *_: mapper.Store(object()),
            'mp_ass_subscript': lambda *_: 0,
        })
        addToDeallocs(deallocMapping)
        
        typeSpec = {
            'tp_as_sequence': seq,
            'tp_as_mapping': mapping,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToDeallocs(deallocType)
        instance = mapper.Retrieve(typePtr)()
        
        # real tests start here
        len(instance)
        instance[33]
        instance[45] = 6
        # wrong connections would have called Raise
    
    @WithMapper
    def testNumberBeatsSequence(self, mapper, addToDeallocs):
        seq, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_concat': Raise})
        addToDeallocs(deallocSeq)
        
        num, deallocNum = MakeNumSeqMapMethods(PyNumberMethods, {'nb_add': lambda *_: mapper.Store(object())})
        addToDeallocs(deallocNum)
        
        typeSpec = {
            'tp_as_sequence': seq,
            'tp_as_number': num,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToDeallocs(deallocType)
        instance = mapper.Retrieve(typePtr)()
        
        # real tests start here
        instance + object()
        # wrong connections would have called Raise


suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)
