
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import OffsetPtr, CreateTypes
from tests.utils.testcase import TestCase

from System import IntPtr, UInt32
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, OpaquePyCObject, Python25Api, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject, Py_TPFLAGS

class Python25Mapper_Types_Test(TestCase):
    
    def testTypeMappings(self):
        types = {
            "PyType_Type": type,
            "PyBaseObject_Type": object,
            "PyString_Type": str,
            "PyList_Type": list,
            "PyDict_Type": dict,
            "PyTuple_Type": tuple,
            "PyFile_Type": file,
            "PyLong_Type": long,
            "PyInt_Type": int,
            "PyFloat_Type": float,
            "PyComplex_Type": complex,
            "PyCObject_Type": OpaquePyCObject,
        }
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for (k, v) in sorted(types.items()):
            typePtr = getattr(mapper, k)
            self.assertEquals(mapper.Retrieve(typePtr), v, "failed to map " + k)
            self.assertEquals(mapper.RefCount(typePtr), 1, "failed to add reference to " + k)
            
            mapper.PyType_Ready(typePtr)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            if k == "PyBaseObject_Type":
                self.assertEquals(basePtr, IntPtr.Zero)
            else:
                self.assertEquals(basePtr, mapper.PyBaseObject_Type)
             
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyType_IsSubtype(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyType_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyString_Type, mapper.PyString_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyBaseObject_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyList_Type), "wrong")
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyType_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyBaseObject_Type), "wrong")
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyType_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyList_Type), "wrong")
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyString_Type, mapper.PyType_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyType_Type, mapper.PyString_Type), "wrong")
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.Store("foo"), mapper.PyString_Type), "wrong")
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyType_Ready(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(typePtr, Marshal.SizeOf(PyTypeObject))
        self.assertEquals(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), mapper.PyType_Type, "failed to fill in missing ob_type")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to fill in missing tp_base")

        typeFlags = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_flags")
        self.assertEquals(typeFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready type")
        
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "ob_type", IntPtr.Zero)
        self.assertEquals(mapper.PyType_Ready(typePtr), 0, "wrong")
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), IntPtr.Zero, "unexpectedly and unnecessarily rereadied type")        
        
        mapper.Dispose()
        Marshal.FreeHGlobal(typePtr)
        deallocTypes()
    
    
    def testReadyBuiltinTypes(self):
        types = (
            "PyList_Type",
            "PyTuple_Type",
            "PyDict_Type", 
            "PyString_Type", # yes, I'm pretending that unicode and basestring just don't exist
            "PyFile_Type",
            "PyInt_Type",
            "PyLong_Type",
            "PyFloat_Type",
            "PyComplex_Type",
            "PyCObject_Type",
        )
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper, readyTypes=False)
        mapper.ReadyBuiltinTypes()
        
        for _type in types:
            typePtr = getattr(mapper, _type)
            basePtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base")
            self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type)
            self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "ob_type"), mapper.PyType_Type)
        
        mapper.Dispose()
        deallocTypes()
        

FIELDS = (
    "tp_alloc",
    "tp_init",
    "tp_new",
    "tp_dealloc",
    "tp_free",
    "tp_print",
    "tp_repr",
    "tp_str",
    "tp_doc",
    "tp_call",
    "tp_as_number",
    # more to come, no doubt
)
BASE_FIELD = IntPtr(11111)
KEEP_FIELD = IntPtr(22222)

class PyType_Ready_InheritTest(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.mapper = Python25Mapper()
        self.deallocTypes = CreateTypes(self.mapper)
        self.baseTypePtr, self.deallocBaseType = MakeTypePtr(self.mapper, {})
        for field in FIELDS:
            CPyMarshal.WritePtrField(self.baseTypePtr, PyTypeObject, field, BASE_FIELD)
        
        
    def tearDown(self):
        self.mapper.Dispose()
        self.deallocBaseType()
        self.deallocTypes()
        TestCase.tearDown(self)
        

    def assertInherits(self, field):
        baseFlags = CPyMarshal.ReadIntField(self.baseTypePtr, PyTypeObject, "tp_flags")
        mask = UInt32(Py_TPFLAGS.READY) ^ UInt32(0xFFFFFFFF)
        CPyMarshal.WriteIntField(self.baseTypePtr, PyTypeObject, "tp_flags", baseFlags & mask)
        
        noTypePtr, deallocNoType = MakeTypePtr(self.mapper, {"tp_base": self.baseTypePtr})
        CPyMarshal.WritePtrField(noTypePtr, PyTypeObject, field, KEEP_FIELD)
        self.assertEquals(self.mapper.PyType_Ready(noTypePtr), 0)
        self.assertEquals(CPyMarshal.ReadPtrField(noTypePtr, PyTypeObject, field), KEEP_FIELD)
        
        baseFlags = CPyMarshal.ReadIntField(self.baseTypePtr, PyTypeObject, "tp_flags")
        self.assertEquals(baseFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready base type")
        
        typeFlags = CPyMarshal.ReadIntField(noTypePtr, PyTypeObject, "tp_flags")
        self.assertEquals(typeFlags & UInt32(Py_TPFLAGS.READY), UInt32(Py_TPFLAGS.READY), "did not ready subtype")
        deallocNoType()
        
        yesTypePtr, deallocYesType = MakeTypePtr(self.mapper, {"tp_base": self.baseTypePtr})
        CPyMarshal.WritePtrField(yesTypePtr, PyTypeObject, field, IntPtr.Zero)
        self.assertEquals(self.mapper.PyType_Ready(yesTypePtr), 0)
        self.assertEquals(CPyMarshal.ReadPtrField(yesTypePtr, PyTypeObject, field), BASE_FIELD)
        deallocYesType()
        
        
    def testPyType_Ready_InheritsFields(self):
        # TODO: multiple inheritance ignored here for now
        for field in FIELDS:
            self.assertInherits(field)
        
    
    def testPyType_Ready_MissingBaseType(self):
        self.mapper.PyType_Ready(self.mapper.PyBaseObject_Type)
        self.assertEquals(CPyMarshal.ReadPtrField(self.mapper.PyBaseObject_Type, PyTypeObject, "tp_base"), IntPtr.Zero)
        
        typePtr, deallocType = MakeTypePtr(self.mapper, {})
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, "tp_base", IntPtr.Zero)
        self.mapper.PyType_Ready(typePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_base"), self.mapper.PyBaseObject_Type)
        
    
        
class Python25Mapper_PyType_GenericAlloc_Test(TestCase):

    def testNoItems(self):
        allocs = []
        mapper = Python25Mapper(GetAllocatingTestAllocator(allocs, []))
        deallocTypes = CreateTypes(mapper)
        typeSpec = {
            "tp_basicsize": 32,
            "tp_itemsize": 64,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        result = mapper.PyType_GenericAlloc(typePtr, 0)
        self.assertEquals(allocs, [(result, 32)], "allocated wrong")

        refcount = CPyMarshal.ReadInt(result)
        self.assertEquals(refcount, 1, "bad initialisation")

        instanceType = CPyMarshal.ReadPtr(OffsetPtr(result, Marshal.OffsetOf(PyObject, "ob_type")))
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
        result = mapper.PyType_GenericAlloc(typePtr, 3)
        self.assertEquals(allocs, [(result, 224)], "allocated wrong")

        refcount = CPyMarshal.ReadInt(result)
        self.assertEquals(refcount, 1, "bad initialisation")

        instanceType = CPyMarshal.ReadPtr(OffsetPtr(result, Marshal.OffsetOf(PyObject, "ob_type")))
        self.assertEquals(instanceType, typePtr, "bad type ptr")
        
        headerSize = Marshal.SizeOf(PyObject)
        zerosPtr = OffsetPtr(result, headerSize)
        for i in range(224 - headerSize):
            self.assertEquals(CPyMarshal.ReadByte(zerosPtr), 0, "not zeroed")
            zerosPtr = OffsetPtr(zerosPtr, 1)
 
        mapper.Dispose()
        deallocTypes()
        deallocType()


class Python25Mapper_PyType_GenericNew_Test(TestCase):

    def testCallsTypeAllocFunction(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)

        calls = []
        def Alloc(typePtr, nItems):
            calls.append((typePtr, nItems))
            return IntPtr(999)

        typeSpec = {
            "tp_alloc": Alloc,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        result = mapper.PyType_GenericNew(typePtr, IntPtr(222), IntPtr(333))
        self.assertEquals(result, IntPtr(999), "did not use type's tp_alloc function")
        self.assertEquals(calls, [(typePtr, 0)], "passed wrong args")
         
        mapper.Dispose()
        deallocTypes()
        deallocType()
        


suite = makesuite(
    Python25Mapper_Types_Test,
    PyType_Ready_InheritTest,
    Python25Mapper_PyType_GenericNew_Test,
    Python25Mapper_PyType_GenericAlloc_Test,
)

if __name__ == '__main__':
    run(suite)