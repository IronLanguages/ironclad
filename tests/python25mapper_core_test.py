
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator

import os
from textwrap import dedent

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import Python25Mapper
from Ironclad.Structs import PyTypeObject
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

        mapper.FreeTemps()
        self.assertEquals(set(frees), set([IntPtr(12345), IntPtr(13579), IntPtr(56789)]),
                          "memory not freed")


    def testRememberAndFreeTempObjects(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        tempObject1 = mapper.Store(1)
        tempObject2 = mapper.Store(2)

        mapper.RememberTempObject(tempObject1)
        mapper.RememberTempObject(tempObject2)

        self.assertEquals(mapper.RefCount(tempObject1), 1,
                          "RememberTempObject should not incref")
        self.assertEquals(mapper.RefCount(tempObject2), 1,
                          "RememberTempObject should not incref")

        mapper.IncRef(tempObject1)
        mapper.IncRef(tempObject2)

        mapper.FreeTemps()

        try:
            self.assertEquals(mapper.RefCount(tempObject1), 1,
                              "FreeTemps should decref objects rather than freeing them")
            self.assertEquals(mapper.RefCount(tempObject2), 1,
                              "FreeTemps should decref objects rather than freeing them")

            mapper.FreeTemps()
            self.assertEquals(mapper.RefCount(tempObject1), 1,
                              "FreeTemps should clear list once called")
            self.assertEquals(mapper.RefCount(tempObject2), 1,
                              "FreeTemps should clear list once called")
        finally:
            mapper.DecRef(tempObject1)
            mapper.DecRef(tempObject2)



class Python25Mapper_PyInt_FromLong_Test(unittest.TestCase):
    
    def testPyInt_FromLong(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)


class Python25Mapper_PyInt_FromSsize_t_Test(unittest.TestCase):
    
    def testPyInt_FromSsize_t(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromSsize_t(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)



class Python25Mapper_PyFloat_FromDouble_Test(unittest.TestCase):
    
    def testPyFloat_FromDouble(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.PyFloat_FromDouble(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)


class Python25Mapper_PyFile_Type_Test(unittest.TestCase):

    def initPyFile_Type(self, mapper):
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        mapper.SetData("PyFile_Type", typeBlock)
        return typeBlock

    def testPyFile_Type(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        typeBlock = self.initPyFile_Type(mapper)
        try:
            mapper.SetData("PyFile_Type", typeBlock)
            self.assertEquals(mapper.PyFile_Type, typeBlock, "type address not stored")
            self.assertEquals(mapper.Retrieve(typeBlock), file, "type not mapped")
        finally:
            Marshal.FreeHGlobal(typeBlock)
    
    def testCallPyFile_Type(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        
        args = (os.path.join('tests', 'data', 'text.txt'), 'r')
        testText = dedent("""\
text text text
more text
""")
        argsPtr = mapper.Store(args)
        kwargsPtr = IntPtr.Zero
        typeBlock = self.initPyFile_Type(mapper)
        try:
            filePtr = mapper.PyObject_Call(mapper.PyFile_Type, argsPtr, kwargsPtr)
            try:
                f = mapper.Retrieve(filePtr)
                self.assertEquals(f.read(), testText, "didn't get a real file object")
            finally:
                mapper.DecRef(filePtr)
                f.close()
        finally:
            mapper.DecRef(argsPtr)
            Marshal.FreeHGlobal(typeBlock)



suite = makesuite(
    Python25MapperTest,
    Python25Mapper_PyInt_FromLong_Test,
    Python25Mapper_PyInt_FromSsize_t_Test,
    Python25Mapper_PyFloat_FromDouble_Test,
    Python25Mapper_PyFile_Type_Test,
)

if __name__ == '__main__':
    run(suite)