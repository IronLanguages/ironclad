import sys
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeItemsTablePtr, MakeMethodDef, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import TempPtrCheckingPython25Mapper, MakeAndAddEmptyModule
from tests.utils.testcase import TestCase

from System import IntPtr

from Ironclad import Python25Mapper
from Ironclad.Structs import METH

from TestUtils import ExecUtils


class BorkedException(Exception):
    pass


INSTANCE_PTR = IntPtr(111)
ARGS_PTR = IntPtr(222)
KWARGS_PTR = IntPtr(333)
EMPTY_KWARGS_PTR = IntPtr.Zero
RESULT_PTR = IntPtr(999)
ERROR_RESULT_PTR = IntPtr.Zero


Null_CPythonVarargsFunction = lambda _, __: IntPtr.Zero
Null_CPythonVarargsKwargsFunction = lambda _, __, ___: IntPtr.Zero


class Py_InitModule4_SetupTest(TestCase):
        
    def testNewModuleHasDispatcher(self):
        mapper = Python25Mapper()
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        Dispatcher = mapper.DispatcherModule.Dispatcher
        _dispatcher = module._dispatcher
        
        self.assertEquals(isinstance(_dispatcher, Dispatcher), True, "wrong dispatcher class")
        self.assertEquals(_dispatcher.mapper, mapper, "dispatcher had wrong mapper")
        mapper.Dispose()
        

class Py_InitModule4_Test(TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, mapper, methodDef, TestModule):
        methods, deallocMethods = MakeItemsTablePtr([methodDef])
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            methods,
            "test_docstring",
            IntPtr.Zero,
            12345)
            
        module = mapper.Retrieve(modulePtr)
        test_module = ExecUtils.GetPythonModule(mapper.Engine, 'test_module')
        
        for item in dir(test_module):
            self.assertEquals(getattr(module, item) is getattr(test_module, item),
                              True, "%s didn't match" % item)
        TestModule(test_module, mapper)
        
        mapper.Dispose()
        deallocMethods()


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
        mapper.Dispose()
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
        mapper.Dispose()
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
        mapper.Dispose()
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
        mapper.Dispose()
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
        mapper.Dispose()
        deallocMethod()
        
        
class PyModule_GetDict_Test(TestCase):
    
    def testGetsDict(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        moduleDict = mapper.Retrieve(mapper.PyModule_GetDict(modulePtr))
        moduleDict['random'] = 4
        
        self.assertEquals(module.random, 4, 'modified wrong dict')
        
        mapper.Dispose()
        deallocTypes()


class PyModule_AddConstants_Test(TestCase):
    
    def testAddConstants(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        self.assertEquals(mapper.PyModule_AddIntConstant(modulePtr, "i_am_an_int", -31000), 0, "reported failure")
        self.assertEquals(module.i_am_an_int, -31000)
        
        self.assertEquals(mapper.PyModule_AddStringConstant(modulePtr, "i_am_a_string", "how_long"), 0, "reported failure")
        self.assertEquals(module.i_am_a_string, "how_long")
        
        mapper.Dispose()
        deallocTypes()
        


class PyModule_AddObject_Test(TestCase):

    def testAddObjectToUnknownModuleFails(self):
        mapper = Python25Mapper()
        self.assertEquals(mapper.PyModule_AddObject(IntPtr.Zero, "zorro", IntPtr.Zero), -1,
                          "bad return on failure")
        mapper.Dispose()


    def testAddObjectWithExistingReferenceAddsMappedObjectAndDecRefsPointer(self):
        mapper = Python25Mapper()
        testObject = object()
        testPtr = mapper.Store(testObject)
        mapper.IncRef(testPtr)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        result = mapper.PyModule_AddObject(modulePtr, "testObject", testPtr)
        self.assertEquals(result, 0, "bad value for success")
        self.assertEquals(mapper.RefCount(testPtr), 1)
        self.assertEquals(module.testObject, testObject, "did not store real object")
        mapper.Dispose()


    def assertAddsTypeWithData(self, tp_name, itemName, class__module__, class__name__, class__doc__):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
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
        
        mapper.Dispose()
        deallocType()
        deallocTypes()


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


class ImportTest(TestCase):
    
    def testPyImport_ImportModule(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            IntPtr.Zero,
            "test_docstring",
            IntPtr.Zero,
            12345)
        
        self.assertEquals(mapper.PyImport_ImportModule("test_module"), modulePtr)
        self.assertEquals(mapper.RefCount(modulePtr), 2, "did not incref")
        
        mapper.Dispose()
        deallocTypes()
    
    def testPyImport_Import(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            IntPtr.Zero,
            "test_docstring",
            IntPtr.Zero,
            12345)
        
        self.assertEquals(mapper.PyImport_Import(mapper.Store("test_module")), modulePtr)
        self.assertEquals(mapper.RefCount(modulePtr), 2, "did not incref")
        
        mapper.Dispose()
        deallocTypes()
    
    def testPyImport_AddModule(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        sysPtr = mapper.PyImport_ImportModule("sys")
        modules = mapper.Retrieve(sysPtr).modules
        
        foobarbazPtr = mapper.PyImport_AddModule("foo.bar.baz")
        self.assertEquals(mapper.Retrieve(foobarbazPtr), modules['foo.bar.baz'])
        self.assertEquals('foo.bar' in modules, True)
        self.assertEquals(modules['foo.bar'].baz, modules['foo.bar.baz'])
        self.assertEquals('foo' in modules, True)
        self.assertEquals(modules['foo'].bar, modules['foo.bar'])
        
        mapper.Dispose()
        deallocTypes()


# not sure this is the right place for these tests
class BuiltinsTest(TestCase):
    
    def testPyEval_GetBuiltins(self):
        mapper = Python25Mapper()
        
        builtinsPtr = mapper.PyEval_GetBuiltins()
        builtins = mapper.Retrieve(builtinsPtr)
        self.assertEquals(builtins, ExecUtils.GetPythonModule(mapper.Engine, '__builtin__').__dict__)
        
        mapper.Dispose()
        
        
        
class SysTest(TestCase):
    
    def testPySys_GetObject(self):
        mapper = Python25Mapper()
        
        modulesPtr = mapper.PySys_GetObject('modules')
        modules = mapper.Retrieve(modulesPtr)
        self.assertEquals(modules, ExecUtils.GetPythonModule(mapper.Engine, 'sys').modules)
        
        self.assertEquals(mapper.PySys_GetObject('not_in_sys'), IntPtr.Zero)
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(NameError, KindaConvertError)
        
        mapper.Dispose()


suite = makesuite(
    Py_InitModule4_SetupTest,
    Py_InitModule4_Test,
    PyModule_GetDict_Test,
    PyModule_AddConstants_Test,
    PyModule_AddObject_Test,
    ImportTest,
    BuiltinsTest, 
    SysTest, 
)

if __name__ == '__main__':
    run(suite)
