
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.memory import OffsetPtr

import System
from System import Array, Delegate, IntPtr
from System.Collections.Generic import Dictionary
from System.Reflection import BindingFlags
from System.Runtime.InteropServices import Marshal
from JumPy import (
    ArgWriter, CPyMarshal, CPythonVarargsFunction_Delegate,
    CPythonVarargsKwargsFunction_Delegate, IntArgWriter, PythonMapper, Python25Mapper,
    SizedStringArgWriter
)
from JumPy.Structs import METH, PyMethodDef, PyObject, PyTypeObject
from IronPython.Hosting import PythonEngine


def PythonModuleFromEngineModule(engineModule):
    engineModuleType = engineModule.GetType()
    pythonModuleInfo = engineModuleType.GetMember("Module",
        BindingFlags.NonPublic | BindingFlags.Instance)[0]
    return pythonModuleInfo.GetValue(engineModule, Array[object]([]))


class TempPtrCheckingPython25Mapper(Python25Mapper):
    def __init__(self, *args):
        Python25Mapper.__init__(self, *args)
        self.tempPtrsFreed = False
    def FreeTempPtrs(self):
        Python25Mapper.FreeTempPtrs(self)
        self.tempPtrsFreed = True


def MakeMethodDef(name, implementation, flags, doc="doc"):
    if flags == METH.VARARGS:
        funcPtr = CPythonVarargsFunction_Delegate(implementation)
    elif flags == METH.VARARGS | METH.KEYWORDS:
        funcPtr = CPythonVarargsKwargsFunction_Delegate(implementation)
    return PyMethodDef(name, Marshal.GetFunctionPointerForDelegate(funcPtr), flags, doc)


def MakeTypePtr(tp_name, typeTypePtr,
                basicSize=8, itemSize=4, methodDef=None,
                tp_allocPtr=IntPtr.Zero, tp_newPtr=IntPtr.Zero):
    typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
    namePtr = Marshal.StringToHGlobalAnsi(tp_name)
    methodsPtr, deallocMethods = MakeSingleMethodTablePtr(methodDef)

    def WriteField(fieldName, writerName, value):
        offset = Marshal.OffsetOf(PyTypeObject, fieldName)
        address = OffsetPtr(typePtr, offset)
        getattr(CPyMarshal, writerName)(address, value)

    WriteField("ob_refcnt", "WriteInt", 1)
    WriteField("ob_type", "WritePtr", typeTypePtr)

    WriteField("tp_basicsize", "WriteInt", basicSize)
    WriteField("tp_itemsize", "WriteInt", itemSize)

    WriteField("tp_name", "WritePtr", namePtr)
    WriteField("tp_methods", "WritePtr", methodsPtr)
    WriteField("tp_alloc", "WritePtr", tp_allocPtr)
    WriteField("tp_new", "WritePtr", tp_newPtr)

    def dealloc():
        Marshal.FreeHGlobal(typePtr)
        Marshal.FreeHGlobal(namePtr)
        deallocMethods()

    return typePtr, dealloc


def MakeSingleMethodTablePtr(methodDef):
    if methodDef is None:
        return IntPtr.Zero, lambda: None
    size = Marshal.SizeOf(PyMethodDef)
    methodsPtr = Marshal.AllocHGlobal(size * 2)
    Marshal.StructureToPtr(methodDef, methodsPtr, False)
    terminator = OffsetPtr(methodsPtr, size)
    CPyMarshal.WriteInt(terminator, 0)

    def dealloc():
        Marshal.DestroyStructure(methodsPtr, PyMethodDef)
        Marshal.FreeHGlobal(methodsPtr)

    return methodsPtr, dealloc


def MakeAndAddEmptyModule(mapper):
    modulePtr = mapper.Py_InitModule4(
        "test_module",
        IntPtr.Zero,
        "test_docstring",
        IntPtr.Zero,
        12345
    )
    return modulePtr



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





class Python25Mapper_Py_InitModule4_Test(unittest.TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, engine, mapper, methodDef, moduleTest):
        size = Marshal.SizeOf(PyMethodDef)
        methods, deallocMethods = MakeSingleMethodTablePtr(methodDef)
        try:
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
            deallocMethods()
            mapper.FreeTempPtrs()


    def test_Py_InitModule4_CreatesPopulatedModuleInSys(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        method = MakeMethodDef(
            "harold", lambda _, __: IntPtr.Zero, METH.VARARGS, "harold's documentation",
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
        mapper = TempPtrCheckingPython25Mapper(engine)
        retval = mapper.Store("jedi")
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.IncRef(argPtr)
            return retval
        method = MakeMethodDef("func", CModuleFunction, METH.VARARGS)

        def testModule(test_module, mapper):
            try:
                self.assertEquals(test_module.func(1, 2, 3), "jedi", "bad result")
                self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up after call")
                _selfPtr, argPtr = calls[0]
                self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")

                # CModuleFunction retained a reference, so we could test the aftermath
                self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                                  "did not pass pointer mapping to correct tuple")

                self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference counting")
            finally:
                mapper.DecRef(argPtr)

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_VarargsFunctionRaisesAppropriateExceptions(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        calls = []
        class BorkedException(System.Exception):
            pass
        def CModuleFunction(_selfPtr, argPtr):
            calls.append(argPtr)
            mapper.IncRef(argPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        method = MakeMethodDef("func", CModuleFunction, METH.VARARGS)

        def testModule(test_module, mapper):
            try:
                self.assertRaises(BorkedException, test_module.func, (1, 2, 3))
                self.assertEquals(mapper.RefCount(calls[0]), 1, "failed to DecRef argPtr on error")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up temp ptrs on error")
                self.assertEquals(mapper.LastException, None, "exception not cleared when raised")
            finally:
                mapper.DecRef(calls[0])

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_DispatchesToOriginalVarargsKwargsFunction(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        retval = mapper.Store("sith")
        calls = []
        def CModuleFunction(_selfPtr, argPtr, kwargPtr):
            calls.append((_selfPtr, argPtr, kwargPtr))
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            return retval
        method = MakeMethodDef("func", CModuleFunction, METH.VARARGS | METH.KEYWORDS)

        def testModule(test_module, mapper):
            try:
                self.assertEquals(test_module.func(1, 2, 3, four=4, five=5), "sith", "bad result")
                self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up after call")
                _selfPtr, argPtr, kwargPtr = calls[0]
                self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")

                # CModuleFunction retained references, so we could test the aftermath
                self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                                  "did not pass pointer mapping to correct tuple")
                self.assertEquals(mapper.Retrieve(kwargPtr), {"four": 4, "five": 5},
                                  "did not pass pointer mapping to correct dict")

                self.assertEquals(mapper.RefCount(kwargPtr), 1, "bad reference counting")
                self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference counting")
            finally:
                mapper.DecRef(kwargPtr)
                mapper.DecRef(argPtr)

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_VarargsKwargsFunctionRaisesAppropriateExceptions(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        calls = []
        class BorkedException(System.Exception):
            pass
        def CModuleFunction(_selfPtr, argPtr, kwargPtr):
            calls.append(argPtr)
            mapper.IncRef(argPtr)
            calls.append(kwargPtr)
            mapper.IncRef(kwargPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        method = MakeMethodDef("func", CModuleFunction, METH.VARARGS | METH.KEYWORDS)

        def testModule(test_module, mapper):
            try:
                self.assertRaises(BorkedException, lambda: test_module.func(1, 2, 3, four=5))
                self.assertEquals(mapper.RefCount(calls[0]), 1, "failed to DecRef argPtr on error")
                self.assertEquals(mapper.RefCount(calls[1]), 1, "failed to DecRef kwargPtr on error")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up temp ptrs on error")
                self.assertEquals(mapper.LastException, None, "exception not cleared when raised")
            finally:
                mapper.DecRef(calls[0])
                mapper.DecRef(calls[1])

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


class Python25Mapper_PyModule_AddObject_Test(unittest.TestCase):

    def testAddObjectToUnknownModuleFails(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        self.assertEquals(mapper.PyModule_AddObject(IntPtr.Zero, "zorro", IntPtr.Zero), -1,
                          "bad return on failure")


    def testAddObjectWithExistingReferenceAddsMappedObjectAndDecRefsPointer(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        testObject = object()
        testPtr = mapper.Store(testObject)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        result = mapper.PyModule_AddObject(modulePtr, "testObject", testPtr)
        try:
            self.assertEquals(result, 0, "bad value for success")
            self.assertEquals(mapper.RefCount(testPtr), 0, "did not decref")
            self.assertEquals(module.Globals["testObject"], testObject, "did not store real object")
        finally:
            mapper.DecRef(modulePtr)
            if mapper.RefCount(testPtr):
                mapper.DecRef(testPtr)


    def assertModuleAddsTypeWithData(self, tp_name, itemName, class__module__, class__name__):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        mapper.SetData("PyType_Type", IntPtr(123))
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        calls = []
        def new(_, __, ___):
            calls.append("called")
            return IntPtr.Zero
        newDgt = PythonMapper.PyType_GenericNew_Delegate(new)
        newFP = Marshal.GetFunctionPointerForDelegate(newDgt)

        typePtr, deallocType = MakeTypePtr(tp_name, mapper.PyType_Type, tp_newPtr=newFP)
        try:
            result = mapper.PyModule_AddObject(modulePtr, itemName, typePtr)

            self.assertEquals(result, 0, "reported failure")

            mappedClass = mapper.Retrieve(typePtr)
            generatedClass = module.Globals[itemName]
            self.assertEquals(mappedClass, generatedClass,
                              "failed to add new type to module")

            self.assertEquals(mappedClass._typePtr, typePtr, "not connected to underlying CPython type")
            self.assertEquals(mappedClass.__name__, class__name__, "unexpected __name__")
            self.assertEquals(mappedClass.__module__, class__module__, "unexpected __module__")

            mappedClass._tp_newDgt(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
            self.assertEquals(calls, ["called"], "tp_new not hooked up correctly")
        finally:
            deallocType()
            mapper.DecRef(modulePtr)


    def testAddModule(self):
        self.assertModuleAddsTypeWithData(
            "some.module.Klass",
            "KlassName",
            "some.module",
            "Klass",
        )
        self.assertModuleAddsTypeWithData(
            "Klass",
            "KlassName",
            "",
            "Klass",
        )


    def testAddTypeObjectAndInstantiate(self):
        allocs = []
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        mapper.SetData("PyType_Type", IntPtr(123))
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        calls = []
        def new(typePtr, argPtr, kwargPtr):
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            calls.append((typePtr, argPtr, kwargPtr))
            return IntPtr(999)
        newDgt = PythonMapper.PyType_GenericNew_Delegate(new)
        newFP = Marshal.GetFunctionPointerForDelegate(newDgt)

        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type,
            tp_newPtr=newFP)

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            engine.Execute("t = thing(1, 2, three=4)", module)
            instance = module.Globals['t']

            instancePtr = instance._instancePtr
            self.assertEquals(instancePtr, IntPtr(999),
                              "instance not associated with correct ptr")

            _, argPtr, kwargPtr = calls[0]
            self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference count")
            self.assertEquals(mapper.RefCount(kwargPtr), 1, "bad reference count")
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2), "args not stored")
            self.assertEquals(mapper.Retrieve(kwargPtr), {'three': 4}, "kwargs not stored")
            self.assertEquals(mapper.tempPtrsFreed, True, "failed to clean up")

        finally:
            mapper.DecRef(modulePtr)
            mapper.DecRef(kwargPtr)
            mapper.DecRef(argPtr)
            deallocType()


    def testAddTypeObjectWithVarargsMethod(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        mapper.SetData("PyType_Type", IntPtr(123))
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        retval = mapper.Store("bathroom")
        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            return retval

        method = MakeMethodDef("meth", CMethod, METH.VARARGS)
        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type, methodDef=method,
            tp_allocPtr=mapper.GetAddress("PyType_GenericAlloc"),
            tp_newPtr=mapper.GetAddress("PyType_GenericNew"))

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")
            engine.Execute("t = thing()", module)
            engine.Execute("result = t.meth(1, 2, 3)", module)
            self.assertEquals(mapper.tempPtrsFreed, True, "did not clean up temp ptrs")
            self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
            self.assertEquals(module.Globals['result'], "bathroom",
                              "failed to translate returned ptr")

            self.assertEquals(len(calls), 1, "wrong call count")
            selfPtr, argPtr = calls[0]

            self.assertEquals(mapper.Retrieve(selfPtr), module.Globals['t'],
                              "called with wrong instance")
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                              "called with wrong args")
        finally:
            mapper.DecRef(modulePtr)
            mapper.DecRef(selfPtr)
            mapper.DecRef(argPtr)
            deallocType()


    def testAddTypeObjectWithVarargsKwargsMethod(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        mapper.SetData("PyType_Type", IntPtr(123))
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        retval = mapper.Store("kitchen")
        calls = []
        def CMethod(selfPtr, argPtr, kwargPtr):
            calls.append((selfPtr, argPtr, kwargPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            return retval

        method = MakeMethodDef("meth", CMethod, METH.VARARGS | METH.KEYWORDS)
        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type, methodDef=method,
            tp_allocPtr=mapper.GetAddress("PyType_GenericAlloc"),
            tp_newPtr=mapper.GetAddress("PyType_GenericNew"))

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")
            engine.Execute("t = thing()", module)
            engine.Execute("result = t.meth(1, 2, 3, four=5)", module)
            self.assertEquals(mapper.tempPtrsFreed, True, "did not clean up temp ptrs")
            self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
            self.assertEquals(module.Globals['result'], "kitchen",
                              "failed to translate returned ptr")

            self.assertEquals(len(calls), 1, "wrong call count")
            selfPtr, argPtr, kwargPtr = calls[0]

            self.assertEquals(mapper.Retrieve(selfPtr), module.Globals['t'],
                              "called with wrong instance")
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                              "called with wrong args")
            self.assertEquals(mapper.Retrieve(kwargPtr), {'four': 5},
                              "called with wrong kwargs")
        finally:
            mapper.DecRef(modulePtr)
            mapper.DecRef(selfPtr)
            mapper.DecRef(argPtr)
            mapper.DecRef(kwargPtr)
            deallocType()


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





class Python25Mapper_PyArg_ParseTuple_Test(unittest.TestCase):

    def testPyArg_ParseTupleUsesGetArgValuesAndGetArgWritersAndSetArgValues(self):
        test = self
        argsPtr = IntPtr(123)
        outPtr = IntPtr(159)
        format = "pfhormat"
        argDict = Dictionary[int, object]()
        formatDict = Dictionary[int, ArgWriter]()

        calls = []
        class MyP25M(Python25Mapper):
            def GetArgValues(self, argsPtrIn):
                calls.append("GetArgValues")
                test.assertEquals((argsPtrIn),
                                  (argsPtr),
                                  "wrong params to GetArgValues")
                return argDict

            def GetArgWriters(self, formatIn):
                calls.append("GetArgWriters")
                test.assertEquals(formatIn,
                                  format,
                                  "wrong params to GetArgWriters")
                return formatDict

            def SetArgValues(self, argDictIn, formatDictIn, outPtrIn):
                calls.append("SetArgValues")
                test.assertEquals((argDictIn, formatDictIn, outPtrIn),
                                  (argDict, formatDict, outPtr),
                                  "wrong params to SetArgValues")
                return 1

        mapper = MyP25M(PythonEngine())
        result = mapper.PyArg_ParseTuple(argsPtr, format, outPtr)
        self.assertEquals(result, 1, "should return SetArgValues result")
        self.assertEquals(calls, ["GetArgValues", "GetArgWriters", "SetArgValues"])


    def assertGetArgValuesWorks(self, args, expectedResults):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        # alloc
        argsPtr = mapper.Store(args)
        try:
            # actual test
            results = dict(mapper.GetArgValues(argsPtr))
            self.assertEquals(results, expectedResults, "something, somewhere, broke")
        finally:
            # dealloc
            mapper.DecRef(argsPtr)


    def testGetArgValuesEmpty(self):
        self.assertGetArgValuesWorks(tuple(), {})


    def testGetArgValuesNotEmpty(self):
        args = (1, 2, "buckle my shoe")
        self.assertGetArgValuesWorks(args, dict(enumerate(args)))



class Python25Mapper_PyArg_ParseTupleAndKeywords_Test(unittest.TestCase):

    def testPyArg_ParseTupleAndKeywordsUsesGetArgValuesAndGetArgWritersAndSetArgValues(self):
        test = self
        argsPtr = IntPtr(123)
        kwargsPtr = IntPtr(456)
        kwlistPtr = IntPtr(789)
        outPtr = IntPtr(159)
        format = "pfhormat"
        argDict = Dictionary[int, object]()
        formatDict = Dictionary[int, ArgWriter]()

        calls = []
        class MyP25M(Python25Mapper):
            def GetArgValues(self, argsPtrIn, kwargsPtrIn, kwlistPtrIn):
                calls.append("GetArgValues")
                test.assertEquals((argsPtrIn, kwargsPtrIn, kwlistPtrIn),
                                  (argsPtr, kwargsPtr, kwlistPtr),
                                  "wrong params to GetArgValues")
                return argDict

            def GetArgWriters(self, formatIn):
                calls.append("GetArgWriters")
                test.assertEquals(formatIn,
                                  format,
                                  "wrong params to GetArgWriters")
                return formatDict

            def SetArgValues(self, argDictIn, formatDictIn, outPtrIn):
                calls.append("SetArgValues")
                test.assertEquals((argDictIn, formatDictIn, outPtrIn),
                                  (argDict, formatDict, outPtr),
                                  "wrong params to SetArgValues")
                return 1

        mapper = MyP25M(PythonEngine())
        result = mapper.PyArg_ParseTupleAndKeywords(argsPtr, kwargsPtr, format, kwlistPtr, outPtr)
        self.assertEquals(result, 1, "should return SetArgValues result")
        self.assertEquals(calls, ["GetArgValues", "GetArgWriters", "SetArgValues"])


    def testSetArgValuesStoresArgWriterExceptionAndReturnsZero(self):
        class MockArgWriter(ArgWriter):
            def Write(self, _, __):
                raise System.Exception("gingerly")
        writers = Dictionary[int, ArgWriter]({0: MockArgWriter(0)})
        args = Dictionary[int, object]({0: 0})

        mapper = Python25Mapper(PythonEngine())
        result = mapper.SetArgValues(args, writers, IntPtr.Zero)
        self.assertEquals(result, 0, "wrong failure return")
        exception = mapper.LastException
        self.assertEquals(type(exception), System.Exception, "failed to store")
        self.assertEquals(exception.Message, "gingerly", "failed to store")


    def testSetArgValuesReturnsOneIfNoError(self):
        class MockArgWriter(ArgWriter):
            def Write(self, _, __):
                pass
        writers = Dictionary[int, ArgWriter]({0: MockArgWriter(0)})
        args = Dictionary[int, object]({0: 0})

        mapper = Python25Mapper(PythonEngine())
        result = mapper.SetArgValues(args, writers, IntPtr.Zero)
        self.assertEquals(result, 1, "wrong success return")


    def assertGetArgValuesWorks(self, args, kwargs, kwlist, expectedResults):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        # alloc
        argsPtr = mapper.Store(args)
        kwargsPtr = mapper.Store(kwargs)
        kwlistPtr = Marshal.AllocHGlobal(CPyMarshal.PtrSize * (len(kwlist) + 1))
        current = kwlistPtr
        for s in kwlist:
            addressWritten = Marshal.StringToHGlobalAnsi(s)
            CPyMarshal.WritePtr(current, addressWritten)
            current = IntPtr(current.ToInt32() + CPyMarshal.PtrSize)

        try:
            # actual test
            results = dict(mapper.GetArgValues(argsPtr, kwargsPtr, kwlistPtr))
            self.assertEquals(results, expectedResults, "something, somewhere, broke")
        finally:
            # dealloc
            mapper.DecRef(argsPtr)
            mapper.DecRef(kwargsPtr)
            for i in range(len(kwlist)):
                Marshal.FreeHGlobal(Marshal.ReadIntPtr(IntPtr(kwlistPtr.ToInt32() + (i * CPyMarshal.PtrSize))))
            Marshal.FreeHGlobal(kwlistPtr)


    def testGetArgValuesNone(self):
        args = tuple()
        kwargs = {}
        kwlist = ['one', 'two', 'three']
        expectedResults = {}

        self.assertGetArgValuesWorks(
            args, kwargs, kwlist, expectedResults)


    def testGetArgValuesArgsOnly(self):
        args = ('a', 'b', 'c')
        kwargs = {}
        kwlist = ['one', 'two', 'three']
        expectedResults = {0:'a', 1:'b', 2:'c'}

        self.assertGetArgValuesWorks(
            args, kwargs, kwlist, expectedResults)


    def testGetArgValuesSingleKwarg(self):
        args = ()
        kwargs = {'two': 'b'}
        kwlist = ['one', 'two', 'three']
        expectedResults = {1:'b'}

        self.assertGetArgValuesWorks(
            args, kwargs, kwlist, expectedResults)


    def testGetArgValuesKwargsOnly(self):
        args = ()
        kwargs = {'one': 'c', 'two': 'b', 'three': 'a'}
        kwlist = ['one', 'two', 'three']
        expectedResults = {0:'c', 1:'b', 2:'a'}

        self.assertGetArgValuesWorks(
            args, kwargs, kwlist, expectedResults)


    def testGetArgValuesMixture(self):
        args = ('a',)
        kwargs = {'three': 'c'}
        kwlist = ['one', 'two', 'three']
        expectedResults = {0:'a', 2:'c'}

        self.assertGetArgValuesWorks(
            args, kwargs, kwlist, expectedResults)


    def assertGetArgWritersProduces(self, format, expected):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        result = dict(mapper.GetArgWriters(format))
        self.assertEquals(len(result), len(expected), "wrong size")
        for (i, _type, nextStartIndex) in expected:
            writer = result[i]
            self.assertEquals(type(writer), _type,
                              "wrong writer type")
            self.assertEquals(writer.NextWriterStartIndex, nextStartIndex,
                              "writers set to access wrong memory")


    def testGetArgWritersWorks(self):
        self.assertGetArgWritersProduces("i", [(0, IntArgWriter, 1)])
        self.assertGetArgWritersProduces("i:someName", [(0, IntArgWriter, 1)])
        self.assertGetArgWritersProduces("iii", [(0, IntArgWriter, 1),
                                                 (1, IntArgWriter, 2),
                                                 (2, IntArgWriter, 3),])
        self.assertGetArgWritersProduces("ii|i", [(0, IntArgWriter, 1),
                                                  (1, IntArgWriter, 2),
                                                  (2, IntArgWriter, 3),])

        self.assertGetArgWritersProduces("s#", [(0, SizedStringArgWriter, 2)])
        self.assertGetArgWritersProduces("s#i", [(0, SizedStringArgWriter, 2),
                                                 (1, IntArgWriter, 3)])
        self.assertGetArgWritersProduces("|s#i", [(0, SizedStringArgWriter, 2),
                                                  (1, IntArgWriter, 3)])

    def testUnrecognisedFormatString(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        self.assertRaises(NotImplementedError, lambda: mapper.GetArgWriters("arsiuhgiurshgRHALI"))


    def testSetArgValuesUsesParamsToWriteAppropriateData(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        expectedPtrTable = IntPtr(5268)

        test = self
        class MockArgWriter(ArgWriter):
            def __init__(self, expectedValue):
                self.called = False
                self.expectedValue = expectedValue
            def Write(self, ptrTable, value):
                self.called = True
                test.assertEquals(value, self.expectedValue, "Wrote wrong value")
                test.assertEquals(ptrTable, expectedPtrTable, "Wrote to wrong location")

        argsToWrite = Dictionary[int, object]({0: 14, 2: 39})
        argWriters = Dictionary[int, ArgWriter]({0: MockArgWriter(14),
                                                 1: MockArgWriter(-1),
                                                 2: MockArgWriter(39)})

        mapper.SetArgValues(argsToWrite, argWriters, expectedPtrTable)
        for i, writer in dict(argWriters).items():
            if i in argsToWrite:
                self.assertTrue(writer.called, "failed to write")
            else:
                self.assertFalse(writer.called, "wrote inappropriately")


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
    Python25Mapper_Py_InitModule4_Test,
    Python25Mapper_PyModule_AddObject_Test,
    Python25Mapper_PyType_GenericNew_Test,
    Python25Mapper_PyType_GenericAlloc_Test,
    Python25Mapper_PyArg_ParseTuple_Test,
    Python25Mapper_PyArg_ParseTupleAndKeywords_Test,
    Python25Mapper_Exception_Test,
)

if __name__ == '__main__':
    run(suite)