
from tests.utils.runtest import automakesuite, run
    
from tests.utils.cpython import MakeGetSetDef, MakeMethodDef, MakeNumSeqMapMethods, MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

import System
from System import IntPtr, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, HGlobalAllocator, Python25Mapper
from Ironclad.Structs import (
    MemberT, METH, Py_TPFLAGS, PyMemberDef, PyNumberMethods, PyStringObject, 
    PyIntObject, PyObject, PyMappingMethods, PySequenceMethods, PyTypeObject
)
        
        
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


class FieldsTest(TestCase):
    def testFails(self):
        self.fail()
        

class TypeDictTest(TestCase):
    
    @WithMapper
    def testRetrieveAssignsDictTo_tp_dict(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": "klass"})
        addToCleanUp(deallocType)
        
        _type = mapper.Retrieve(typePtr)
        _typeDictPtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict")
        self.assertEquals(mapper.Retrieve(_typeDictPtr), _type.__dict__)


class MethodConnectionTestCase(TestCase):

    @WithMapper
    def assertTypeMethodCalls(self, typeSpec, methodName, args, kwargs, result, mapper, addToCleanUp):
        self.mapper = mapper
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        self.instance = mapper.Retrieve(typePtr)()
        method = getattr(self.instance, methodName)
        self.assertEquals(method(*args, **kwargs), result)


class MethodsTest(MethodConnectionTestCase):

    def testNoArgsMethod(self):
        result = object()
        def NoArgs(p1, p2):
            self.assertEquals(self.mapper.Retrieve(p1), self.instance)
            self.assertEquals(p2, IntPtr.Zero)
            return self.mapper.Store(result)
        
        methodDef, deallocMethod = MakeMethodDef("method", NoArgs, METH.NOARGS)
        typeSpec = {"tp_methods": [methodDef]}
        self.assertTypeMethodCalls(typeSpec, "method", (), {}, result)
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
        self.assertTypeMethodCalls(typeSpec, "method", (arg,), {}, result)
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
        self.assertTypeMethodCalls(typeSpec, "method", args, {}, result)
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
        self.assertTypeMethodCalls(typeSpec, "method", args, kwargs, result)
        deallocMethod()

class GetsetsTest(MethodConnectionTestCase):
    def testFails(self):
        self.fail()

class TypeMethodsTest(MethodConnectionTestCase):
    def testFails(self):
        self.fail()

class NumberMethodsTest(MethodConnectionTestCase):
    def testFails(self):
        self.fail()

class SequenceMethodsTest(MethodConnectionTestCase):
    def testFails(self):
        self.fail()

class MappingMethodsTest(MethodConnectionTestCase):
    def testFails(self):
        self.fail()

class CollisionsTest(MethodConnectionTestCase):
    def testFails(self):
        self.fail()

suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)
