
import unittest

from System import Array, IntPtr
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



class Python25MapperTest(unittest.TestCase):

    def testBasicStoreRetrieveDelete(self):
        allocs = []
        frees = []
        class TestAllocator(IAllocator):
            def Allocate(self, bytes):
                ptr = Marshal.AllocHGlobal(bytes)
                allocs.append(ptr)
                return ptr
            def Free(self, ptr):
                frees.append(ptr)
                Marshal.FreeHGlobal(ptr)

        engine = PythonEngine()
        allocator = TestAllocator()
        mapper = Python25Mapper(engine, allocator)

        obj1 = object()
        ptr = mapper.Store(obj1)
        self.assertNotEquals(ptr, IntPtr.Zero, "did not store reference")
        self.assertEquals(Marshal.ReadInt32(ptr), 1, "unexpected refcount")
        self.assertEquals(allocs, [ptr], "unexpected allocations")

        obj2 = mapper.Retrieve(ptr)
        self.assertTrue(obj1 is obj2, "retrieved wrong object")

        mapper.Delete(ptr)
        self.assertEquals(frees, [ptr], "unexpected deallocations")
        self.assertRaises(KeyError, lambda: mapper.Retrieve(ptr))
        self.assertRaises(KeyError, lambda: mapper.Delete(ptr))
        self.assertEquals(frees, [ptr], "unexpected deallocations")



class Python25Mapper_Py_InitModule4_Test(unittest.TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, method, moduleTest):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
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
            moduleTest(test_module)
        finally:
            Marshal.FreeHGlobal(methods)


    def test_Py_InitModule4_CreatesPopulatedModuleInSys(self):
        method = PyMethodDef(
            "harold",
            NullCPythonFunctionPointer,
            METH.VARARGS,
            "harold's documentation",
        )

        def testModule(test_module):
            self.assertEquals(test_module.__doc__, 'test_docstring',
                              'module docstring not remembered')
            self.assertTrue(callable(test_module.harold),
                            'function not remembered')
            self.assertEquals(test_module.harold.__doc__, "harold's documentation",
                              'function docstring not remembered')

        self.assert_Py_InitModule4_withSingleMethod(method, testModule)


    def test_Py_InitModule4_DispatchesToOriginalVarargsFunction(self):
        result = []
        def CModuleFunction(_selfPtr, argPtr):
            result.append((_selfPtr, argPtr))
            return IntPtr.Zero
        cModuleDelegate = CPythonVarargsFunction_Delegate(CModuleFunction)

        method = PyMethodDef(
            "harold",
            Marshal.GetFunctionPointerForDelegate(cModuleDelegate),
            METH.VARARGS,
            "harold's documentation",
        )

        def testModule(test_module):
            test_module.harold()
            _selfPtr, argPtr = result[0]
            self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")
            self.assertNotEquals(argPtr, IntPtr.Zero, "did not pass potentially-sane pointer to args")

        self.assert_Py_InitModule4_withSingleMethod(method, testModule)


    def test_Py_InitModule4_DispatchesToOriginalVarargsKwargsFunction(self):
        result = []
        def CModuleFunction(_selfPtr, argPtr, kwargPtr):
            result.append((_selfPtr, argPtr, kwargPtr))
            return IntPtr.Zero
        cModuleDelegate = CPythonVarargsKwargsFunction_Delegate(CModuleFunction)

        method = PyMethodDef(
            "harold",
            Marshal.GetFunctionPointerForDelegate(cModuleDelegate),
            METH.VARARGS | METH.KEYWORDS,
            "harold's documentation",
        )

        def testModule(test_module):
            test_module.harold()
            _selfPtr, argPtr, kwargPtr = result[0]
            self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")
            self.assertNotEquals(argPtr, IntPtr.Zero, "did not pass potentially-sane pointer to args")
            self.assertNotEquals(argPtr, IntPtr.Zero, "did not pass potentially-sane pointer to kwargs")

        self.assert_Py_InitModule4_withSingleMethod(method, testModule)




suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(Python25MapperTest))
suite.addTest(loader.loadTestsFromTestCase(Python25Mapper_Py_InitModule4_Test))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)