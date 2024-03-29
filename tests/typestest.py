
import operator, types

from functools import reduce

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import Byte, IntPtr, UInt32, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import CannotInterpretException, CPyMarshal, dgt_ptr_ptrptrptr, HGlobalAllocator, PythonMapper
from Ironclad.Structs import *


BUILTIN_TYPES = {
    "PyType_Type": type,
    "PyBaseObject_Type": object,
    "PyBytes_Type": bytes,
    #"PyUnicode_Type": str, # TODO... # https://github.com/IronLanguages/ironclad/issues/13
    "PyList_Type": list,
    "PyDict_Type": dict,
    "PyTuple_Type": tuple,
    "PyLong_Type": int,
    "PyBool_Type": bool,
    "PyFloat_Type": float,
    "PyComplex_Type": complex,
    "PySlice_Type": slice,
    "PyEllipsis_Type": type(Ellipsis),
    "_PyNone_Type": type(None),
    "_PyNotImplemented_Type": type(NotImplemented),
    "PyFunction_Type": types.FunctionType,
    "PyMethod_Type": types.MethodType,
}

TYPE_SUBCLASS_FLAGS = {
    bytes: Py_TPFLAGS.BYTES_SUBCLASS,
    int: Py_TPFLAGS.LONG_SUBCLASS,
    list: Py_TPFLAGS.LIST_SUBCLASS,
    tuple: Py_TPFLAGS.TUPLE_SUBCLASS,
    #str: Py_TPFLAGS.UNICODE_SUBCLASS, # TODO... # https://github.com/IronLanguages/ironclad/issues/13
    dict: Py_TPFLAGS.DICT_SUBCLASS,
# TODO    BaseException: Py_TPFLAGS.BASE_EXC_SUBCLASS, # this is a little tricky
    type: Py_TPFLAGS.TYPE_SUBCLASS,
}
SUBCLASS_FLAGS_MASK = UInt32(reduce(operator.or_, TYPE_SUBCLASS_FLAGS.values()))

class Types_Test(TestCase):
    
    @WithMapper
    def testTypeMappings(self, mapper, _):
        for (k, v) in BUILTIN_TYPES.items():
            typePtr = getattr(mapper, k)
            self.assertEqual(CPyMarshal.ReadCStringField(typePtr, PyTypeObject, 'tp_name'), v.__name__)
            
            self.assertEqual(mapper.Retrieve(typePtr), v, "failed to map " + k)

            self.assertEqual(mapper.RefCount(typePtr), 1, "failed to add reference to " + k)
            
            mapper.PyType_Ready(typePtr)
            self.assertNotEqual(CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_basicsize"), 0)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            if k == "PyBaseObject_Type":
                self.assertEqual(basePtr, IntPtr.Zero)
            elif k == "PyBool_Type":
                self.assertEqual(basePtr, mapper.PyLong_Type)
            else:
                self.assertEqual(basePtr, mapper.PyBaseObject_Type)

    def assertTypeSubclassFlag(self, mapper, t, f):
        typeFlags = CPyMarshal.ReadIntField(mapper.Store(t), PyTypeObject, "tp_flags")
        self.assertEqual(typeFlags & UInt32(f), UInt32(f), "did not have appropriate flag")
        
    def assertNoTypeSubclassFlag(self, mapper, t):
        typeFlags = CPyMarshal.ReadIntField(mapper.Store(t), PyTypeObject, "tp_flags")
        self.assertEqual(typeFlags & SUBCLASS_FLAGS_MASK, 0, "had bad flag")
        

    @WithMapper
    def testTypeSubclassFlags(self, mapper, _):
        for (t, f) in TYPE_SUBCLASS_FLAGS.items():
            self.assertTypeSubclassFlag(mapper, t, f)
            st = type('%s_sub' % t, (t,), {})
            self.assertTypeSubclassFlag(mapper, st, f)
        
        self.assertNoTypeSubclassFlag(mapper, object)
        self.assertNoTypeSubclassFlag(mapper, type("obj_sub", (object,), {}))
        

    @WithMapper
    def testPyType_IsSubtype(self, mapper, _):
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, IntPtr.Zero))
        self.assertFalse(mapper.PyType_IsSubtype(IntPtr.Zero, mapper.PyType_Type))
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyType_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyBytes_Type, mapper.PyBytes_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyBaseObject_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyList_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyType_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyBaseObject_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyType_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyList_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBytes_Type, mapper.PyType_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyBytes_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.Store(b"foo"), mapper.PyBytes_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.Store("foo"), mapper.PyUnicode_Type))
        
        class T(type): pass
        Tptr = mapper.Store(T)
        self.assertTrue(mapper.PyType_IsSubtype(Tptr, mapper.PyType_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, Tptr))
        
        class B(bytes): pass
        Bptr = mapper.Store(B)
        self.assertTrue(mapper.PyType_IsSubtype(Bptr, mapper.PyBytes_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBytes_Type, Bptr))
        self.assertFalse(mapper.PyType_IsSubtype(Bptr, mapper.PyType_Type))

        raise NotImplementedError # https://github.com/IronLanguages/ironclad/issues/13
        class S(str): pass
        Sptr = mapper.Store(S)
        self.assertTrue(mapper.PyType_IsSubtype(Sptr, mapper.PyUnicode_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyUnicode_Type, Sptr))
        self.assertFalse(mapper.PyType_IsSubtype(Sptr, mapper.PyType_Type))


    @WithMapper
    def testPyType_IsSubtype_NullPtrs(self, mapper, CallLater):
        type_size = Marshal.SizeOf(PyTypeObject())
        ptr = Marshal.AllocHGlobal(type_size)
        CallLater(lambda: Marshal.FreeHGlobal(ptr))
        CPyMarshal.Zero(ptr, type_size)
        
        self.assertTrue(mapper.PyType_IsSubtype(ptr, mapper.PyBaseObject_Type))
        self.assertTrue(mapper.PyType_IsSubtype(ptr, ptr))


    @WithMapper
    def testPyType_Ready(self, mapper, addToCleanUp):
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(typePtr, Marshal.SizeOf(PyTypeObject()))
        addToCleanUp(lambda: Marshal.FreeHGlobal(typePtr))

        self.assertEqual(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), mapper.PyType_Type, "failed to fill in missing ob_type")
        self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to fill in missing tp_base")
        tp_dict = mapper.Retrieve(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict"))
        self.assertEqual(mapper.Retrieve(typePtr).__dict__, tp_dict)

        typeFlags = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_flags")
        self.assertEqual(typeFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready type")
        
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "ob_type", IntPtr.Zero)
        self.assertEqual(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), IntPtr.Zero, "unexpectedly and unnecessarily rereadied type")


    @WithMapper
    def testReadyBuiltinTypes(self, mapper, _):
        mapper.ReadyBuiltinTypes()
        
        for _type in BUILTIN_TYPES:
            typePtr = getattr(mapper, _type)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            
            if typePtr != mapper.PySeqIter_Type:
                # PySeqIter_Type is suprrisingly tedious to turn into a proper PythonType in C#
                tp_dict = mapper.Retrieve(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict"))
                self.assertEqual(mapper.Retrieve(typePtr).__dict__, tp_dict)

            if typePtr not in (mapper.PyBaseObject_Type, mapper.PyBool_Type):
                self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
            if typePtr == mapper.PyBool_Type:
                self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyLong_Type)
            typeTypePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type")
            if typePtr != mapper.PyType_Type:
                self.assertEqual(typeTypePtr, mapper.PyType_Type)


    @WithMapper
    def testNotAutoActualisableTypes(self, mapper, _):
        safeTypes = "PyBytes_Type PyList_Type PyTuple_Type PyType_Type PyFloat_Type".split()
        discoveryModes = ("IncRef", "Retrieve", "DecRef", "RefCount")
        for _type in (s for s in BUILTIN_TYPES if s not in safeTypes):
            for mode in discoveryModes:
                objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject()))
                CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 2)
                CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", getattr(mapper, _type))
                self.assertRaisesClr(CannotInterpretException, getattr(mapper, mode), objPtr)
                Marshal.FreeHGlobal(objPtr)
    
    
    @WithMapper
    def testNumberMethods(self, mapper, _):
        numberTypes = ("PyLong_Type", "PyFloat_Type", "PyComplex_Type")
        implementedFields = {
            "nb_int": mapper.GetFuncPtr("PyNumber_Long"),
            "nb_float": mapper.GetFuncPtr("PyNumber_Float"),
            "nb_multiply": mapper.GetFuncPtr("PyNumber_Multiply")
        }
        
        for _type in numberTypes:
            typePtr = getattr(mapper, _type)
            nmPtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_as_number")
            self.assertNotEqual(nmPtr, IntPtr.Zero)
            for field in implementedFields:
                fieldPtr = CPyMarshal.ReadPtrField(nmPtr, PyNumberMethods, field)
                self.assertNotEqual(fieldPtr, IntPtr.Zero)
                self.assertEqual(fieldPtr, implementedFields[field])
            
            flags = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_flags")
            hasIndex = bool(flags & int(Py_TPFLAGS.HAVE_INDEX))
            if (not _type in ("PyFloat_Type", "PyComplex_Type")):
                self.assertEqual(hasIndex, True, _type)
                fieldPtr = CPyMarshal.ReadPtrField(nmPtr, PyNumberMethods, "nb_index")
                self.assertNotEqual(fieldPtr, IntPtr.Zero)
                self.assertEqual(fieldPtr, mapper.GetFuncPtr("PyNumber_Index"))
            else:
                self.assertEqual(hasIndex, False)
                

    def assertMaps(self, mapper, func, ptr, refcnt):
        func(ptr)
        obj = mapper.Retrieve(ptr)
        ref = WeakReference(obj)
        self.assertEqual(mapper.Store(obj), ptr)
        self.assertEqual(mapper.RefCount(ptr), refcnt)
        
        while mapper.RefCount(ptr) > 2:
            mapper.DecRef(ptr)
        del obj
        gcwait()
        self.assertEqual(ref.IsAlive, True)
        
        obj = ref.Target
        mapper.DecRef(ptr)
        del obj
        gcwait()
        self.assertEqual(ref.IsAlive, False)
    
    
    def testExtensionTypesAutoActualisable(self):
        discoveryModes = {
            "IncRef": lambda f, o: self.assertMaps(mapper, f, o, 5), 
            "Retrieve": lambda f, o: self.assertMaps(mapper, f, o, 4), 
            "DecRef": lambda f, o: self.assertMaps(mapper, f, o, 3), 
            "RefCount": lambda f, o: self.assertMaps(mapper, f, o, 4),
        }
        
        allocator = HGlobalAllocator()
        mapper = PythonMapper(allocator)
        deallocTypes = CreateTypes(mapper)
        # delay deallocs to avoid types with the same addresses causing confusion
        userTypeDeallocs = []
        try:
            for (mode, TestFunc) in discoveryModes.items():
                typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": mode + "Class"})
                userTypeDeallocs.append(deallocType)
                objPtr = allocator.Alloc(IntPtr(Marshal.SizeOf(PyObject())))
                CPyMarshal.WritePtrField(objPtr, PyObject, "ob_refcnt", 2)
                CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)
                
                discoveryFunc = getattr(mapper, mode)
                TestFunc(discoveryFunc, objPtr)
        finally:
            mapper.Dispose()
            for deallocFunc in userTypeDeallocs:
                deallocFunc()
            deallocTypes()


    @WithMapper
    def testStoreUnknownType(self, mapper, _):
        class C(object):
            __name__ = "cantankerous.cochineal"
        cPtr = mapper.Store(C)
        self.assertEqual(CPyMarshal.ReadIntField(cPtr, PyTypeObject, "ob_refcnt"), 2, "seems easiest to 'leak' types, and ensure they live forever")
        self.assertEqual(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "ob_type"), mapper.PyType_Type)
        self.assertEqual(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        self.assertEqual(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_bases"), IntPtr.Zero)
        self.assertEqual(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_as_number"), IntPtr.Zero)

        self.assertEqual(CPyMarshal.ReadCStringField(cPtr, PyTypeObject, "tp_name"), "cantankerous.cochineal")

        baseFlags = CPyMarshal.ReadIntField(cPtr, PyTypeObject, "tp_flags")
        self.assertEqual(baseFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready newly-stored type")
        
        instancePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject()))
        CPyMarshal.WritePtrField(instancePtr, PyObject, "ob_type", cPtr)
        CPyMarshal.WriteIntField(instancePtr, PyObject, "ob_refcnt", 2)
        
        instance = mapper.Retrieve(instancePtr)
        self.assertEqual(isinstance(instance, C), True)
        self.assertEqual(mapper.Store(instance), instancePtr)


    @WithMapper
    def testStoreUnknownTypeWithBases(self, mapper, _):
        class C(object): pass
        class D(object): pass
        class E(C, D): pass
        
        ePtr = mapper.Store(E)
        basesPtr = CPyMarshal.ReadPtrField(ePtr, PyTypeObject, "tp_bases")
        self.assertEqual(mapper.Retrieve(basesPtr), (C, D))


    def assertSizes(self, ptr, basic, item=0):
        self.assertEqual(CPyMarshal.ReadIntField(ptr, PyTypeObject, "tp_basicsize"), basic)
        self.assertEqual(CPyMarshal.ReadIntField(ptr, PyTypeObject, "tp_itemsize"), item)

    @WithMapper
    def testSizes(self, mapper, _):
        self.assertSizes(mapper.PyBaseObject_Type, Marshal.SizeOf(PyObject()))
        self.assertSizes(mapper.PyType_Type, Marshal.SizeOf(PyHeapTypeObject()))
        self.assertSizes(mapper.PyTuple_Type, Marshal.SizeOf(PyTupleObject()), Marshal.SizeOf(IntPtr())) # bigger than necessary
        self.assertSizes(mapper.PyBytes_Type, Marshal.SizeOf(PyBytesObject()) - 1, Marshal.SizeOf(Byte()))
        self.assertSizes(mapper.PyList_Type, Marshal.SizeOf(PyListObject()))
        self.assertSizes(mapper.PySlice_Type, Marshal.SizeOf(PySliceObject()))
        self.assertSizes(mapper.PyMethod_Type, Marshal.SizeOf(PyMethodObject()))
        self.assertSizes(mapper.PyLong_Type, Marshal.SizeOf(PyLongObject()))
        self.assertSizes(mapper.PyFloat_Type, Marshal.SizeOf(PyFloatObject()))
        self.assertSizes(mapper.PyComplex_Type, Marshal.SizeOf(PyComplexObject()))


class PyType_GenericAlloc_Test(TestCase):

    def testNoItems(self):
        allocs = []
        with PythonMapper(GetAllocatingTestAllocator(allocs, [])) as mapper:
            deallocTypes = CreateTypes(mapper)
            typeSpec = {
                "tp_basicsize": 32,
                "tp_itemsize": 64,
            }
            typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
            
            del allocs[:]
            result = mapper.PyType_GenericAlloc(typePtr, IntPtr(0))
            self.assertEqual(allocs, [(result, 32)], "allocated wrong")

            refcount = CPyMarshal.ReadIntField(result, PyObject, "ob_refcnt")
            self.assertEqual(refcount, 1, "bad initialisation")

            instanceType = CPyMarshal.ReadPtrField(result, PyObject, "ob_type")
            self.assertEqual(instanceType, typePtr, "bad type ptr")
            
            headerSize = Marshal.SizeOf(PyObject())
            zerosPtr = OffsetPtr(result, headerSize)
            for i in range(32 - headerSize):
                self.assertEqual(CPyMarshal.ReadByte(zerosPtr), 0, "not zeroed")
                zerosPtr = OffsetPtr(zerosPtr, 1)

        deallocTypes()
        deallocType()


    def testSomeItems(self):
        allocs = []
        with PythonMapper(GetAllocatingTestAllocator(allocs, [])) as mapper:
            deallocTypes = CreateTypes(mapper)
            typeSpec = {
                "tp_basicsize": 32,
                "tp_itemsize": 64,
            }
            typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
            
            del allocs[:]
            result = mapper.PyType_GenericAlloc(typePtr, IntPtr(3))
            self.assertEqual(allocs, [(result, 224)], "allocated wrong")

            refcount = CPyMarshal.ReadIntField(result, PyObject, "ob_refcnt")
            self.assertEqual(refcount, 1, "bad initialisation")

            instanceType = CPyMarshal.ReadPtrField(result, PyObject, "ob_type")
            self.assertEqual(instanceType, typePtr, "bad type ptr")

            size = CPyMarshal.ReadIntField(result, PyVarObject, "ob_size")
            self.assertEqual(size, 3, "bad ob_size")
            
            headerSize = Marshal.SizeOf(PyVarObject())
            zerosPtr = OffsetPtr(result, headerSize)
            for i in range(224 - headerSize):
                self.assertEqual(CPyMarshal.ReadByte(zerosPtr), 0, "not zeroed")
                zerosPtr = OffsetPtr(zerosPtr, 1)

        deallocTypes()
        deallocType()


class PyType_GenericNew_Test(TestCase):

    @WithMapper
    def testCallsTypeAllocFunction(self, mapper, addToCleanUp):
        calls = []
        def Alloc(typePtr, nItems):
            calls.append((typePtr, nItems))
            return IntPtr(999)

        typeSpec = {
            "tp_alloc": Alloc,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        result = mapper.PyType_GenericNew(typePtr, IntPtr(222), IntPtr(333))
        self.assertEqual(result, IntPtr(999), "did not use type's tp_alloc function")
        self.assertEqual(calls, [(typePtr, 0)], "passed wrong args")


class IC_PyType_New_Test(TestCase):
    
    @WithMapper
    def testIC_PyType_Type_tp_new(self, mapper, _):
        IC_PyType_New = CPyMarshal.ReadFunctionPtrField(mapper.PyType_Type, PyTypeObject, "tp_new", dgt_ptr_ptrptrptr)
        typeArgs = ("hello", (float,), {'cheese': 27})
        # we have only ever seen this called from *within* a metatype's tp_new;
        # therefore, we claim that its intent is to contruct a vanilla type, and
        # that any metaclass-notification stuff should be handled by the caller.
        # therefore, we can ignore the first arg and always pretend it's PyType_Type.
        # handwave handwave; hey, look, a three-headed monkey!
        typePtr = IC_PyType_New(IntPtr.Zero, mapper.Store(typeArgs), IntPtr.Zero)
        
        type_ = mapper.Retrieve(typePtr)
        self.assertEqual(type_.__name__, "hello")
        self.assertEqual(issubclass(type_, float), True)
        self.assertEqual(type_.cheese, 27)
        


INHERIT_FIELDS = (
    "tp_alloc",
    "tp_new",
    "tp_dealloc",
    "tp_free",
    "tp_doc",
    "tp_call",
    "tp_as_number",
    "tp_as_sequence",
    "tp_as_mapping",
    "tp_as_buffer",
    "tp_basicsize",
    "tp_itemsize",
)
DONT_INHERIT_FIELDS = (
    "tp_init",
    "tp_repr",
    "tp_str",
)
NO_VALUE = IntPtr.Zero
SOME_VALUE = IntPtr(12345)

class PyType_Ready_InheritTest(TestCase):
    
    @WithMapper
    def testBaseTypeMissing(self, mapper, CallLater):
        mapper.PyType_Ready(mapper.PyBaseObject_Type)
        self.assertEqual(CPyMarshal.ReadPtrField(mapper.PyBaseObject_Type, PyTypeObject, "tp_base"), IntPtr.Zero)
        
        typePtr, deallocType = MakeTypePtr(mapper, {})
        CallLater(deallocType)
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_base", NO_VALUE)
        mapper.PyType_Ready(typePtr)
        self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        

    @WithMapper
    def testFields(self, mapper, CallLater):
        basePtr, deallocBase = MakeTypePtr(mapper, {})
        typePtr, deallocType = MakeTypePtr(mapper, {})
        CallLater(deallocBase)
        CallLater(deallocType)
        
        # The purpose of this rigmarole is to enable me to use SOME_VALUE
        # for every field, rather than creating 'proper' values for every 
        # field -- once I've Retrieved the types, I won't actualise them 
        # again, so I can put any old non-zero nonsense in any field to 
        # check that it gets inherited (or not)
        mapper.Retrieve(basePtr)
        mapper.Retrieve(typePtr)
        CPyMarshal.WriteIntField(typePtr, PyTypeObject, "tp_flags", 0)
        # end rigmarole
        
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_base", basePtr)
        for field in INHERIT_FIELDS + DONT_INHERIT_FIELDS:
            CPyMarshal.WritePtrField(typePtr, PyTypeObject, field, NO_VALUE)
            CPyMarshal.WritePtrField(basePtr, PyTypeObject, field, SOME_VALUE)
        
        mapper.PyType_Ready(typePtr)
        for field in INHERIT_FIELDS:
            self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, field), SOME_VALUE)
        for field in DONT_INHERIT_FIELDS:
            self.assertEqual(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, field), NO_VALUE)
        


suite = makesuite(
    Types_Test,
    PyType_GenericNew_Test,
    IC_PyType_New_Test,
    PyType_GenericAlloc_Test,
    PyType_Ready_InheritTest,
)

if __name__ == '__main__':
    run(suite)
