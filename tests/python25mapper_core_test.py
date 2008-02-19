
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.memory import OffsetPtr

import System
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import CPyMarshal, PythonMapper, Python25Mapper
from JumPy.Structs import PyObject
from IronPython.Hosting import PythonEngine




class Python25MapperTest(unittest.TestCase):

    def testBasicStoreRetrieveDelete(self):
        frees = []
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))

        obj1 = object()
        self.assertEquals(allocs, [], "unexpected allocations")
        ptr = mapper.Store(obj1)
        self.assertEquals(len(allocs), 1, "unexpected number of allocations")
        self.assertEquals(allocs[0][0], ptr, "unexpected result")
        self.assertNotEquals(ptr, IntPtr.Zero, "did not store reference")
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")

        obj2 = mapper.Retrieve(ptr)
        self.assertTrue(obj1 is obj2, "retrieved wrong object")

        self.assertEquals(frees, [], "unexpected deallocations")
        mapper.Delete(ptr)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
        self.assertRaises(KeyError, lambda: mapper.Delete(ptr))


    def testStoreUnmanagedData(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        o = object()
        mapper.StoreUnmanagedData(IntPtr(123), o)

        self.assertEquals(mapper.Retrieve(IntPtr(123)), o, "object not stored")


    def testRefCountIncRefDecRef(self):
        frees = []
        engine = PythonEngine()
        allocator = GetAllocatingTestAllocator([], frees)
        mapper = Python25Mapper(engine, allocator)

        obj1 = object()
        ptr = mapper.Store(obj1)
        mapper.IncRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 2, "unexpected refcount")

        mapper.DecRef(ptr)
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")

        self.assertEquals(frees, [], "unexpected deallocations")
        mapper.DecRef(ptr)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
        self.assertRaises(KeyError, lambda: mapper.Delete(ptr))

        self.assertEquals(mapper.RefCount(IntPtr(1)), 0, "unknown objects' should be 0")


    def testNullPointers(self):
        engine = PythonEngine()
        allocator = GetDoNothingTestAllocator([])
        mapper = Python25Mapper(engine, allocator)

        self.assertRaises(KeyError, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Delete(IntPtr.Zero))

        self.assertEquals(mapper.RefCount(IntPtr.Zero), 0, "wrong")


    def testRememberAndFreeTempPtrs(self):
        # hopefully, nobody will depend on character data from PyArg_Parse* remaining
        # available beyond the function call in which it was provided. hopefully.
        frees = []
        engine = PythonEngine()
        allocator = GetDoNothingTestAllocator(frees)
        mapper = Python25Mapper(engine, allocator)

        mapper.RememberTempPtr(IntPtr(12345))
        mapper.RememberTempPtr(IntPtr(13579))
        mapper.RememberTempPtr(IntPtr(56789))
        self.assertEquals(frees, [], "freed memory prematurely")

        mapper.FreeTempPtrs()
        self.assertEquals(set(frees), set([IntPtr(12345), IntPtr(13579), IntPtr(56789)]),
                          "memory not freed")


class Python25Mapper_PyType_GenericNew_Test(unittest.TestCase):

    def testCallsTypeAllocFunction(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        mapper.SetData("PyType_Type", IntPtr(123))

        calls = []
        def AllocInstance(typePtr, nItems):
            calls.append((typePtr, nItems))
            return IntPtr(999)
        tp_allocDgt = PythonMapper.PyType_GenericAlloc_Delegate(AllocInstance)
        tp_allocFP = Marshal.GetFunctionPointerForDelegate(tp_allocDgt)

        typePtr, deallocType = MakeTypePtr(
            "sometype", mapper.PyType_Type, tp_allocPtr=tp_allocFP)
        try:
            result = mapper.PyType_GenericNew(typePtr, IntPtr(222), IntPtr(333))
            self.assertEquals(result, IntPtr(999), "did not use type's tp_alloc function")
            self.assertEquals(calls, [(typePtr, 0)], "passed wrong args")
        finally:
            deallocType()


class Python25Mapper_PyType_GenericAlloc_Test(unittest.TestCase):

    def testNoItems(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        mapper.SetData("PyType_Type", IntPtr(123))

        typePtr, deallocType = MakeTypePtr("sometype", mapper.PyType_Type,
                                           basicSize=32, itemSize=64)
        try:
            result = mapper.PyType_GenericAlloc(typePtr, 0)
            self.assertEquals(allocs, [(result, 32)], "allocated wrong")

            refcount = CPyMarshal.ReadInt(result)
            self.assertEquals(refcount, 1, "bad initialisation")

            instanceType = CPyMarshal.ReadPtr(OffsetPtr(result, Marshal.OffsetOf(PyObject, "ob_type")))
            self.assertEquals(instanceType, typePtr, "bad type ptr")

        finally:
            Marshal.FreeHGlobal(allocs[0][0])
            deallocType()


    def testSomeItems(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        mapper.SetData("PyType_Type", IntPtr(123))

        typePtr, deallocType = MakeTypePtr("sometype", mapper.PyType_Type,
                                           basicSize=32, itemSize=64)
        try:
            result = mapper.PyType_GenericAlloc(typePtr, 3)
            self.assertEquals(allocs, [(result, 224)], "allocated wrong")

            refcount = CPyMarshal.ReadInt(result)
            self.assertEquals(refcount, 1, "bad initialisation")

            instanceType = CPyMarshal.ReadPtr(OffsetPtr(result, Marshal.OffsetOf(PyObject, "ob_type")))
            self.assertEquals(instanceType, typePtr, "bad type ptr")

        finally:
            Marshal.FreeHGlobal(allocs[0][0])
            deallocType()


class Python25Mapper_Exception_Test(unittest.TestCase):

    def testException(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        self.assertEquals(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEquals(type(mapper.LastException), System.Exception,
                          "get should retrieve last set exception")
        self.assertEquals(mapper.LastException.Message, "doozy",
                          "get should retrieve last set exception")




suite = makesuite(
    Python25MapperTest,
    Python25Mapper_PyType_GenericNew_Test,
    Python25Mapper_PyType_GenericAlloc_Test,
    Python25Mapper_Exception_Test,
)

if __name__ == '__main__':
    run(suite)