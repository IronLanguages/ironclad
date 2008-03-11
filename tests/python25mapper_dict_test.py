
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import CreateTypes, OffsetPtr

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject
from IronPython.Hosting import PythonEngine




class Python25MapperDictTest(unittest.TestCase):

    def testPyDict_New(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))
        deallocTypes = CreateTypes(mapper)
        
        try:
            dictPtr = mapper.PyDict_New()
            self.assertEquals(mapper.RefCount(dictPtr), 1, "bad refcount")
            self.assertEquals(allocs, [(dictPtr, Marshal.SizeOf(PyObject))], "did not allocate as expected")
            ob_typePtr = OffsetPtr(dictPtr, Marshal.OffsetOf(PyObject, "ob_type"))
            self.assertEquals(CPyMarshal.ReadPtr(ob_typePtr), mapper.PyDict_Type, "wrong type")
            dictObj = mapper.Retrieve(dictPtr)
            self.assertEquals(dictObj, {}, "retrieved unexpected value")
            
            mapper.DecRef(dictPtr)
            self.assertRaises(KeyError, lambda: mapper.RefCount(dictPtr))
            self.assertEquals(frees, [dictPtr], "did not release memory")
        finally:
            deallocTypes()


    def testPyDict_Size(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        dict0 = mapper.Store({})
        dict3 = mapper.Store({1:2, 3:4, 5:6})
        try:
            self.assertEquals(mapper.PyDict_Size(dict0), 0, "wrong")
            self.assertEquals(mapper.PyDict_Size(dict3), 3, "wrong")
        finally:
            deallocTypes()


    def testPyDict_GetItemStringSuccess(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({"abcde": 12345})
        try:
            itemPtr = mapper.PyDict_GetItemString(dictPtr, "abcde")
            self.assertEquals(mapper.Retrieve(itemPtr), 12345, "failed to get item")
            self.assertEquals(mapper.RefCount(itemPtr), 1, "something is wrong")
            mapper.FreeTemps()
            self.assertRaises(KeyError, lambda: mapper.RefCount(itemPtr))
        finally:
            mapper.DecRef(dictPtr)
            deallocTypes()


    def testPyDict_GetItemStringFailure(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        dictPtr = mapper.Store({"abcde": 12345})
        try:
            itemPtr = mapper.PyDict_GetItemString(dictPtr, "bwahahaha!")
            self.assertEquals(itemPtr, IntPtr.Zero, "bad return for missing key")
            self.assertEquals(mapper.LastException, None, "should not set exception")
        finally:
            mapper.DecRef(dictPtr)
            deallocTypes()
        

    def testStoreDictCreatesDictType(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyDict_Type", typeBlock)
            dictPtr = mapper.Store({0: 1, 2: 3})
            try:
                ob_typePtr = OffsetPtr(dictPtr, Marshal.OffsetOf(PyObject, "ob_type"))
                self.assertEquals(CPyMarshal.ReadPtr(ob_typePtr), typeBlock, "wrong type")
            finally:
                mapper.DecRef(dictPtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)


suite = makesuite(
    Python25MapperDictTest,
)

if __name__ == '__main__':
    run(suite)