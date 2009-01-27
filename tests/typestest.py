
import types

from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr, UInt32, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import CannotInterpretException, CPyMarshal, HGlobalAllocator, OpaquePyCObject, Python25Mapper, OpaquePyCell
from Ironclad.Structs import PyObject, PyNumberMethods, PyTypeObject, PyVarObject, Py_TPFLAGS

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
    "PyCObject_Type": OpaquePyCObject,
    "PyCell_Type": OpaquePyCell,
}

class Types_Test(TestCase):
    
    @WithMapper
    def testTypeMappings(self, mapper, _):
        for (k, v) in BUILTIN_TYPES.items():
            typePtr = getattr(mapper, k)
            self.assertEquals(mapper.Retrieve(typePtr), v, "failed to map " + k)
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
    def testPyType_Ready(self, mapper, addToCleanUp):
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(typePtr, Marshal.SizeOf(PyTypeObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(typePtr))

        self.assertEquals(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), mapper.PyType_Type, "failed to fill in missing ob_type")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to fill in missing tp_base")

        typeFlags = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_flags")
        self.assertEquals(typeFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready type")
        
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "ob_type", IntPtr.Zero)
        self.assertEquals(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), IntPtr.Zero, "unexpectedly and unnecessarily rereadied type")        


    @WithMapper
    def testReadyBuiltinTypes(self, mapper, _):
        mapper.ReadyBuiltinTypes()
        
        for _type in BUILTIN_TYPES:
            typePtr = getattr(mapper, _type)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            if typePtr not in (mapper.PyBaseObject_Type, mapper.PyBool_Type):
                self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
            if typePtr == mapper.PyBool_Type:
                self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyInt_Type)
            typeTypePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type")
            if typePtr != mapper.PyType_Type:
                self.assertEquals(typeTypePtr, mapper.PyType_Type)


    @WithMapper
    def testNotAutoActualisableTypes(self, mapper, _):
        safeTypes = ("PyString_Type", "PyList_Type", "PyTuple_Type", "PyType_Type")
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
            pass
        cPtr = mapper.Store(C)
        self.assertEquals(CPyMarshal.ReadIntField(cPtr, PyTypeObject, "ob_refcnt"), 2, "seems easiest to 'leak' types, and ensure they live forever")
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "ob_type"), mapper.PyType_Type)
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
        self.assertEquals(CPyMarshal.ReadPtrField(cPtr, PyTypeObject, "tp_as_number"), IntPtr.Zero)

        baseFlags = CPyMarshal.ReadIntField(cPtr, PyTypeObject, "tp_flags")
        self.assertEquals(baseFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready newly-stored type")
        
        instancePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WritePtrField(instancePtr, PyObject, "ob_type", cPtr)
        CPyMarshal.WriteIntField(instancePtr, PyObject, "ob_refcnt", 2)
        
        instance = mapper.Retrieve(instancePtr)
        self.assertEquals(isinstance(instance, C), True)
        self.assertEquals(mapper.Store(instance), instancePtr)


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
    "tp_as_buffer"
)
DONT_INHERIT_FIELDS = (
    "tp_init",
    "tp_repr",
    "tp_str",
)
BASE_FIELD = IntPtr(11111)
KEEP_FIELD = IntPtr(22222)

class PyType_Ready_InheritTest(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.mapper = Python25Mapper()
        self.deallocTypes = CreateTypes(self.mapper)
        self.baseTypePtr, self.deallocBaseType = MakeTypePtr(self.mapper, {})
        for field in INHERIT_FIELDS:
            CPyMarshal.WritePtrField(self.baseTypePtr, PyTypeObject, field, BASE_FIELD)
        
        
    def tearDown(self):
        self.mapper.Dispose()
        self.deallocBaseType()
        self.deallocTypes()
        TestCase.tearDown(self)
        
    
    def testPyType_Ready_MissingBaseType(self):
        self.mapper.PyType_Ready(self.mapper.PyBaseObject_Type)
        self.assertEquals(CPyMarshal.ReadPtrField(self.mapper.PyBaseObject_Type, PyTypeObject, "tp_base"), IntPtr.Zero)
        
        typePtr, deallocType = MakeTypePtr(self.mapper, {})
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_base", IntPtr.Zero)
        self.mapper.PyType_Ready(typePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), self.mapper.PyBaseObject_Type)
        

    def assertInherits(self, field):
        # clear base READY flag
        baseFlags = CPyMarshal.ReadIntField(self.baseTypePtr, PyTypeObject, "tp_flags")
        mask = UInt32(Py_TPFLAGS.READY) ^ UInt32(0xFFFFFFFF)
        CPyMarshal.WriteIntField(self.baseTypePtr, PyTypeObject, "tp_flags", baseFlags & mask)
        
        # create a subtype (not expecting to inherit)
        noTypePtr, deallocNoType = MakeTypePtr(self.mapper, {"tp_base": self.baseTypePtr})
        CPyMarshal.WritePtrField(noTypePtr, PyTypeObject, field, KEEP_FIELD)
        self.assertEquals(self.mapper.PyType_Ready(noTypePtr), 0)
        
        # check base type was readied
        baseFlags = CPyMarshal.ReadIntField(self.baseTypePtr, PyTypeObject, "tp_flags")
        self.assertEquals(baseFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY))
        
        # check subtype was readied
        typeFlags = CPyMarshal.ReadIntField(noTypePtr, PyTypeObject, "tp_flags")
        self.assertEquals(typeFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY))
        
        # check field was not inherited by subtype which defines its own
        self.assertEquals(CPyMarshal.ReadPtrField(noTypePtr, PyTypeObject, field), KEEP_FIELD)
        deallocNoType()
        
        # create another subtype with null field, check that this one does inherit
        yesTypePtr, deallocYesType = MakeTypePtr(self.mapper, {"tp_base": self.baseTypePtr})
        CPyMarshal.WritePtrField(yesTypePtr, PyTypeObject, field, IntPtr.Zero)
        self.assertEquals(self.mapper.PyType_Ready(yesTypePtr), 0)
        self.assertEquals(CPyMarshal.ReadPtrField(yesTypePtr, PyTypeObject, field), BASE_FIELD)
        deallocYesType()
    
    
    def assertDoesNotInherit(self, field):
        # create subtype with null field
        noTypePtr, deallocNoType = MakeTypePtr(self.mapper, {"tp_base": self.baseTypePtr})
        CPyMarshal.WritePtrField(noTypePtr, PyTypeObject, field, IntPtr.Zero)
        self.assertEquals(self.mapper.PyType_Ready(noTypePtr), 0)
        
        # check that null was not filled in
        self.assertEquals(CPyMarshal.ReadPtrField(noTypePtr, PyTypeObject, field), IntPtr.Zero)
        deallocNoType()
        
        
    def testPyType_Ready_InheritsFields(self):
        # TODO: multiple inheritance ignored here for now
        for field in INHERIT_FIELDS:
            self.assertInherits(field)
        for field in DONT_INHERIT_FIELDS:
            self.assertDoesNotInherit(field)
        
    def testPyType_Ready_InheritsSizes(self):
        CPyMarshal.WriteIntField(self.baseTypePtr, PyTypeObject, "tp_basicsize", 123)
        CPyMarshal.WriteIntField(self.baseTypePtr, PyTypeObject, "tp_itemsize", 456)
        
        noSpec = {
            "tp_base": self.baseTypePtr,
            "tp_basicsize": 1234,
            "tp_itemsize": 5678,
        }
        noTypePtr, deallocNoType = MakeTypePtr(self.mapper, noSpec)
        self.assertEquals(self.mapper.PyType_Ready(noTypePtr), 0)
        self.assertEquals(CPyMarshal.ReadIntField(noTypePtr, PyTypeObject, "tp_basicsize"), 1234)
        self.assertEquals(CPyMarshal.ReadIntField(noTypePtr, PyTypeObject, "tp_itemsize"), 5678)
        deallocNoType()
        
        yesSpec = {
            "tp_base": self.baseTypePtr,
            "tp_basicsize": 0,
            "tp_itemsize": 0,
        }
        yesTypePtr, deallocYesType = MakeTypePtr(self.mapper, yesSpec)
        self.assertEquals(self.mapper.PyType_Ready(yesTypePtr), 0)
        self.assertEquals(CPyMarshal.ReadIntField(yesTypePtr, PyTypeObject, "tp_basicsize"), 123)
        self.assertEquals(CPyMarshal.ReadIntField(yesTypePtr, PyTypeObject, "tp_itemsize"), 456)
        deallocYesType()
        
        
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



suite = makesuite(
    Types_Test,
    PyType_Ready_InheritTest,
    PyType_GenericNew_Test,
    PyType_GenericAlloc_Test,
)

if __name__ == '__main__':
    run(suite)
