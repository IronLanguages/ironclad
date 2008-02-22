
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeMethodDef, MakeSingleMethodTablePtr, MakeTypePtr
from tests.utils.memory import OffsetPtr
from tests.utils.python25mapper import TempPtrCheckingPython25Mapper, MakeAndAddEmptyModule

import System
from System import Array, IntPtr
from System.Reflection import BindingFlags
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, CPython_initproc_Delegate, PythonMapper, Python25Mapper
from Ironclad.Structs import METH, PyMethodDef, PyObject
from IronPython.Hosting import PythonEngine


def PythonModuleFromEngineModule(engineModule):
    engineModuleType = engineModule.GetType()
    pythonModuleInfo = engineModuleType.GetMember("Module",
        BindingFlags.NonPublic | BindingFlags.Instance)[0]
    return pythonModuleInfo.GetValue(engineModule, Array[object]([]))


class BorkedException(System.Exception):
    pass


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
            mapper.FreeTemps()


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


    def test_Py_InitModule4_DispatchesToOriginalNoArgsFunction(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        retval = mapper.Store("ewok")
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            return retval
        method = MakeMethodDef("func", CModuleFunction, METH.NOARGS)

        def testModule(test_module, mapper):
            self.assertEquals(test_module.func(), "ewok", "bad result")
            self.assertEquals(len(calls), 1, "wrong call count")
            _selfPtr, argPtr = calls[0]

            self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
            self.assertTrue(mapper.tempPtrsFreed, "failed to clean up after call")
            self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")
            self.assertEquals(argPtr, IntPtr.Zero, "no args on noargs functions (oddly enough)")

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_DispatchesToOriginalSingleArgFunction(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        retval = mapper.Store("ewok")
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.IncRef(argPtr)
            return retval
        method = MakeMethodDef("func", CModuleFunction, METH.O)

        def testModule(test_module, mapper):
            try:
                self.assertEquals(test_module.func(37), "ewok", "bad result")
                self.assertEquals(len(calls), 1, "wrong call count")
                _selfPtr, argPtr = calls[0]

                self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up after call")
                self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")

                # CModuleFunction retained a reference, so we could test the aftermath
                self.assertEquals(mapper.Retrieve(argPtr), 37,
                                  "did not pass pointer mapping to actual arg")

                self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference counting")
            finally:
                mapper.DecRef(argPtr)

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
                self.assertEquals(len(calls), 1, "wrong call count")
                _selfPtr, argPtr = calls[0]

                self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up after call")
                self.assertEquals(_selfPtr, IntPtr.Zero, "no self on module functions")

                # CModuleFunction retained a reference, so we could test the aftermath
                self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                                  "did not pass pointer mapping to correct tuple")

                self.assertEquals(mapper.RefCount(argPtr), 1, "bad reference counting")
            finally:
                mapper.DecRef(argPtr)

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
                self.assertEquals(len(calls), 1, "wrong call count")
                _selfPtr, argPtr, kwargPtr = calls[0]

                self.assertEquals(mapper.RefCount(retval), 0, "did not clean up return value")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up after call")
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


    def test_Py_InitModule4_NoArgsFunctionRaisesAppropriateException(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        method = MakeMethodDef("func", CModuleFunction, METH.NOARGS)

        def testModule(test_module, mapper):
            self.assertRaises(BorkedException, test_module.func)
            self.assertEquals(len(calls), 1, "wrong call count")
            _selfPtr, argPtr = calls[0]

            self.assertEquals(_selfPtr, IntPtr.Zero, "should pass null instance to function")
            self.assertEquals(argPtr, IntPtr.Zero, "should pass null to noargs function")
            self.assertTrue(mapper.tempPtrsFreed, "failed to clean up temp ptrs on error")
            self.assertEquals(mapper.LastException, None, "exception not cleared when raised")

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_SingleArgFunctionRaisesAppropriateException(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.IncRef(argPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        method = MakeMethodDef("func", CModuleFunction, METH.O)

        def testModule(test_module, mapper):
            self.assertRaises(BorkedException, lambda: test_module.func(37))
            self.assertEquals(len(calls), 1, "wrong call count")
            _selfPtr, argPtr = calls[0]

            self.assertEquals(_selfPtr, IntPtr.Zero, "should pass null instance to function")
            self.assertEquals(mapper.RefCount(argPtr), 1, "did not clean up")
            self.assertTrue(mapper.tempPtrsFreed, "failed to clean up temp ptrs on error")
            self.assertEquals(mapper.LastException, None, "exception not cleared when raised")

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_VarargsFunctionRaisesAppropriateException(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.IncRef(argPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        method = MakeMethodDef("func", CModuleFunction, METH.VARARGS)

        def testModule(test_module, mapper):
            try:
                self.assertRaises(BorkedException, test_module.func, (1, 2, 3))
                self.assertEquals(len(calls), 1, "wrong call count")
                _selfPtr, argPtr = calls[0]

                self.assertEquals(_selfPtr, IntPtr.Zero, "should pass null instance to function")
                self.assertEquals(mapper.RefCount(argPtr), 1, "failed to DecRef argPtr on error")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up temp ptrs on error")
                self.assertEquals(mapper.LastException, None, "exception not cleared when raised")
            finally:
                mapper.DecRef(argPtr)

        self.assert_Py_InitModule4_withSingleMethod(engine, mapper, method, testModule)


    def test_Py_InitModule4_VarargsKwargsFunctionRaisesAppropriateException(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)
        calls = []
        def CModuleFunction(_selfPtr, argPtr, kwargPtr):
            calls.append((_selfPtr, argPtr, kwargPtr))
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        method = MakeMethodDef("func", CModuleFunction, METH.VARARGS | METH.KEYWORDS)

        def testModule(test_module, mapper):
            try:
                self.assertRaises(BorkedException, lambda: test_module.func(1, 2, 3, four=5))
                self.assertEquals(len(calls), 1, "wrong call count")
                _selfPtr, argPtr, kwargPtr = calls[0]

                self.assertEquals(_selfPtr, IntPtr.Zero, "should pass null instance to function")
                self.assertEquals(mapper.RefCount(argPtr), 1, "failed to DecRef argPtr on error")
                self.assertEquals(mapper.RefCount(kwargPtr), 1, "failed to DecRef kwargPtr on error")
                self.assertTrue(mapper.tempPtrsFreed, "failed to clean up temp ptrs on error")
                self.assertEquals(mapper.LastException, None, "exception not cleared when raised")
            finally:
                mapper.DecRef(argPtr)
                mapper.DecRef(kwargPtr)

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
            calls.append("__new__")
            return IntPtr.Zero
        newDgt = PythonMapper.PyType_GenericNew_Delegate(new)
        newFP = Marshal.GetFunctionPointerForDelegate(newDgt)

        def init(_, __, ___):
            calls.append("__init__")
            return 0
        initDgt = CPython_initproc_Delegate(init)
        initFP = Marshal.GetFunctionPointerForDelegate(initDgt)

        typePtr, deallocType = MakeTypePtr(
            tp_name, mapper.PyType_Type, tp_newPtr=newFP, tp_initPtr=initFP)
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
            mappedClass._tp_initDgt(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
            self.assertEquals(calls, ["__new__", "__init__"],
                              "tp_new and tp_init not hooked up correctly")
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
            calls.append(("__new__", typePtr, argPtr, kwargPtr))
            return IntPtr(999)
        newDgt = PythonMapper.PyType_GenericNew_Delegate(new)
        newFP = Marshal.GetFunctionPointerForDelegate(newDgt)

        def init(selfPtr, argPtr, kwargPtr):
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            calls.append(("__init__", selfPtr, argPtr, kwargPtr))
            return 0
        initDgt = CPython_initproc_Delegate(init)
        initFP = Marshal.GetFunctionPointerForDelegate(initDgt)

        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type,
            tp_newPtr=newFP, tp_initPtr = initFP)

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            engine.Execute("t = thing(1, 2, three=4)", module)
            instance = module.Globals['t']

            instancePtr = instance._instancePtr
            self.assertEquals(instancePtr, IntPtr(999),
                              "instance not associated with correct ptr")

            methodName, newClsPtr, newArgPtr, newKwargPtr = calls[0]
            self.assertEquals(methodName, "__new__", "called wrong method")
            self.assertEquals(newClsPtr, typePtr, "instantiated wrong class")
            self.assertEquals(mapper.RefCount(newArgPtr), 1, "bad reference count")
            self.assertEquals(mapper.RefCount(newKwargPtr), 1, "bad reference count")
            self.assertEquals(mapper.Retrieve(newArgPtr), (1, 2), "args not stored")
            self.assertEquals(mapper.Retrieve(newKwargPtr), {'three': 4}, "kwargs not stored")
            self.assertEquals(mapper.tempPtrsFreed, True, "failed to clean up")

            # note: for now, I'm comfortable passing 2 copies of the
            # args and kwargs to the 2 methods; this may change in future
            methodName, initSelfPtr, initArgPtr, initKwargPtr = calls[1]
            self.assertEquals(methodName, "__init__", "called wrong method")
            self.assertEquals(initSelfPtr, instancePtr, "initialised wrong object")
            self.assertEquals(mapper.RefCount(initArgPtr), 1, "bad reference count")
            self.assertEquals(mapper.RefCount(initKwargPtr), 1, "bad reference count")
            self.assertEquals(mapper.Retrieve(initArgPtr), (1, 2), "args not stored")
            self.assertEquals(mapper.Retrieve(initKwargPtr), {'three': 4}, "kwargs not stored")
            self.assertEquals(mapper.tempPtrsFreed, True, "failed to clean up")

        finally:
            mapper.DecRef(modulePtr)
            mapper.DecRef(newKwargPtr)
            mapper.DecRef(newArgPtr)
            mapper.DecRef(initKwargPtr)
            mapper.DecRef(initArgPtr)
            deallocType()


    def assertDispatchesToTypeMethod(self, engine, mapper, method, flags,
                                     argString, retvalPtr, testArgs):
        mapper.SetData("PyType_Type", IntPtr(123))
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        retval = mapper.Retrieve(retvalPtr)

        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type,
            methodDef=MakeMethodDef("meth", method, flags),
            tp_allocPtr=mapper.GetAddress("PyType_GenericAlloc"),
            tp_newPtr=mapper.GetAddress("PyType_GenericNew"))

        callArgs = tuple()
        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            engine.Execute("t = thing()", module)
            engine.Execute("x = t.meth(%s)" % argString, module)

            self.assertEquals(len(method.calls), 1, "wrong call count")
            callArgs = method.calls[0]
            self.assertEquals(mapper.Retrieve(callArgs[0]), module.Globals['t'],
                              "called with wrong instance")
            testArgs(*callArgs[1:])

            self.assertEquals(mapper.tempPtrsFreed, True, "did not clean up temp ptrs")
            self.assertEquals(mapper.RefCount(retvalPtr), 0, "did not clean up return value")
            self.assertEquals(module.Globals['x'], retval,
                              "failed to translate returned ptr")
        finally:
            mapper.DecRef(modulePtr)
            deallocType()
            for arg in callArgs:
                if arg != IntPtr.Zero:
                    mapper.DecRef(arg)


    def testAddTypeObjectWithNoArgsMethod(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        retvalPtr = mapper.Store("cellar")
        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            return retvalPtr
        CMethod.calls = calls

        def testFunc(argPtr):
            self.assertEquals(argPtr, IntPtr.Zero,
                              "called with wrong args")

        self.assertDispatchesToTypeMethod(
            engine, mapper, CMethod, METH.NOARGS,
            "", retvalPtr, testFunc)


    def testAddTypeObjectWithSingleObjectArgMethod(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        retvalPtr = mapper.Store("larder")
        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            return retvalPtr
        CMethod.calls = calls

        def testFunc(argPtr):
            self.assertEquals(mapper.Retrieve(argPtr), 99,
                              "called with wrong args")
            self.assertEquals(mapper.RefCount(argPtr), 1,
                              "failed to clean up")

        self.assertDispatchesToTypeMethod(
            engine, mapper, CMethod, METH.O,
            "99", retvalPtr, testFunc)


    def testAddTypeObjectWithVarargsMethod(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        retvalPtr = mapper.Store("bathroom")
        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            return retvalPtr
        CMethod.calls = calls

        def testFunc(argPtr):
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                              "called with wrong args")
            self.assertEquals(mapper.RefCount(argPtr), 1,
                              "failed to clean up")

        self.assertDispatchesToTypeMethod(
            engine, mapper, CMethod, METH.VARARGS,
            "1, 2, 3", retvalPtr, testFunc)


    def testAddTypeObjectWithVarargsKwargsMethod(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        retvalPtr = mapper.Store("kitchen")
        calls = []
        def CMethod(selfPtr, argPtr, kwargPtr):
            calls.append((selfPtr, argPtr, kwargPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            return retvalPtr
        CMethod.calls = calls

        def testFunc(argPtr, kwargPtr):
            self.assertEquals(mapper.Retrieve(argPtr), (1, 2, 3),
                              "called with wrong args")
            self.assertEquals(mapper.Retrieve(kwargPtr), {'four': 5},
                              "called with wrong kwargs")
            self.assertEquals(mapper.RefCount(argPtr), 1,
                              "failed to clean up")
            self.assertEquals(mapper.RefCount(kwargPtr), 1,
                              "failed to clean up")

        self.assertDispatchesToTypeMethod(
            engine, mapper, CMethod, METH.VARARGS | METH.KEYWORDS,
            "1, 2, 3, four=5", retvalPtr, testFunc)


    def assertDispatchesToTypeMethodAndHandlesException(self, engine, mapper, method, flags,
                                                        argString, exceptionType, testArgs):
        mapper.SetData("PyType_Type", IntPtr(123))
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type,
            methodDef=MakeMethodDef("meth", method, flags),
            tp_allocPtr=mapper.GetAddress("PyType_GenericAlloc"),
            tp_newPtr=mapper.GetAddress("PyType_GenericNew"))

        callArgs = tuple()
        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            engine.Execute("t = thing()", module)
            self.assertRaises(exceptionType,
                              lambda: engine.Execute("x = t.meth(%s)" % argString, module))

            self.assertEquals(len(method.calls), 1, "wrong call count")
            callArgs = method.calls[0]
            self.assertEquals(mapper.Retrieve(callArgs[0]), module.Globals['t'],
                              "called with wrong instance")
            testArgs(*callArgs[1:])

            self.assertEquals(mapper.tempPtrsFreed, True, "did not clean up temp ptrs")
        finally:
            mapper.DecRef(modulePtr)
            deallocType()
            for arg in callArgs:
                if arg != IntPtr.Zero:
                    mapper.DecRef(arg)


    def testAddTypeObjectWithNoArgsMethodRaisingError(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        CMethod.calls = calls

        self.assertDispatchesToTypeMethodAndHandlesException(
            engine, mapper, CMethod, METH.NOARGS,
            "", BorkedException, lambda _:None)


    def testAddTypeObjectWithSingleObjectArgMethodRaisingError(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        CMethod.calls = calls

        def testFunc(argPtr):
            self.assertEquals(mapper.RefCount(argPtr), 1,
                              "failed to clean up")

        self.assertDispatchesToTypeMethodAndHandlesException(
            engine, mapper, CMethod, METH.O,
            "99", BorkedException, testFunc)


    def testAddTypeObjectWithVarargsMethodRaisingError(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        calls = []
        def CMethod(selfPtr, argPtr):
            calls.append((selfPtr, argPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        CMethod.calls = calls

        def testFunc(argPtr):
            self.assertEquals(mapper.RefCount(argPtr), 1,
                              "failed to clean up")

        self.assertDispatchesToTypeMethodAndHandlesException(
            engine, mapper, CMethod, METH.VARARGS,
            "1, 2, 3", BorkedException, testFunc)


    def testAddTypeObjectWithVarargsKwargsMethodRaisingError(self):
        engine = PythonEngine()
        mapper = TempPtrCheckingPython25Mapper(engine)

        calls = []
        def CMethod(selfPtr, argPtr, kwargPtr):
            calls.append((selfPtr, argPtr, kwargPtr))
            mapper.IncRef(selfPtr)
            mapper.IncRef(argPtr)
            mapper.IncRef(kwargPtr)
            mapper.LastException = BorkedException()
            return IntPtr.Zero
        CMethod.calls = calls

        def testFunc(argPtr, kwargPtr):
            self.assertEquals(mapper.RefCount(argPtr), 1,
                              "failed to clean up")
            self.assertEquals(mapper.RefCount(kwargPtr), 1,
                              "failed to clean up")

        self.assertDispatchesToTypeMethodAndHandlesException(
            engine, mapper, CMethod, METH.VARARGS | METH.KEYWORDS,
            "1, 2, 3, four=5", BorkedException, testFunc)


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


suite = makesuite(
    Python25Mapper_Py_InitModule4_Test,
    Python25Mapper_PyModule_AddObject_Test,
    Python25Mapper_PyType_GenericNew_Test,
    Python25Mapper_PyType_GenericAlloc_Test,
)

if __name__ == '__main__':
    run(suite)