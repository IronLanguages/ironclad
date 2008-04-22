
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeMethodDef, MakeSingleMethodTablePtr, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import TempPtrCheckingPython25Mapper, MakeAndAddEmptyModule

import System
from System import IntPtr, NullReferenceException
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    CPython_initproc_Delegate, CPythonSelfFunction_Delegate, CPythonVarargsFunction_Delegate, 
    CPythonVarargsKwargsFunction_Delegate, PythonMapper, Python25Mapper
)
from Ironclad.Structs import METH, Py_TPFLAGS, PyMethodDef

from TestUtils import ExecUtils

class BorkedException(System.Exception):
    pass


class ObjectWithLength(object):
    def __init__(self, length):
        self.length = length
    def __len__(self):
        return self.length


class ModuleWrapper(object):
    def __init__(self, engine, module):
        self.moduleScope = engine.CreateScope(module.Scope.Dict)
    def __getattr__(self, name):
        return self.moduleScope.GetVariable[object](name)
    def __setattr__(self, name, value):
        if name == 'moduleScope':
            self.__dict__['moduleScope'] = value
            return
        self.moduleScope.SetVariable(name, value)


INSTANCE_PTR = IntPtr(111)
ARGS_PTR = IntPtr(222)
KWARGS_PTR = IntPtr(333)
EMPTY_KWARGS_PTR = IntPtr.Zero
RESULT_PTR = IntPtr(999)
ERROR_RESULT_PTR = IntPtr.Zero


Null_CPythonVarargsFunction = lambda _, __: IntPtr.Zero
Null_CPythonVarargsKwargsFunction = lambda _, __, ___: IntPtr.Zero


class EmptyModuleTestCase(unittest.TestCase):
    
    def setUp(self):
        self.mapper = TempPtrCheckingPython25Mapper()
        self.modulePtr = MakeAndAddEmptyModule(self.mapper)
        self.module = ModuleWrapper(self.mapper.Engine, self.mapper.Retrieve(self.modulePtr))
        
        
    def tearDown(self):
        self.mapper.DecRef(self.modulePtr)
        self.mapper.FreeTemps()
    

class Python25Mapper_PyInitModule_DispatchUtilsTest(EmptyModuleTestCase):
        
    def assertCleanupWorks(self, args, decrefs):
        decreffed = []
        self.mapper.DecRef = decreffed.append
        self.mapper.tempPtrsFreed = False
        self.module._cleanup(*args)
        self.assertEquals(decreffed, decrefs, "wrong")
        self.assertEquals(self.mapper.tempPtrsFreed, True, "failed to free temps")
        

    def testCleanup(self):
        self.assertCleanupWorks((IntPtr(0), ), [])
        self.assertCleanupWorks((IntPtr(1), IntPtr(2), IntPtr(3)), [IntPtr(1), IntPtr(2), IntPtr(3)])
        self.assertCleanupWorks((IntPtr(1), IntPtr(0), IntPtr(3)), [IntPtr(1), IntPtr(3)])


    def testRaiseExceptionIfRequired(self):
        self.module._raiseExceptionIfRequired(IntPtr(12345))
        
        self.assertRaises(NullReferenceException, self.module._raiseExceptionIfRequired, IntPtr(0))
        
        self.mapper.LastException = BorkedException()
        self.assertRaises(BorkedException, self.module._raiseExceptionIfRequired, IntPtr(12345))
        self.assertEquals(self.mapper.LastException, None, 'did not reset exception when raised')


class Python25Mapper_PyInitModule_DispatchFunctionsTest(EmptyModuleTestCase):

    def patchUtilities(self, shouldRaise):
        calls = []
        self.module._cleanup = lambda *args: calls.append(("_cleanup", args))
        def _raise(resultPtr):
            calls.append(("_raiseExc", resultPtr))
            raise BorkedException()
        def _dontRaise(resultPtr):
            calls.append(("_raiseExc", resultPtr))
        if shouldRaise:
            self.module._raiseExceptionIfRequired = _raise
        else:
            self.module._raiseExceptionIfRequired = _dontRaise
        return calls
        

    def testDispatchVarArgsOrObjArgs(self):
        actualCalls = self.patchUtilities(False)
        
        def testFunc(selfPtr, argsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass instancePtr")
            self.assertEquals(argsPtr, ARGS_PTR, "failed to pass argsPtr")
            return RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsFunction_Delegate(testFunc)
        
        expectedResult = object()
        def checkResult(resultPtr):
            actualCalls.append("Retrieve")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
            return expectedResult
        self.mapper.Retrieve = checkResult
        
        actualArgs = object()
        def storeArgs(args):
            actualCalls.append("Store")
            self.assertEquals(args, actualArgs)
            return ARGS_PTR
        self.mapper.Store = storeArgs
        
        actualResult = self.module._ironclad_dispatch("testFuncName", INSTANCE_PTR, actualArgs)
        self.assertEquals(actualResult, expectedResult, "bad result")
        
        expectedCalls = ["Store", "testFunc", ("_raiseExc", RESULT_PTR), "Retrieve", ("_cleanup", (ARGS_PTR, RESULT_PTR))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        

    def testDispatchVarArgsOrObjArgsWithError(self):
        actualCalls = self.patchUtilities(True)
        
        def testFunc(selfPtr, argsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass instancePtr")
            self.assertEquals(argsPtr, ARGS_PTR, "failed to pass argsPtr")
            return ERROR_RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsFunction_Delegate(testFunc)
        self.mapper.Retrieve = lambda _: self.fail("no need to get result if exception raised")
        
        actualArgs = object()
        def storeArgs(args):
            actualCalls.append("Store")
            self.assertEquals(args, actualArgs)
            return ARGS_PTR
        self.mapper.Store = storeArgs
        
        self.assertRaises(BorkedException, 
            lambda: self.module._ironclad_dispatch("testFuncName", INSTANCE_PTR, actualArgs))
        expectedCalls = ["Store", "testFunc", ("_raiseExc", ERROR_RESULT_PTR), ("_cleanup", (ARGS_PTR, ERROR_RESULT_PTR))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        
        
    def testDispatchSelf(self):
        actualCalls = self.patchUtilities(False)
        
        def testFunc(selfPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass")
            return RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonSelfFunction_Delegate(testFunc)
        
        expectedResult = object()
        def checkResult(resultPtr):
            actualCalls.append("Retrieve")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
            return expectedResult
        self.mapper.Retrieve = checkResult
        
        def errorHandler(resultPtr):
            actualCalls.append("HandleError")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
        
        # test with error handler
        actualResult = self.module._ironclad_dispatch_self("testFuncName", INSTANCE_PTR, errorHandler)
        self.assertEquals(actualResult, expectedResult, "bad result")
        
        expectedCalls = ["testFunc", "HandleError", ("_raiseExc", RESULT_PTR), "Retrieve", ("_cleanup", (RESULT_PTR, ))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        
        # test without
        del actualCalls[:]
        self.module._ironclad_dispatch_self("testFuncName", INSTANCE_PTR)
        self.assertEquals(actualResult, expectedResult, "bad result")
        
        expectedCalls = ["testFunc", ("_raiseExc", RESULT_PTR), "Retrieve", ("_cleanup", (RESULT_PTR, ))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        
        
    def testDispatchSelfWithError(self):
        actualCalls = self.patchUtilities(True)
        
        def testFunc(selfPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass")
            return RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonSelfFunction_Delegate(testFunc)
        
        expectedResult = object()
        def checkResult(resultPtr):
            actualCalls.append("Retrieve")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
            return expectedResult
        self.mapper.Retrieve = checkResult
        
        def errorHandler(resultPtr):
            actualCalls.append("HandleError")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
        
        # test with error handler
        self.assertRaises(BorkedException, 
            lambda: self.module._ironclad_dispatch_self("testFuncName", INSTANCE_PTR, errorHandler))
        
        expectedCalls = ["testFunc", "HandleError", ("_raiseExc", RESULT_PTR), ("_cleanup", (RESULT_PTR, ))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        
        # test without
        del actualCalls[:]
        self.assertRaises(BorkedException, 
            lambda: self.module._ironclad_dispatch_self("testFuncName", INSTANCE_PTR))
        
        expectedCalls = ["testFunc", ("_raiseExc", RESULT_PTR), ("_cleanup", (RESULT_PTR, ))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        
        

    def testDispatchNoargs(self):
        actualCalls = self.patchUtilities(False)
        
        def testFunc(selfPtr, argsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass")
            self.assertEquals(argsPtr, IntPtr.Zero, "NOARGS callable should pass null for args")
            return RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsFunction_Delegate(testFunc)
        
        expectedResult = object()
        def checkResult(resultPtr):
            actualCalls.append("Retrieve")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
            return expectedResult
        self.mapper.Retrieve = checkResult
        
        actualResult = self.module._ironclad_dispatch_noargs("testFuncName", INSTANCE_PTR)
        self.assertEquals(actualResult, expectedResult, "bad result")
        
        expectedCalls = ["testFunc", ("_raiseExc", RESULT_PTR), "Retrieve", ("_cleanup", (RESULT_PTR, ))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        

    def testDispatchNoargsWithError(self):
        actualCalls = self.patchUtilities(True)
        
        def testFunc(selfPtr, argsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass instancePtr")
            self.assertEquals(argsPtr, IntPtr.Zero, "NOARGS callable should pass null for args")
            return ERROR_RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsFunction_Delegate(testFunc)
        self.mapper.Retrieve = lambda _: self.fail("no need to get result if exception raised")
        
        self.assertRaises(BorkedException, 
            lambda: self.module._ironclad_dispatch_noargs("testFuncName", INSTANCE_PTR))
        expectedCalls = ["testFunc", ("_raiseExc", ERROR_RESULT_PTR), ("_cleanup", (ERROR_RESULT_PTR, ))]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        

    def testDispatchVarArgsKwargs(self):
        actualCalls = self.patchUtilities(False)
        
        def testFunc(selfPtr, argsPtr, kwargsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass instancePtr")
            self.assertEquals(argsPtr, ARGS_PTR, "failed to pass argsPtr")
            self.assertEquals(kwargsPtr, KWARGS_PTR, "failed to pass kwargsPtr")
            return RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsKwargsFunction_Delegate(testFunc)
        
        expectedResult = object()
        def checkResult(resultPtr):
            actualCalls.append("Retrieve")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
            return expectedResult
        self.mapper.Retrieve = checkResult
        
        actualArgs = object()
        actualKwargs = ObjectWithLength(1)
        def storeArgs(args):
            if args == actualArgs:
                actualCalls.append("Store args")
                self.assertEquals(args, actualArgs)
                return ARGS_PTR
            elif args == actualKwargs:
                actualCalls.append("Store kwargs")
                self.assertEquals(args, actualKwargs)
                return KWARGS_PTR
            else:
                self.fail("stored unexpected object")
        self.mapper.Store = storeArgs
        
        actualResult = self.module._ironclad_dispatch_kwargs("testFuncName", INSTANCE_PTR, actualArgs, actualKwargs)
        self.assertEquals(actualResult, expectedResult, "bad result")
        
        expectedCalls = [
            "Store args", "Store kwargs", "testFunc", 
            ("_raiseExc", RESULT_PTR), 
            "Retrieve", 
            ("_cleanup", (ARGS_PTR, KWARGS_PTR, RESULT_PTR))
        ]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        

    def testDispatchVarArgsKwargsWithEmptyKwargs(self):
        actualCalls = self.patchUtilities(False)
        
        def testFunc(selfPtr, argsPtr, kwargsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass instancePtr")
            self.assertEquals(argsPtr, ARGS_PTR, "failed to pass argsPtr")
            self.assertEquals(kwargsPtr, EMPTY_KWARGS_PTR, "failed to pass kwargsPtr")
            return RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsKwargsFunction_Delegate(testFunc)
        
        expectedResult = object()
        def checkResult(resultPtr):
            actualCalls.append("Retrieve")
            self.assertEquals(resultPtr, RESULT_PTR, "got bad result pointer")
            return expectedResult
        self.mapper.Retrieve = checkResult
        
        actualArgs = object()
        actualKwargs = ObjectWithLength(0)
        def storeArgs(args):
            if args == actualArgs:
                actualCalls.append("Store args")
                self.assertEquals(args, actualArgs)
                return ARGS_PTR
            else:
                self.fail("stored unexpected object")
        self.mapper.Store = storeArgs
        
        actualResult = self.module._ironclad_dispatch_kwargs("testFuncName", INSTANCE_PTR, actualArgs, actualKwargs)
        self.assertEquals(actualResult, expectedResult, "bad result")
        
        expectedCalls = [
            "Store args", "testFunc", 
            ("_raiseExc", RESULT_PTR), 
            "Retrieve", 
            ("_cleanup", (ARGS_PTR, EMPTY_KWARGS_PTR, RESULT_PTR))
        ]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")
        

    def testDispatchVarArgsKwargsWithError(self):
        actualCalls = self.patchUtilities(True)
        
        def testFunc(selfPtr, argsPtr, kwargsPtr):
            actualCalls.append("testFunc")
            self.assertEquals(selfPtr, INSTANCE_PTR, "failed to pass instancePtr")
            self.assertEquals(argsPtr, ARGS_PTR, "failed to pass argsPtr")
            self.assertEquals(kwargsPtr, KWARGS_PTR, "failed to pass kwargsPtr")
            return ERROR_RESULT_PTR
        self.module._ironclad_dispatch_table["testFuncName"] = CPythonVarargsKwargsFunction_Delegate(testFunc)
        self.mapper.Retrieve = lambda _: self.fail("no need to get result if exception raised")
        
        actualArgs = object()
        actualKwargs = ObjectWithLength(1)
        def storeArgs(args):
            if args == actualArgs:
                actualCalls.append("Store args")
                self.assertEquals(args, actualArgs)
                return ARGS_PTR
            elif args == actualKwargs:
                actualCalls.append("Store kwargs")
                self.assertEquals(args, actualKwargs)
                return KWARGS_PTR
            else:
                self.fail("stored unexpected object")
        self.mapper.Store = storeArgs
        
        self.assertRaises(BorkedException, 
            lambda: self.module._ironclad_dispatch_kwargs("testFuncName", INSTANCE_PTR, actualArgs, actualKwargs))
        expectedCalls = [
            "Store args", "Store kwargs", "testFunc", 
            ("_raiseExc", ERROR_RESULT_PTR), 
            ("_cleanup", (ARGS_PTR, KWARGS_PTR, ERROR_RESULT_PTR))
        ]
        self.assertEquals(actualCalls, expectedCalls, "bad call sequence")



class Python25Mapper_Py_InitModule4_Test(unittest.TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, mapper, methodDef, moduleTest):
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

            module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
            test_module = ExecUtils.GetPythonModule(mapper.Engine, 'test_module')
            
            for item in dir(test_module):
                # ModuleWrapper.__doc__ will hide underlying module.__doc__ if we just use plain getattr
                self.assertEquals(ModuleWrapper.__getattr__(module, item) is getattr(test_module, item),
                                  True, "%s didn't match" % item)
            moduleTest(test_module, mapper)
        finally:
            deallocMethods()
            mapper.FreeTemps()
            mapper.DecRef(modulePtr)


    def test_Py_InitModule4_CreatesPopulatedModuleInSys(self):
        mapper = Python25Mapper()
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

        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)


    def test_Py_InitModule4_NoArgsFunctionDispatch(self):
        mapper = Python25Mapper()
        method = MakeMethodDef("func", Null_CPythonVarargsFunction, METH.NOARGS)
        
        def testModule(module, mapper):
            result = object()
            def dispatch_noargs(name, _selfPtr):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(_selfPtr, IntPtr.Zero, "instance should be null for function")
                return result
            module._ironclad_dispatch_noargs = dispatch_noargs
            self.assertEquals(module.func(), result, "didn't use _ironclad_dispatch_noargs")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)


    def test_Py_InitModule4_SingleArgFunctionDispatch(self):
        mapper = TempPtrCheckingPython25Mapper()
        method = MakeMethodDef("func", Null_CPythonVarargsFunction, METH.O)
        
        def testModule(module, mapper):
            result = object()
            actualArg = object()
            def dispatch(name, _selfPtr, arg):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(_selfPtr, IntPtr.Zero, "instance should be null for function")
                self.assertEquals(arg, actualArg, "didn't pass arg")
                return result
            module._ironclad_dispatch = dispatch
            self.assertEquals(module.func(actualArg), result, "didn't use _ironclad_dispatch")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)


    def test_Py_InitModule4_VarargsFunctionDispatch(self):
        mapper = TempPtrCheckingPython25Mapper()
        method = MakeMethodDef("func", Null_CPythonVarargsFunction, METH.VARARGS)
        
        def testModule(module, mapper):
            result = object()
            actualArgs = (1, "2", "buckle")
            def dispatch(name, _selfPtr, args):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(_selfPtr, IntPtr.Zero, "instance should be null for function")
                self.assertEquals(args, actualArgs, "didn't pass args")
                return result
            module._ironclad_dispatch = dispatch
            self.assertEquals(module.func(*actualArgs), result, "didn't use _ironclad_dispatch")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)


    def test_Py_InitModule4_VarargsKwargsFunctionDispatch(self):
        mapper = TempPtrCheckingPython25Mapper()
        method = MakeMethodDef("func", Null_CPythonVarargsKwargsFunction, METH.VARARGS | METH.KEYWORDS)
        
        def testModule(module, mapper):
            result = object()
            actualArgs = (1, "2", "buckle")
            actualKwargs = {"my": "shoe"}
            def dispatch_kwargs(name, _selfPtr, args, kwargs):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(_selfPtr, IntPtr.Zero, "instance should be null for function")
                self.assertEquals(args, actualArgs, "didn't pass args")
                self.assertEquals(kwargs, actualKwargs, "didn't pass kwargs")
                return result
            module._ironclad_dispatch_kwargs = dispatch_kwargs
            self.assertEquals(module.func(*actualArgs, **actualKwargs), result, "didn't use _ironclad_dispatch_kwargs")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        


class Python25Mapper_PyModule_AddObject_Test(unittest.TestCase):

    def testAddObjectToUnknownModuleFails(self):
        mapper = Python25Mapper()

        self.assertEquals(mapper.PyModule_AddObject(IntPtr.Zero, "zorro", IntPtr.Zero), -1,
                          "bad return on failure")


    def testAddObjectWithExistingReferenceAddsMappedObjectAndDecRefsPointer(self):
        mapper = Python25Mapper()
        testObject = object()
        testPtr = mapper.Store(testObject)
        modulePtr = MakeAndAddEmptyModule(mapper)
        moduleScope = mapper.Engine.CreateScope(mapper.Retrieve(modulePtr).Scope.Dict)

        result = mapper.PyModule_AddObject(modulePtr, "testObject", testPtr)
        try:
            self.assertEquals(result, 0, "bad value for success")
            self.assertRaises(KeyError, lambda: mapper.RefCount(testPtr))
            self.assertEquals(moduleScope.GetVariable[object]("testObject"), testObject, "did not store real object")
        finally:
            mapper.DecRef(modulePtr)


    def assertModuleAddsTypeWithData(self, tp_name, itemName, class__module__, class__name__, class__doc__):
        mapper = Python25Mapper()
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))

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

        deallocTypes = CreateTypes(mapper)
        typePtr, deallocType = MakeTypePtr(
            tp_name, mapper.PyType_Type, tp_doc=class__doc__, tp_newPtr=newFP, tp_initPtr=initFP)
        try:
            result = mapper.PyModule_AddObject(modulePtr, itemName, typePtr)

            self.assertEquals(result, 0, "reported failure")

            mappedClass = mapper.Retrieve(typePtr)
            generatedClass = getattr(module, itemName)
            self.assertEquals(mappedClass, generatedClass,
                              "failed to add new type to module")

            self.assertEquals(mappedClass._typePtr, typePtr, "not connected to underlying CPython type")
            self.assertEquals(mappedClass.__doc__, class__doc__, "unexpected docstring")
            self.assertEquals(mappedClass.__name__, class__name__, "unexpected __name__")
            self.assertEquals(mappedClass.__module__, class__module__, "unexpected __module__")

            mappedClass._tp_newDgt(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
            mappedClass._tp_initDgt(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
            self.assertEquals(calls, ["__new__", "__init__"],
                              "tp_new and tp_init not hooked up correctly")
        finally:
            deallocType()
            deallocTypes()
            mapper.DecRef(modulePtr)


    def testAddModule(self):
        self.assertModuleAddsTypeWithData(
            "some.module.Klass",
            "KlassName",
            "some.module",
            "Klass",
            "Klass is some sort of class.\n\nYou may find it useful.",
        )
        self.assertModuleAddsTypeWithData(
            "Klass",
            "KlassName",
            "",
            "Klass",
            "Klass is some sort of class.\n\nBeware, for its docstring contains '\\n's and similar trickery.",
        )

    def assertAddTypeObjectAndInstantiateWorks(self, newFails=False, initFails=False):
        # if it falls to you to debug this test... I apologise :(
        mapper = TempPtrCheckingPython25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        newPtr = mapper.Store(object())

        calls = []
        def new(typePtr, argPtr, kwargPtr):
            calls.append(("__new__", typePtr, argPtr, kwargPtr))
            self.assertEquals(mapper.Retrieve(argPtr), (1, 'two'), "new got wrong args")
            self.assertEquals(mapper.Retrieve(kwargPtr), {'three': 4}, "new got wrong kwargs")
            if newFails:
                mapper.LastException = BorkedException()
                return IntPtr.Zero
            return newPtr
        newDgt = PythonMapper.PyType_GenericNew_Delegate(new)
        newFP = Marshal.GetFunctionPointerForDelegate(newDgt)

        def init(selfPtr, argPtr, kwargPtr):
            calls.append(("__init__", selfPtr, argPtr, kwargPtr))
            self.assertEquals(mapper.Retrieve(argPtr), (1, 'two'), "init got wrong args")
            self.assertEquals(mapper.Retrieve(kwargPtr), {'three': 4}, "init got wrong kwargs")
            if initFails:
                mapper.LastException = BorkedException()
                mapper.IncRef(selfPtr)
                return -1
            return 0
        initDgt = CPython_initproc_Delegate(init)
        initFP = Marshal.GetFunctionPointerForDelegate(initDgt)

        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type,
            tp_newPtr=newFP, tp_initPtr=initFP)

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            thingholder = []
            def Instantiate():
                thingholder.append(module.thing(1, 'two', three=4))

            if newFails or initFails:
                self.assertRaises(BorkedException, Instantiate)
            else:
                Instantiate()

            def TestArgPtrs(argPtr, kwargPtr):
                self.assertRaises(KeyError, lambda: mapper.RefCount(argPtr))
                self.assertRaises(KeyError, lambda: mapper.RefCount(kwargPtr))
                self.assertEquals(mapper.tempPtrsFreed, True, "failed to clean up")

            methodName, newClsPtr, newArgPtr, newKwargPtr = calls[0]
            if not newFails:
                self.assertEquals(methodName, "__new__", "called wrong method")
                self.assertEquals(newClsPtr, typePtr, "instantiated wrong class")
                TestArgPtrs(newArgPtr, newKwargPtr)

                # note: for now, I'm comfortable passing 2 copies of the
                # args and kwargs to the 2 methods; this may change in future
                methodName, initSelfPtr, initArgPtr, initKwargPtr = calls[1]
                if not initFails:
                    self.assertEquals(methodName, "__init__", "called wrong method")
                    instancePtr = thingholder[0]._instancePtr
                    self.assertEquals(instancePtr, newPtr,
                                      "instance not associated with return value from _tp_new")
                    self.assertEquals(initSelfPtr, instancePtr, "initialised wrong object")
                    TestArgPtrs(initArgPtr, initKwargPtr)
                else:
                    # if an __init__ fails immediately after a __new__, I believe this is correct.
                    # HOWEVER, if a subsequent __init__ fails, just about anything you might do
                    # with the object could well crash horribly.
                    self.assertEquals(mapper.RefCount(initSelfPtr), 1,
                                      "failed to decref instance pointer on failed __init__")
        finally:
            deallocType()
            deallocTypes()
            mapper.DecRef(modulePtr)
            mapper.DecRef(newPtr)


    def testAddTypeObjectAndInstantiate(self):
        self.assertAddTypeObjectAndInstantiateWorks()
        self.assertAddTypeObjectAndInstantiateWorks(newFails=True)
        self.assertAddTypeObjectAndInstantiateWorks(initFails=True)



class Python25Mapper_PyModule_AddObject_DispatchMethodsTest(unittest.TestCase):

    def assertDispatchesToTypeMethod(self, mapper, method, flags, 
                                     expectedDispatchFunc, DoCall, TestExtraArgs):
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        
        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type,
            methodDef=MakeMethodDef("meth", method, flags),
            tp_allocPtr=mapper.GetAddress("PyType_GenericAlloc"),
            tp_newPtr=mapper.GetAddress("PyType_GenericNew"))

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            result = object()
            def MockDispatchFunc(*args):
                self.assertEquals(args[0], "thing.meth", "called wrong method")
                self.assertEquals(args[1], t._instancePtr, "called method on wrong instance")
                TestExtraArgs(args[2:])
                return result
            setattr(module, expectedDispatchFunc, MockDispatchFunc)
            
            t = module.thing()
            x = DoCall(t.meth)
            self.assertEquals(x, result, "bad return")
        finally:
            mapper.DecRef(modulePtr)
            deallocType()
            deallocTypes()


    def testAddTypeObjectWithNoArgsMethodDispatch(self):
        mapper = Python25Mapper()
        
        def DoCall(kallable):
            return kallable()
        
        def TestExtraArgs(extraArgs):
            self.assertEquals(len(extraArgs), 0, "noargs function doesn't need args")
        
        self.assertDispatchesToTypeMethod(
            mapper, Null_CPythonVarargsFunction, METH.NOARGS, 
            "_ironclad_dispatch_noargs",
            DoCall, TestExtraArgs)


    def testAddTypeObjectWithObjArgMethodDispatch(self):
        mapper = Python25Mapper()
        
        arg = object()
        def DoCall(kallable):
            return kallable(arg)
        
        def TestExtraArgs(extraArgs):
            self.assertEquals(extraArgs, (arg,), "failed to pass arg")
        
        self.assertDispatchesToTypeMethod(
            mapper, Null_CPythonVarargsFunction, METH.O, 
            "_ironclad_dispatch",
            DoCall, TestExtraArgs)


    def testAddTypeObjectWithVarargsMethodDispatch(self):
        mapper = Python25Mapper()
        
        args = ("for", "the", "horde")
        def DoCall(kallable):
            return kallable(*args)
        
        def TestExtraArgs(extraArgs):
            self.assertEquals(extraArgs, (args, ), "failed to pass args")
        
        self.assertDispatchesToTypeMethod(
            mapper, Null_CPythonVarargsFunction, METH.VARARGS, 
            "_ironclad_dispatch",
            DoCall, TestExtraArgs)


    def testAddTypeObjectWithVarargsKwargsMethodDispatch(self):
        mapper = Python25Mapper()
        
        args = ("for", "the", "horde")
        kwargs = {"g1": "LM", "g2": "BS", "g3": "GM"}
        def DoCall(kallable):
            return kallable(*args, **kwargs)
        
        def TestExtraArgs(extraArgs):
            self.assertEquals(extraArgs, (args, kwargs), "failed to pass args")
        
        self.assertDispatchesToTypeMethod(
            mapper, Null_CPythonVarargsKwargsFunction, METH.VARARGS | METH.KEYWORDS, 
            "_ironclad_dispatch_kwargs",
            DoCall, TestExtraArgs)


    def assertDispatchesToSelfTypeMethod(self, mapper, extraTypeKwargs, expectedDelegateKeySuffix,
                                         expectedMethodName, DoCall, TestErrorHandler):
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        
        typeKwargs = {
            "tp_allocPtr": mapper.GetAddress("PyType_GenericAlloc"),
            "tp_newPtr": mapper.GetAddress("PyType_GenericNew"),
        }
        typeKwargs.update(extraTypeKwargs)
        typePtr, deallocType = MakeTypePtr(
            "thing", mapper.PyType_Type, **typeKwargs)

        try:
            result = mapper.PyModule_AddObject(modulePtr, "thing", typePtr)
            self.assertEquals(result, 0, "reported failure")

            result = object()
            def MockDispatchFunc(methodName, selfPtr, errorHandler=None):
                self.assertEquals(methodName, "thing." + expectedDelegateKeySuffix, "called wrong method")
                self.assertEquals(selfPtr, t._instancePtr, "called method on wrong instance")
                TestErrorHandler(errorHandler)
                return result
            setattr(module, "_ironclad_dispatch_self", MockDispatchFunc)
            
            t = module.thing()
            x = DoCall(getattr(t, expectedMethodName))
            self.assertEquals(x, result, "bad return")
        finally:
            mapper.DecRef(modulePtr)
            deallocType()
            deallocTypes()


    def testAddTypeObjectWith_tp_iter_MethodDispatch(self):
        mapper = Python25Mapper()
        
        def DoCall(kallable):
            return kallable()
        
        def TestErrorHandler(errorHandler): 
            self.assertEquals(errorHandler, None, "no special error handling required")

        tp_iter = lambda _: IntPtr.Zero
        tp_iter_dgt = CPythonSelfFunction_Delegate(tp_iter)
        tp_iter_fp = Marshal.GetFunctionPointerForDelegate(tp_iter_dgt)

        # tp_iterPtr=IntPtr.Zero, tp_iternextPtr=IntPtr.Zero
        typeKwargs = {
            "tp_iterPtr": tp_iter_fp,
            "tp_flags": Py_TPFLAGS.HAVE_ITER
        }
        
        self.assertDispatchesToSelfTypeMethod(
            mapper, typeKwargs, "tp_iter", "__iter__",
            DoCall, TestErrorHandler)


    def testAddTypeObjectWith_tp_iternext_MethodDispatch(self):
        mapper = Python25Mapper()
        
        def DoCall(kallable):
            return kallable()
        
        def TestErrorHandler(errorHandler): 
            self.assertRaises(StopIteration, errorHandler, IntPtr.Zero)
            mapper.LastException = ValueError()
            errorHandler(IntPtr.Zero)

        tp_iternext = lambda _: IntPtr.Zero
        tp_iternext_dgt = CPythonSelfFunction_Delegate(tp_iternext)
        tp_iternext_fp = Marshal.GetFunctionPointerForDelegate(tp_iternext_dgt)

        # tp_iterPtr=IntPtr.Zero, tp_iternextPtr=IntPtr.Zero
        typeKwargs = {
            "tp_iternextPtr": tp_iternext_fp,
            "tp_flags": Py_TPFLAGS.HAVE_ITER
        }
        
        self.assertDispatchesToSelfTypeMethod(
            mapper, typeKwargs, "tp_iternext", "next",
            DoCall, TestErrorHandler)


suite = makesuite(
    Python25Mapper_PyInitModule_DispatchUtilsTest,
    Python25Mapper_PyInitModule_DispatchFunctionsTest,
    Python25Mapper_Py_InitModule4_Test,
    Python25Mapper_PyModule_AddObject_Test,
    Python25Mapper_PyModule_AddObject_DispatchMethodsTest,
)

if __name__ == '__main__':
    run(suite)