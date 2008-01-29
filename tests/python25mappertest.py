
import unittest

from System import Array, Int32, IntPtr
from System.Reflection import BindingFlags
from System.Runtime.InteropServices import Marshal
from JumPy import (
    CPythonVarargsFunction_Delegate, CPythonVarargsKwargsFunction_Delegate,
    IAllocator, METH, PyMethodDef, Python25Mapper, StubReference
)
from IronPython.Hosting import PythonEngine


def NullCPythonFunction(_, __):
    return IntPtr.Zero
NullCPythonDelegate = CPythonVarargsFunction_Delegate(NullCPythonFunction)
NullCPythonFunctionPointer = Marshal.GetFunctionPointerForDelegate(NullCPythonDelegate)


def PythonModuleFromEngineModule(engineModule):
    engineModuleType = engineModule.GetType()
    pythonModuleInfo = engineModuleType.GetMember("Module",
        BindingFlags.NonPublic | BindingFlags.Instance)[0]
    return pythonModuleInfo.GetValue(engineModule, Array[object]([]))


def GetTestAllocator(allocsList, freesList):
    class TestAllocator(IAllocator):
        def Allocate(self, bytes):
            ptr = Marshal.AllocHGlobal(bytes)
            allocsList.append(ptr)
            return ptr
        def Free(self, ptr):
            freesList.append(ptr)
            Marshal.FreeHGlobal(ptr)
    return TestAllocator


class Python25MapperTest(unittest.TestCase):

    def testBasicStoreRetrieveDelete(self):
        frees = []
        allocs = []
        engine = PythonEngine()
        allocator = GetTestAllocator(allocs, frees)()
        mapper = Python25Mapper(engine, allocator)

        obj1 = object()
        self.assertEquals(allocs, [], "unexpected allocations")
        ptr = mapper.Store(obj1)
        self.assertEquals(allocs, [ptr], "unexpected allocations")
        self.assertNotEquals(ptr, IntPtr.Zero, "did not store reference")
        self.assertEquals(mapper.RefCount(ptr), 1, "unexpected refcount")

        obj2 = mapper.Retrieve(ptr)
        self.assertTrue(obj1 is obj2, "retrieved wrong object")

        self.assertEquals(frees, [], "unexpected deallocations")
        mapper.Delete(ptr)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
        self.assertRaises(KeyError, lambda: mapper.Delete(ptr))


    def testIncRefDecRef(self):
        frees = []
        engine = PythonEngine()
        allocator = GetTestAllocator([], frees)()
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


    def testNullPointers(self):
        engine = PythonEngine()
        allocator = GetTestAllocator([], [])()
        mapper = Python25Mapper(engine, allocator)

        self.assertRaises(KeyError, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Delete(IntPtr.Zero))



class Python25Mapper_Py_InitModule4_Test(unittest.TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, engine, mapper, method, moduleTest):
        size = Marshal.SizeOf(PyMethodDef)
        methods = Marshal.AllocHGlobal(size * 2)
        try:
            Marshal.StructureToPtr(method, methods, False)
            terminator = IntPtr(methods.ToInt32() + size)
            Marshal.WriteInt64(terminator, 0)

            modulePtr = mapper.Py_InitModule4(
                "test_module",
                methods,
                "test_docstring",
                IntPtr.Zero,
                12345
            )

            engineModule = mapper.Retrieve(modulePtr)
            pythonModule = PythonModuleFromEngineModule(engineModule)

            test_module = engine.Sys.modules['test_module']
            self.assertEquals(pythonModule, test_module, "mapping incorrect")
            moduleTest(test_module, mapper)
        finally:
            Marshal.FreeHGlobal(methods)


    def test_Py_InitModule4_CreatesPopulatedModuleInSys(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        method = PyMethodDef(
            "harold",
            NullCPythonFunctionPointer,
            METH.VARARGS,
            "harold's documentation",
        )

        def testModule(test_module, _):
            self.assertEquals(test_module.__doc__, 'test_docstring',
                              'module docstring not remembered')
            self.assertTrue(callable(test_module.harold),
                            'function not remembered')
            self.assertEquals(test_module.harold.__doc__, "harold's documentation",
                              'function docstring not remembered')

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_DispatchesToOriginalVarargsFunction(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.IncRef(argPtr)
            return IntPtr.Zero
        cModuleDelegate = CPythonVarargsFunction_Delegate(CModuleFunction)

        method = PyMethodDef(
            "harold",
            Marshal.GetFunctionPointerForDelegate(cModuleDelegate),
            METH.VARARGS,
            "harold's documentation",
        )

        def testModule(test_module, mapper):
            test_module.harold(1, 2, 3)
            _selfPtr, argPtr = calls[0]
            self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")

            # CModuleFunction retained a reference, so we could test the aftermath
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                              "did not pass pointer mapping to correct tuple")

            self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference counting")
            mapper.DecRef(argPtr)

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_DispatchesToOriginalVarargsKwargsFunction(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        calls = []
        def CModuleFunction(_selfPtr, argPtr, kwargPtr):
            calls.append((_selfPtr, argPtr, kwargPtr))
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            return IntPtr.Zero
        cModuleDelegate = CPythonVarargsKwargsFunction_Delegate(CModuleFunction)

        method = PyMethodDef(
            "harold",
            Marshal.GetFunctionPointerForDelegate(cModuleDelegate),
            METH.VARARGS | METH.KEYWORDS,
            "harold's documentation",
        )

        def testModule(test_module, mapper):
            test_module.harold(1, 2, 3, four=4, five=5)
            _selfPtr, argPtr, kwargPtr = calls[0]
            self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")

            # CModuleFunction retained references, so we could test the aftermath
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                              "did not pass pointer mapping to correct tuple")
            self.assertEquals(mapper.Retrieve(kwargPtr), {"four": 4, "five": 5},
                              "did not pass pointer mapping to correct dict")

            self.assertEquals(mapper.RefCount(kwargPtr), 1, "bad reference counting")
            self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference counting")
            mapper.DecRef(kwargPtr)
            mapper.DecRef(argPtr)

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


class Python25Mapper_PyArg_ParseTupleAndKeywords_Test(unittest.TestCase):

    def assertParsesTupleAndKeywords_WithInts(self, args, kwargs, format, kwlist, expectedResults):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        ptrsize = Marshal.SizeOf(IntPtr)
        intsize = Marshal.SizeOf(Int32)

        # alloc
        argsPtr = mapper.Store(args)
        kwargsPtr = mapper.Store(kwargs)
        outPtr = Marshal.AllocHGlobal(ptrsize * (len(kwlist) + 1))
        actualDataPtr = Marshal.AllocHGlobal(intsize * len(kwlist))

        kwlistPtr = Marshal.AllocHGlobal(ptrsize * (len(kwlist) + 1))
        current = kwlistPtr
        for s in kwlist:
            addressWritten = Marshal.StringToHGlobalUni(s)
            Marshal.WriteIntPtr(current, addressWritten)
            current = IntPtr(current.ToInt32() + ptrsize)

        try:
            # memory setup - fill actualData with 0s
            Marshal.WriteIntPtr(current, IntPtr.Zero)
            for i in range(len(kwlist)):
                Marshal.WriteInt32(IntPtr(actualDataPtr.ToInt32() + (i * intsize)), 0)
                Marshal.WriteIntPtr(IntPtr(outPtr.ToInt32() + (i * ptrsize)),
                                    IntPtr(actualDataPtr.ToInt32() + (i * intsize)))
            Marshal.WriteIntPtr(IntPtr(outPtr.ToInt32() + (len(kwlist) * ptrsize)), IntPtr.Zero)

            # actual test
            retval = mapper.PyArg_ParseTupleAndKeywords(argsPtr, kwargsPtr, format, kwlistPtr, outPtr)
            results = [Marshal.ReadInt32(IntPtr(actualDataPtr.ToInt32() + (i * intsize)))
                       for i in range(len(kwlist))]

            self.assertEquals(retval, True, "reported failure")
            self.assertEquals(results, expectedResults, "something, somewhere, broke")
        finally:
            # dealloc
            mapper.DecRef(argsPtr)
            mapper.DecRef(kwargsPtr)
            for i in range(len(kwlist)):
                Marshal.FreeHGlobal(Marshal.ReadIntPtr(IntPtr(kwlistPtr.ToInt32() + (i * ptrsize))))
            Marshal.FreeHGlobal(kwlistPtr)
            Marshal.FreeHGlobal(outPtr)
            Marshal.FreeHGlobal(actualDataPtr)


    def testNone(self):
        args = tuple()
        kwargs = {}
        format = 'lll'
        kwlist = ['one', 'two', 'three']
        expectedResults = [0, 0, 0]

        self.assertParsesTupleAndKeywords_WithInts(
            args, kwargs, format, kwlist, expectedResults)


    def testArgsOnly(self):
        args = (1, 2, 3)
        kwargs = {}
        format = 'lll'
        kwlist = ['one', 'two', 'three']
        expectedResults = [1, 2, 3]

        self.assertParsesTupleAndKeywords_WithInts(
            args, kwargs, format, kwlist, expectedResults)


    def testSingleKwarg(self):
        args = ()
        kwargs = {'two': 2}
        format = 'lll'
        kwlist = ['one', 'two', 'three']
        expectedResults = [0, 2, 0]

        self.assertParsesTupleAndKeywords_WithInts(
            args, kwargs, format, kwlist, expectedResults)


    def testKwargsOnly(self):
        args = ()
        kwargs = {'one': 3, 'two': 2, 'three': 1}
        format = 'lll'
        kwlist = ['one', 'two', 'three']
        expectedResults = [3, 2, 1]

        self.assertParsesTupleAndKeywords_WithInts(
            args, kwargs, format, kwlist, expectedResults)


    def testMixture(self):
        args = (1,)
        kwargs = {'three': 3}
        format = 'lll'
        kwlist = ['one', 'two', 'three']
        expectedResults = [1, 0, 3]

        self.assertParsesTupleAndKeywords_WithInts(
            args, kwargs, format, kwlist, expectedResults)







suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(Python25MapperTest))
suite.addTest(loader.loadTestsFromTestCase(Python25Mapper_Py_InitModule4_Test))
suite.addTest(loader.loadTestsFromTestCase(Python25Mapper_PyArg_ParseTupleAndKeywords_Test))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)