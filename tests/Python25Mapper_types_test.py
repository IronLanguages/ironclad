
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import OffsetPtr, CreateTypes

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, PythonMapper, Python25Mapper
from Ironclad.Structs import PyObject

class Python25Mapper_Types_Test(unittest.TestCase):
    
    def testTypeMappings(self):
        types = {
            "PyBaseObject_Type": object,
            "PyString_Type": str,
            "PyList_Type": list,
            "PyTuple_Type": tuple,
            "PyFile_Type": file,
            "PyLong_Type": long,
            "PyInt_Type": int,
            "PyFloat_Type": float,
        }
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for (k, v) in types.items():
            self.assertEquals(mapper.Retrieve(getattr(mapper, k)), v, "failed to map " + k)
            
        deallocTypes()
    
    
    def testPyType_IsSubtype(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyBaseObject_Type), "wrong")
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyList_Type), "wrong")
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyList_Type), "wrong")
        self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyBaseObject_Type), "wrong")
        
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyString_Type, mapper.PyList_Type), "wrong")
        self.assertFalse(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyString_Type), "wrong")
        
        deallocTypes()
        
                
        
class Python25Mapper_PyType_GenericAlloc_Test(unittest.TestCase):

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

        Marshal.FreeHGlobal(allocs[0][0])
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

        Marshal.FreeHGlobal(allocs[0][0])
        deallocTypes()
        deallocType()


class Python25Mapper_PyType_GenericNew_Test(unittest.TestCase):

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
        
        deallocTypes()
        deallocType()
        


suite = makesuite(
    Python25Mapper_Types_Test,
    Python25Mapper_PyType_GenericNew_Test,
    Python25Mapper_PyType_GenericAlloc_Test,
)

if __name__ == '__main__':
    run(suite)