
import types

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import Byte, IntPtr, UInt32, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import CannotInterpretException, CPyMarshal, dgt_ptr_ptrptrptr, HGlobalAllocator, Python25Mapper, OpaquePyCell
from Ironclad.Structs import *

class ItemEnumeratorThing(object):
    def __getitem__(self):
        pass
ItemEnumeratorType = type(iter(ItemEnumeratorThing()))

BUILTIN_TYPES = {
    "PyType_Type": type,
    "PyBaseObject_Type": object,
    "PyString_Type": str,
    "PyList_Type": list,
    "PyDict_Type": dict,
    "PyTuple_Type": tuple,
    "PyFile_Type": file,
    "PyLong_Type": long,
    "PyInt_Type": int,
    "PyBool_Type": bool,
    "PyFloat_Type": float,
    "PyComplex_Type": complex,
    "PySlice_Type": slice,
    "PyEllipsis_Type": types.EllipsisType,
    "PyNone_Type": types.NoneType,
    "PyNotImplemented_Type": types.NotImplementedType,
    "PySeqIter_Type": ItemEnumeratorType,
    "PyCell_Type": OpaquePyCell,
    "PyMethod_Type": types.MethodType,
    "PyClass_Type": types.ClassType,
    "PyInstance_Type": types.InstanceType,
}

class Types_Test(TestCase):
    
    @WithMapper
    def testTypeMappings(self, mapper, _):
        for (k, v) in BUILTIN_TYPES.items():
            typePtr = getattr(mapper, k)
            
            if typePtr == mapper.PyFile_Type:
                self.assertNotEquals(mapper.Retrieve(typePtr), v, "failed to map PyFile_Type to something-that-isn't file")
            else:
                self.assertEquals(mapper.Retrieve(typePtr), v, "failed to map " + k)
            
            if typePtr in (mapper.PyType_Type, mapper.PyBaseObject_Type):
                # surprising refcount because of the unmanaged PyFile malarkey
                self.assertEquals(mapper.RefCount(typePtr), 2, "failed to add reference to " + k)
            else:
                self.assertEquals(mapper.RefCount(typePtr), 1, "failed to add reference to " + k)
            
            mapper.PyType_Ready(typePtr)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            if k == "PyBaseObject_Type":
                self.assertEquals(basePtr, IntPtr.Zero)
            elif k == "PyBool_Type":
                self.assertEquals(basePtr, mapper.PyInt_Type)
            else:
                self.assertEquals(basePtr, mapper.PyBaseObject_Type)


    @WithMapper
    def testPyType_IsSubtype(self, mapper, _):
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, IntPtr.Zero))
        self.assertFalse(mapper.PyType_IsSubtype(IntPtr.Zero, mapper.PyType_Type))
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyType_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyString_Type, mapper.PyString_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyBaseObject_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyList_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyType_Type))
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyBaseObject_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyType_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyList_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyString_Type, mapper.PyType_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyString_Type))
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.Store("foo"), mapper.PyString_Type))
        
        class T(type): pass
        Tptr = mapper.Store(T)
        self.assertTrue(mapper.PyType_IsSubtype(Tptr, mapper.PyType_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, Tptr))
        
        class S(str): pass
        Sptr = mapper.Store(S)
        self.assertTrue(mapper.PyType_IsSubtype(Sptr, mapper.PyString_Type))
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyString_Type, Sptr))
        self.assertFalse(mapper.PyType_IsSubtype(Sptr, mapper.PyType_Type))


    @WithMapper
    def testPyType_IsSubtype_NullPtrs(self, mapper, CallLater):
        type_size = Marshal.SizeOf(PyTypeObject)
        ptr = Marshal.AllocHGlobal(type_size)
        CallLater(lambda: Marshal.FreeHGlobal(ptr))
        CPyMarshal.Zero(ptr, type_size)
        
        self.assertTrue(mapper.PyType_IsSubtype(ptr, mapper.PyBaseObject_Type))
        self.assertTrue(mapper.PyType_IsSubtype(ptr, ptr))


    @WithMapper
    def testPyType_Ready(self, mapper, addToCleanUp):
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(typePtr, Marshal.SizeOf(PyTypeObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(typePtr))

        self.assertEquals(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), mapper.PyType_Type, "failed to fill in missing ob_type")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to fill in missing tp_base")
        tp_dict = mapper.Retrieve(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict"))
        self.assertEquals(mapper.Retrieve(typePtr).__dict__, tp_dict)

        typeFlags = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_flags")
        self.assertEquals(typeFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready type")
        self.assertEquals(typeFlags & UInt32(Py_TPFLAGS.HAVE_CLASS), UInt32(Py_TPFLAGS.HAVE_CLASS), 
                          "we always set this flag, for no better reason than 'it makes ctypes kinda work'")
        
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "ob_type", IntPtr.Zero)
        self.assertEquals(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), IntPtr.Zero, "unexpectedly and unnecessarily rereadied type")        


    @WithMapper
    def testReadyBuiltinTypes(self, mapper, _):
        mapper.ReadyBuiltinTypes()
        
        for _type in BUILTIN_TYPES:
            typePtr = getattr(mapper, _type)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            
            if typePtr not in (mapper.PySeqIter_Type, mapper.PyCell_Type):
                # PySeqIter_Type is suprrisingly tedious to turn into a proper PythonType in C#
                # OpaquePyCellObject probably shouldn't even exist, and I don't expect it to ever be used.
                tp_dict = mapper.Retrieve(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict"))
                self.assertEquals(mapper.Retrieve(typePtr).__dict__, tp_dict)

            if typePtr not in (mapper.PyBaseObject_Type, mapper.PyBool_Type):
                self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
            if typePtr == mapper.PyBool_Type:
                self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyInt_Type)
            typeTypePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type")
            if typePtr != mapper.PyType_Type:
                self.assertEquals(typeTypePtr, mapper.PyType_Type)


    @WithMapper
    def testNotAutoActualisableTypes(self, mapper, _):
        safeTypes = ("PyString_Type", "PyList_Type", "PyTuple_Type", "PyType_Type", "PyFile_Type")
        discoveryModes = ("IncRef", "Retrieve", "DecRef", "RefCount")
        for _type in filter(lambda s: s not in safeTypes, BUILTIN_TYPES):
            for mode in discoveryModes:
                objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
                CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 2)
                CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", getattr(mapper, _type))
                self.assertRaises(CannotInterpretException, getattr(mapper, mode), objPtr)
                Marshal.FreeHGlobal(objPtr)
    
    
    @WithMapper
    def testNumberMethods(self, mapper, _):
        numberTypes = ("PyInt_Type", "PyLong_Type", "PyFloat_Type", "PyComplex_Type")
        implementedFields = {
            "nb_int": mapper.GetAddress("PyNumber_Int"),
            "nb_long": mapper.GetAddress("PyNumber_Long"),
            "nb_float": mapper.GetAddress("PyNumber_Float"),
            "nb_multiply": mapper.GetAddress("PyNumber_Multiply")
        }
        
        for _type in numberTypes:
            typePtr = getattr(mapper, _type)
            nmPtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_as_number")
            self.assertNotEquals(nmPtr, IntPtr.Zero)
            for field in implementedFields:
                fieldPtr = CPyMarshal.ReadPtrField(nmPtr, PyNumberMethods, field)
                self.assertNotEquals(fieldPtr, IntPtr.Zero)
                self.assertEquals(fieldPtr, implementedFields[field])
            
            flags = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_flags")
            hasIndex = bool(flags & int(Py_TPFLAGS.HAVE_INDEX))
            if (not _type in ("PyFloat_Type", "PyComplex_Type")):
                self.assertEquals(hasIndex, True, _type)
                fieldPtr = CPyMarshal.ReadPtrField(nmPtr, PyNumberMethods, "nb_index")
                self.assertNotEquals(fieldPtr, IntPtr.Zero)
                self.assertEquals(fieldPtr, mapper.GetAddress("PyNumber_Index"))
            else:
                self.assertEquals(hasIndex, False)
                

    def assertMaps(self, mapper, func, ptr, refcnt):
        func(ptr)
        obj = mapper.Retrieve(ptr)
        ref = WeakReference(obj)
        self.assertEquals(mapper.Store(obj), ptr)
        self.assertEquals(mapper.RefCount(ptr), refcnt)
        
        while mapper.RefCount(ptr) > 2:
            mapper.DecRef(ptr)
        del obj
        gcwait()
        self.assertEquals(ref.IsAlive, True)
        
        obj = ref.Target
        mapper.DecRef(ptr)
        del obj
        gcwait()
        self.assertEquals(ref.IsAlive, False)
    
    
    def testExtensionTypesAutoActualisable(self):
        discoveryModes = {
            "IncRef": lambda f, o: self.assertMaps(mapper, f, o, 5), 
            "Retrieve": lambda f, o: self.assertMaps(mapper, f, o, 4), 
            "DecRef": lambda f, o: self.assertMaps(mapper, f, o, 3), 
            "RefCount": lambda f, o: self.assertMaps(mapper, f, o, 4),
        }
        
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        # delay deallocs to avoid types with the same addresses causing confusion
        userTypeDeallocs = []
        for (mode, TestFunc) in discoveryModes.items():
            typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": mode + "Class"})
            userTypeDeallocs.append(deallocType)
            objPtr = allocator.Alloc(Marshal.SizeOf(PyObject))
            CPyMarshal.WriteIntField(objPtr, PyObject, "ob_refcnt", 2)
            CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", typePtr)
            
            discoveryFunc = getattr(mapper, mode)
            TestFunc(discoveryFunc, objPtr)
                
        mapper.Dispose()
        for deallocFunc in userTypeDeallocs:
            deallocFunc()
        deallocTypes()


    @WithMapper
    def testStoreUnknownType(self, mapper, _):
        class C(object):
            __name__ = "cantankerous.cochineal"
        cPtr = mapper.Store(C)
        self.assertEquals(CPyMarshal.ReadIntField(cPtr, PyTypeObject, "ob_refcnt"), 2, "seems easiest to 'leak' types, and ensure they live forever")
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "ob_type"), mapper.PyType_Type)
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_bases"), IntPtr.Zero)
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_as_number"), IntPtr.Zero)

        namePtr = CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_name")
        self.assertEquals(mapper.Retrieve(namePtr), "cantankerous.cochineal")

        baseFlags = CPyMarshal.ReadIntField(cPtr, PyTypeObject, "tp_flags")
        self.assertEquals(baseFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready newly-stored type")
        
        instancePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WritePtrField(instancePtr, PyObject, "ob_type", cPtr)
        CPyMarshal.WriteIntField(instancePtr, PyObject, "ob_refcnt", 2)
        
        instance = mapper.Retrieve(instancePtr)
        self.assertEquals(isinstance(instance, C), True)
        self.assertEquals(mapper.Store(instance), instancePtr)


    @WithMapper
    def testStoreUnknownTypeWithBases(self, mapper, _):
        class C(object): pass
        class D(object): pass
        class E(C, D): pass
        
        ePtr = mapper.Store(E)
        basesPtr = CPyMarshal.ReadPtrField(ePtr, PyTypeObject, "tp_bases")
        self.assertEquals(mapper.Retrieve(basesPtr), (C, D))


    def assertSizes(self, ptr, basic, item=0):
        self.assertEquals(CPyMarshal.ReadIntField(ptr, PyTypeObject, "tp_basicsize"), basic)
        self.assertEquals(CPyMarshal.ReadIntField(ptr, PyTypeObject, "tp_itemsize"), item)

    @WithMapper
    def testSizes(self, mapper, _):
        self.assertSizes(mapper.PyBaseObject_Type, Marshal.SizeOf(PyObject))
        self.assertSizes(mapper.PyType_Type, Marshal.SizeOf(PyTypeObject))
        self.assertSizes(mapper.PyTuple_Type, Marshal.SizeOf(PyTupleObject), Marshal.SizeOf(IntPtr)) # bigger than necessary
        self.assertSizes(mapper.PyString_Type, Marshal.SizeOf(PyStringObject) - 1, Marshal.SizeOf(Byte))
        self.assertSizes(mapper.PyList_Type, Marshal.SizeOf(PyListObject))
        self.assertSizes(mapper.PySlice_Type, Marshal.SizeOf(PySliceObject))
        self.assertSizes(mapper.PyMethod_Type, Marshal.SizeOf(PyMethodObject))
        self.assertSizes(mapper.PyInt_Type, Marshal.SizeOf(PyIntObject))
        self.assertSizes(mapper.PyFloat_Type, Marshal.SizeOf(PyFloatObject))
        self.assertSizes(mapper.PyComplex_Type, Marshal.SizeOf(PyComplexObject))
        self.assertSizes(mapper.PyClass_Type, Marshal.SizeOf(PyClassObject))
        self.assertSizes(mapper.PyInstance_Type, Marshal.SizeOf(PyInstanceObject))


class OldStyle_Test(TestCase):
        
    @WithMapper
    def testPyClass_New(self, mapper, _):
        namePtr = mapper.Store('klass')
        dictPtr = mapper.Store({'wurble': 'burble'})
        basesPtr = mapper.Store(())
        
        klassPtr = mapper.PyClass_New(basesPtr, dictPtr, namePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(klassPtr, PyObject, "ob_type"), mapper.PyClass_Type)
        klass = mapper.Retrieve(klassPtr)
        
        self.assertEquals(klass.__name__, 'klass')
        self.assertEquals(klass.wurble, 'burble')
        self.assertEquals(klass.__bases__, ())
    
    
    @WithMapper
    def testPyClass_New_NullBases(self, mapper, _):
        namePtr = mapper.Store('klass')
        dictPtr = mapper.Store({'wurble': 'burble'})
        
        klassPtr = mapper.PyClass_New(IntPtr.Zero, dictPtr, namePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(klassPtr, PyObject, "ob_type"), mapper.PyClass_Type)
        klass = mapper.Retrieve(klassPtr)
        
        self.assertEquals(klass.__name__, 'klass')
        self.assertEquals(klass.wurble, 'burble')
        self.assertEquals(klass.__bases__, ())

    
    @WithMapper
    def testStoreOldStyle(self, mapper, _):
        class O():
            pass
        OPtr = mapper.Store(O)
        self.assertEquals(CPyMarshal.ReadIntField(OPtr, PyObject, "ob_refcnt"), 2) # again, leak classes deliberately
        self.assertEquals(CPyMarshal.ReadPtrField(OPtr, PyObject, "ob_type"), mapper.PyClass_Type)
        
        self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtrField(OPtr, PyClassObject, "cl_bases")), ())
        self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtrField(OPtr, PyClassObject, "cl_name")), "O")
        self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtrField(OPtr, PyClassObject, "cl_dict")) is O.__dict__, True)
        
        self.assertEquals(CPyMarshal.ReadPtrField(OPtr, PyClassObject, "cl_getattr"), IntPtr.Zero)
        self.assertEquals(CPyMarshal.ReadPtrField(OPtr, PyClassObject, "cl_setattr"), IntPtr.Zero)
        self.assertEquals(CPyMarshal.ReadPtrField(OPtr, PyClassObject, "cl_delattr"), IntPtr.Zero)
        
        o = O()
        oPtr = mapper.Store(o)
        self.assertEquals(CPyMarshal.ReadIntField(oPtr, PyObject, "ob_refcnt"), 1)
        self.assertEquals(CPyMarshal.ReadPtrField(oPtr, PyObject, "ob_type"), mapper.PyInstance_Type)
        
        self.assertEquals(CPyMarshal.ReadPtrField(oPtr, PyInstanceObject, "in_class"), OPtr)
        self.assertEquals(mapper.Retrieve(CPyMarshal.ReadPtrField(oPtr, PyInstanceObject, "in_dict")) is o.__dict__, True)
        self.assertEquals(CPyMarshal.ReadPtrField(oPtr, PyInstanceObject, "in_weakreflist"), IntPtr.Zero)
    
    
    @WithMapper
    def testDestroyOldInstance(self, mapper, _):
        # don't care about destroying OldClasses: leaked intentionally
        class O(): pass
        o = O()
        oPtr = mapper.Store(o)
        
        dictPtr = CPyMarshal.ReadPtrField(oPtr, PyInstanceObject, 'in_dict')
        mapper.IncRef(dictPtr)
        refcnt = mapper.RefCount(dictPtr)
        
        mapper.DecRef(oPtr)
        self.assertEquals(mapper.RefCount(dictPtr), refcnt - 1)



class PyType_GenericAlloc_Test(TestCase):

    def testNoItems(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        typeSpec = {
            "tp_basicsize": 32,
            "tp_itemsize": 64,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        del allocs[:]
        result = mapper.PyType_GenericAlloc(typePtr, 0)
        self.assertEquals(allocs, [(result, 32)], "allocated wrong")

        refcount = CPyMarshal.ReadIntField(result, PyObject, "ob_refcnt")
        self.assertEquals(refcount, 1, "bad initialisation")

        instanceType = CPyMarshal.ReadPtrField(result, PyObject, "ob_type")
        self.assertEquals(instanceType, typePtr, "bad type ptr")
        
        headerSize = Marshal.SizeOf(PyObject)
        zerosPtr = OffsetPtr(result, headerSize)
        for i in range(32 - headerSize):
            self.assertEquals(CPyMarshal.ReadByte(zerosPtr), 0, "not zeroed")
            zerosPtr = OffsetPtr(zerosPtr, 1)
 
        mapper.Dispose()
        deallocTypes()
        deallocType()


    def testSomeItems(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        typeSpec = {
            "tp_basicsize": 32,
            "tp_itemsize": 64,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        del allocs[:]
        result = mapper.PyType_GenericAlloc(typePtr, 3)
        self.assertEquals(allocs, [(result, 224)], "allocated wrong")

        refcount = CPyMarshal.ReadIntField(result, PyObject, "ob_refcnt")
        self.assertEquals(refcount, 1, "bad initialisation")

        instanceType = CPyMarshal.ReadPtrField(result, PyObject, "ob_type")
        self.assertEquals(instanceType, typePtr, "bad type ptr")

        size = CPyMarshal.ReadIntField(result, PyVarObject, "ob_size")
        self.assertEquals(size, 3, "bad ob_size")
        
        headerSize = Marshal.SizeOf(PyVarObject)
        zerosPtr = OffsetPtr(result, headerSize)
        for i in range(224 - headerSize):
            self.assertEquals(CPyMarshal.ReadByte(zerosPtr), 0, "not zeroed")
            zerosPtr = OffsetPtr(zerosPtr, 1)
 
        mapper.Dispose()
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
        self.assertEquals(result, IntPtr(999), "did not use type's tp_alloc function")
        self.assertEquals(calls, [(typePtr, 0)], "passed wrong args")


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
        self.assertEquals(type_.__name__, "hello")
        self.assertEquals(issubclass(type_, float), True)
        self.assertEquals(type_.cheese, 27)
        


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
        self.assertEquals(CPyMarshal.ReadPtrField(mapper.PyBaseObject_Type, PyTypeObject, "tp_base"), IntPtr.Zero)
        
        typePtr, deallocType = MakeTypePtr(mapper, {})
        CallLater(deallocType)
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_base", NO_VALUE)
        mapper.PyType_Ready(typePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        

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
        CPyMarshal.WriteIntField(typePtr, PyTypeObject, "tp_flags", int(Py_TPFLAGS.HAVE_CLASS))
        # end rigmarole
        
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_base", basePtr)
        for field in INHERIT_FIELDS + DONT_INHERIT_FIELDS:
            CPyMarshal.WritePtrField(typePtr, PyTypeObject, field, NO_VALUE)
            CPyMarshal.WritePtrField(basePtr, PyTypeObject, field, SOME_VALUE)
        
        mapper.PyType_Ready(typePtr)
        for field in INHERIT_FIELDS:
            self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, field), SOME_VALUE)
        for field in DONT_INHERIT_FIELDS:
            self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, field), NO_VALUE)
        


suite = makesuite(
    Types_Test,
    OldStyle_Test,
    PyType_GenericNew_Test,
    IC_PyType_New_Test,
    PyType_GenericAlloc_Test,
    PyType_Ready_InheritTest,
)

if __name__ == '__main__':
    run(suite)
