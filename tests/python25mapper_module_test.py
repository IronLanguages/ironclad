
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import DELEGATE_TYPES, MakeItemsTablePtr, MakeMethodDef, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import TempPtrCheckingPython25Mapper, MakeAndAddEmptyModule

import System
from System import IntPtr, NullReferenceException
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    CPyMarshal, CPython_initproc_Delegate, CPythonSelfFunction_Delegate, CPythonVarargsFunction_Delegate, 
    CPythonVarargsKwargsFunction_Delegate, PythonMapper, Python25Mapper
)
from Ironclad.Structs import METH, Py_TPFLAGS, PyMethodDef, PyObject, PyTypeObject

from TestUtils import ExecUtils


class BorkedException(System.Exception):
    pass


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



class Python25Mapper_Py_InitModule4_SetupTest(unittest.TestCase):
        
    def testNewModuleHasDispatcher(self):
        mapper = Python25Mapper()
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        dispatcherModule = ModuleWrapper(mapper.Engine, mapper.DispatcherModule)
        
        Dispatcher = dispatcherModule.Dispatcher
        _dispatcher = module._dispatcher
        
        self.assertEquals(isinstance(_dispatcher, Dispatcher), True, "wrong dispatcher class")
        self.assertEquals(_dispatcher.mapper, mapper, "dispatcher had wrong mapper")
        mapper.DecRef(modulePtr)
        

class Python25Mapper_Py_InitModule4_Test(unittest.TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, mapper, methodDef, TestModule):
        methods, deallocMethods = MakeItemsTablePtr([methodDef])
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            methods,
            "test_docstring",
            IntPtr.Zero,
            12345)
            
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        test_module = ExecUtils.GetPythonModule(mapper.Engine, 'test_module')
        
        for item in dir(test_module):
            # ModuleWrapper.__doc__ will hide underlying module.__doc__ if we just use plain getattr
            self.assertEquals(ModuleWrapper.__getattr__(module, item) is getattr(test_module, item),
                              True, "%s didn't match" % item)
        TestModule(test_module, mapper)
        
        deallocMethods()
        mapper.FreeTemps()
        mapper.DecRef(modulePtr)


    def test_Py_InitModule4_CreatesPopulatedModule(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef(
            "harold", lambda _, __: IntPtr.Zero, METH.VARARGS, "harold's documentation")
        
        def testModule(test_module, _):
            self.assertEquals(test_module.__doc__, 'test_docstring',
                              'module docstring not remembered')
            self.assertTrue(callable(test_module.harold),
                            'function not remembered')
            self.assertTrue(callable(test_module._dispatcher.table['harold']),
                            'delegate not remembered')
            self.assertEquals(test_module.harold.__doc__, "harold's documentation",
                              'function docstring not remembered')

        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        

    def test_Py_InitModule4_NoArgsFunction(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("func", Null_CPythonVarargsFunction, METH.NOARGS)
        
        def testModule(module, mapper):
            result = object()
            def dispatch(name):
                self.assertEquals(name, "func", "called wrong function")
                return result
            module._dispatcher.function_noargs = dispatch
            self.assertEquals(module.func(), result, "didn't use correct _dispatcher method")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()


    def test_Py_InitModule4_ObjargFunction(self):
        mapper = TempPtrCheckingPython25Mapper()
        method, deallocMethod = MakeMethodDef("func", Null_CPythonVarargsFunction, METH.O)
        
        def testModule(module, mapper):
            result = object()
            actualArg = object()
            def dispatch(name, arg):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(arg, actualArg, "didn't pass arg")
                return result
            module._dispatcher.function_objarg = dispatch
            self.assertEquals(module.func(actualArg), result, "didn't use correct _dispatcher method")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()


    def test_Py_InitModule4_VarargsFunction(self):
        mapper = TempPtrCheckingPython25Mapper()
        method, deallocMethod = MakeMethodDef("func", Null_CPythonVarargsFunction, METH.VARARGS)
        
        def testModule(module, mapper):
            result = object()
            actualArgs = (1, "2", "buckle")
            def dispatch(name, *args):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(args, actualArgs, "didn't pass args")
                return result
            module._dispatcher.function_varargs = dispatch
            self.assertEquals(module.func(*actualArgs), result, "didn't use correct _dispatcher method")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()


    def test_Py_InitModule4_VarargsKwargsFunction(self):
        mapper = TempPtrCheckingPython25Mapper()
        method, deallocMethod = MakeMethodDef("func", Null_CPythonVarargsKwargsFunction, METH.VARARGS | METH.KEYWORDS)
        
        def testModule(module, mapper):
            result = object()
            actualArgs = (1, "2", "buckle")
            actualKwargs = {"my": "shoe"}
            def dispatch_kwargs(name, *args, **kwargs):
                self.assertEquals(name, "func", "called wrong function")
                self.assertEquals(args, actualArgs, "didn't pass args")
                self.assertEquals(kwargs, actualKwargs, "didn't pass kwargs")
                return result
            module._dispatcher.function_kwargs = dispatch_kwargs
            self.assertEquals(module.func(*actualArgs, **actualKwargs), result, "didn't use _ironclad_dispatch_kwargs")
        
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        


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
        self.assertEquals(result, 0, "bad value for success")
        self.assertRaises(KeyError, lambda: mapper.RefCount(testPtr))
        self.assertEquals(moduleScope.GetVariable[object]("testObject"), testObject, "did not store real object")
        mapper.DecRef(modulePtr)


    def assertAddsTypeWithData(self, tp_name, itemName, class__module__, class__name__, class__doc__):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        
        typeSpec = {
            "tp_name": tp_name,
            "tp_doc": class__doc__
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
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
        
        deallocType()
        deallocTypes()
        mapper.DecRef(modulePtr)


    def testAddModule(self):
        self.assertAddsTypeWithData(
            "some.module.Klass",
            "KlassName",
            "some.module",
            "Klass",
            "Klass is some sort of class.\n\nYou may find it useful.",
        )
        self.assertAddsTypeWithData(
            "Klass",
            "KlassName",
            "",
            "Klass",
            "Klass is some sort of class.\nBeware, for its docstring contains '\\n's and similar trickery.",
        )


class Python25Mapper_PyModule_AddObject_DispatchTrickyMethodsTest(unittest.TestCase):

    def testAddTypeObject_NewInitDispatch(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        
        # all methods should be patched out
        def Raise(msg):
            raise Exception(msg)
        typeSpec = {
            "tp_name": "klass",
            "tp_new": lambda _, __, ___: Raise("new unpatched"),
            "tp_init": lambda _, __, ___: Raise("init unpatched")
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        mapper.PyModule_AddObject(modulePtr, "klass", typePtr)
        
        ARGS = (1, "two")
        KWARGS = {"three": 4}
        instancePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(instancePtr, PyTypeObject, 'ob_refcnt', 1)
        CPyMarshal.WritePtrField(instancePtr, PyTypeObject, 'ob_type', mapper.PyType_Type)
        
        calls = []
        def test_tp_new(typePtr_new, argsPtr, kwargsPtr):
            calls.append(('tp_new', (typePtr_new, argsPtr, kwargsPtr)))
            self.assertEquals(typePtr_new, typePtr, "wrong type")
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS, "wrong args")
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS, "wrong kwargs")
            return instancePtr
        
        def test_tp_init(instancePtr_init, argsPtr, kwargsPtr):
            calls.append(('tp_init', (instancePtr_init, argsPtr, kwargsPtr)))
            self.assertEquals(instancePtr_init, instancePtr, "wrong init")
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS, "wrong args")
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS, "wrong kwargs")
            return 0
        
        module._dispatcher.table['klass.tp_new'] = PythonMapper.PyType_GenericNew_Delegate(test_tp_new)
        module._dispatcher.table['klass.tp_init'] = CPython_initproc_Delegate(test_tp_init)
        
        instance = module.klass(*ARGS, **KWARGS)
        self.assertEquals(instance._instancePtr, instancePtr, "wrong instance,")
        
        Marshal.FreeHGlobal(instancePtr)
        deallocType()
        deallocTypes()
        

class Python25Mapper_PyModule_AddObject_DispatchMethodsTest(unittest.TestCase):

    def assertAddTypeObject_withSingleMethod(self, mapper, methodDef, TestModule):
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        
        typeSpec = {
            "tp_name": "klass",
            "tp_methods": [methodDef]
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        
        result = mapper.PyModule_AddObject(modulePtr, "klass", typePtr)
        self.assertEquals(result, 0, "reported failure")
        TestModule(module)
        
        deallocType()
        mapper.DecRef(modulePtr)
        deallocTypes()
            
            
    def test_PyAddTypeObject_NoArgsMethod(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsFunction, METH.NOARGS)
        
        def TestModule(module):
            result = object()
            def dispatch(name, instancePtr):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                return result
            module._dispatcher.method_noargs = dispatch
            instance = module.klass()
            self.assertEquals(instance.method(), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestModule)
        deallocMethod()


    def test_PyAddTypeObject_ObjArgMethod(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsFunction, METH.O)
        
        def TestModule(module):
            arg = object()
            result = object()
            def dispatch(name, instancePtr, dispatch_arg):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                self.assertEquals(dispatch_arg, arg, "called with wrong arg")
                return result
            module._dispatcher.method_objarg = dispatch
            instance = module.klass()
            self.assertEquals(instance.method(arg), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestModule)
        deallocMethod()


    def testAddTypeObjectWithVarargsMethodDispatch(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsFunction, METH.VARARGS)
        
        def TestModule(module):
            args = ("for", "the", "horde")
            result = object()
            def dispatch(name, instancePtr, *dispatch_args):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                self.assertEquals(dispatch_args, args, "called with wrong args")
                return result
            module._dispatcher.method_varargs = dispatch
            instance = module.klass()
            self.assertEquals(instance.method(*args), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestModule)
        deallocMethod()
        

    def testAddTypeObjectWithVarargsKwargsMethodDispatch(self):
        mapper = Python25Mapper()
        method, deallocMethod = MakeMethodDef("method", Null_CPythonVarargsKwargsFunction, METH.VARARGS | METH.KEYWORDS)
        
        def TestModule(module):
            args = ("for", "the", "horde")
            kwargs = {"g1": "LM", "g2": "BS", "g3": "GM"}
            result = object()
            def dispatch(name, instancePtr, *dispatch_args, **dispatch_kwargs):
                self.assertEquals(name, "klass.method", "called wrong function")
                self.assertEquals(instancePtr, instance._instancePtr, "called on wrong instance")
                self.assertEquals(dispatch_args, args, "called with wrong args")
                self.assertEquals(dispatch_kwargs, kwargs, "called with wrong args")
                return result
            module._dispatcher.method_kwargs = dispatch
            instance = module.klass()
            self.assertEquals(instance.method(*args, **kwargs), result, "didn't use correct _dispatcher method")
        
        self.assertAddTypeObject_withSingleMethod(mapper, method, TestModule)
        deallocMethod()

class Python25Mapper_PyModule_AddObject_DispatchIterTest(unittest.TestCase):

    def assertDispatchesToSelfTypeMethod(self, mapper, typeSpec, expectedKeyName,
                                         expectedMethodName, TestErrorHandler):
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = ModuleWrapper(mapper.Engine, mapper.Retrieve(modulePtr))
        
        typeSpec["tp_name"] = "klass"
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        self.assertEquals(mapper.PyModule_AddObject(modulePtr, "klass", typePtr), 
                          0, "reported failure")

        result = object()
        instance = module.klass()
        def MockDispatchFunc(methodName, selfPtr, errorHandler=None):
            self.assertEquals(methodName, "klass." + expectedKeyName, "called wrong method")
            self.assertEquals(selfPtr, instance._instancePtr, "called method on wrong instance")
            TestErrorHandler(errorHandler)
            return result
        module._dispatcher.method_selfarg = MockDispatchFunc
        
        self.assertEquals(getattr(instance, expectedMethodName)(), result, "bad return")
        mapper.DecRef(modulePtr)
        deallocType()
        deallocTypes()


    def testAddTypeObjectWith_tp_iter_MethodDispatch(self):
        mapper = Python25Mapper()
        
        def TestErrorHandler(errorHandler): 
            self.assertEquals(errorHandler, None, "no special error handling required")

        typeSpec = {
            "tp_iter": lambda _: IntPtr.Zero,
            "tp_flags": Py_TPFLAGS.HAVE_ITER
        }
        self.assertDispatchesToSelfTypeMethod(
            mapper, typeSpec, "tp_iter", "__iter__", TestErrorHandler)


    def testAddTypeObjectWith_tp_iternext_MethodDispatch(self):
        mapper = Python25Mapper()
        
        def TestErrorHandler(errorHandler): 
            errorHandler(IntPtr(12345))
            self.assertRaises(StopIteration, errorHandler, IntPtr.Zero)
            mapper.LastException = ValueError()
            errorHandler(IntPtr.Zero)

        typeKwargs = {
            "tp_iternext": lambda _: IntPtr.Zero,
            "tp_flags": Py_TPFLAGS.HAVE_ITER
        }
        
        self.assertDispatchesToSelfTypeMethod(
            mapper, typeKwargs, "tp_iternext", "next", TestErrorHandler)


suite = makesuite(
    Python25Mapper_Py_InitModule4_SetupTest,
    Python25Mapper_Py_InitModule4_Test,
    Python25Mapper_PyModule_AddObject_Test,
    Python25Mapper_PyModule_AddObject_DispatchTrickyMethodsTest,
    Python25Mapper_PyModule_AddObject_DispatchMethodsTest,
    Python25Mapper_PyModule_AddObject_DispatchIterTest,
)

if __name__ == '__main__':
    run(suite)