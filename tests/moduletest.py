import sys
from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeItemsTablePtr, MakeMethodDef, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.pythonmapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase, WithMapper, WithMapperSubclass

from System import IntPtr

from Ironclad import Dispatcher, PythonMapper
from Ironclad.Structs import METH


class Py_InitModule4_SetupTest(TestCase):
    
    @WithMapper
    def testNewModuleHasDispatcher(self, mapper, _):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        _dispatcher = module._dispatcher
        
        self.assertEqual(isinstance(_dispatcher, Dispatcher), True, "wrong dispatcher class")
        self.assertEqual(_dispatcher.mapper, mapper, "dispatcher had wrong mapper")
        

MODULE_PTR = IntPtr(54321)

class Py_InitModule4_Test(TestCase):

    def assert_Py_InitModule4_withSingleMethod(self, mapper, methodDef, TestModule):
        methods, deallocMethods = MakeItemsTablePtr([methodDef])
        try:
            modulePtr = mapper.Py_InitModule4(
                "test_module",
                methods,
                "test_docstring",
                MODULE_PTR,
                12345)

            module = mapper.Retrieve(modulePtr)
            test_module = sys.modules['test_module']

            for item in dir(test_module):
                self.assertEqual(getattr(module, item) is getattr(test_module, item),
                                  True, "%s didn't match" % item)
            TestModule(test_module, mapper)
        finally:
            mapper.Dispose()
            deallocMethods()


    def test_Py_InitModule4_CreatesPopulatedModule(self):
        mapper = PythonMapper()
        method, deallocMethod = MakeMethodDef(
            "harold", lambda _, __: IntPtr.Zero, METH.VARARGS, "harold's documentation")
        
        def testModule(test_module, _):
            self.assertEqual(test_module.__doc__, 'test_docstring',
                              'module docstring not remembered')
            self.assertTrue(callable(test_module.harold),
                            'function not remembered')
            self.assertTrue(callable(test_module._dispatcher.table['harold']),
                            'delegate not remembered')
            self.assertEqual(test_module.harold.__doc__, "harold's documentation",
                              'function docstring not remembered')

        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        

    def test_Py_InitModule4_NoArgsFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, __):
            self.assertEqual((_, __), (MODULE_PTR, IntPtr.Zero))
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.NOARGS)
        
        def testModule(module, mapper):
            self.assertEqual(module.func(), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_OldargsFunction_OneArg(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        arg = object()
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argPtr):
            self.assertEqual(_, MODULE_PTR)
            self.assertEqual(mapper.Retrieve(argPtr), arg)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.OLDARGS)
        
        def testModule(module, mapper):
            self.assertEqual(module.func(arg), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_OldargsFunction_SomeArgs(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        args = (object(), object())
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argsPtr):
            self.assertEqual(_, MODULE_PTR)
            self.assertEqual(mapper.Retrieve(argsPtr), args)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.OLDARGS)
        
        def testModule(module, mapper):
            self.assertEqual(module.func(*args), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_ObjargFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        arg = object()
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argPtr):
            self.assertEqual(_, MODULE_PTR)
            self.assertEqual(mapper.Retrieve(argPtr), arg)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.O)
        
        def testModule(module, mapper):
            self.assertEqual(module.func(arg), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_VarargsFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        args = (object(), object())
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argsPtr):
            self.assertEqual(_, MODULE_PTR)
            self.assertEqual(mapper.Retrieve(argsPtr), args)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.VARARGS)
        
        def testModule(module, mapper):
            self.assertEqual(module.func(*args), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()


    def test_Py_InitModule4_VarargsKwargsFunction(self):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        args = (object(), object())
        kwargs = {'a': object(), 'b': object()}
        result = object()
        resultPtr = mapper.Store(result)
        mapper.IncRef(resultPtr)
        
        def func(_, argsPtr, kwargsPtr):
            self.assertEqual(_, MODULE_PTR)
            self.assertEqual(mapper.Retrieve(argsPtr), args)
            self.assertEqual(mapper.Retrieve(kwargsPtr), kwargs)
            return resultPtr
        method, deallocMethod = MakeMethodDef("func", func, METH.VARARGS | METH.KEYWORDS)
        
        def testModule(module, mapper):
            self.assertEqual(module.func(*args, **kwargs), result, "not hooked up")
            
        self.assert_Py_InitModule4_withSingleMethod(mapper, method, testModule)
        deallocMethod()
        deallocTypes()
        
        
class PyModule_Functions_Test(TestCase):
    
    @WithMapper
    def testGetsDict(self, mapper, _):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        moduleDict = mapper.Retrieve(mapper.PyModule_GetDict(modulePtr))
        moduleDict['random'] = 4
        
        self.assertEqual(module.random, 4, 'modified wrong dict')
        
    
    @WithMapper
    def testAddConstants(self, mapper, _):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        self.assertEqual(mapper.PyModule_AddIntConstant(modulePtr, "i_am_an_int", -31000), 0, "reported failure")
        self.assertEqual(module.i_am_an_int, -31000)
        
        self.assertEqual(mapper.PyModule_AddStringConstant(modulePtr, "i_am_a_string", "how_long"), 0, "reported failure")
        self.assertEqual(module.i_am_a_string, "how_long")
        

    @WithMapper
    def testAddObjectToUnknownModuleFails(self, mapper, _):
        self.assertEqual(mapper.PyModule_AddObject(IntPtr.Zero, "zorro", IntPtr.Zero), -1,
                          "bad return on failure")


    @WithMapper
    def testAddObjectWithExistingReferenceAddsMappedObjectAndDecRefsPointer(self, mapper, _):
        testObject = object()
        testPtr = mapper.Store(testObject)
        mapper.IncRef(testPtr)
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)

        result = mapper.PyModule_AddObject(modulePtr, "testObject", testPtr)
        self.assertEqual(result, 0, "bad value for success")
        self.assertEqual(mapper.RefCount(testPtr), 1)
        self.assertEqual(module.testObject, testObject, "did not store real object")


    @WithMapper
    def assertAddsTypeWithData(self, tp_name, itemName, class__module__, class__name__, class__doc__, mapper, addDealloc):
        modulePtr = MakeAndAddEmptyModule(mapper)
        module = mapper.Retrieve(modulePtr)
        
        typeSpec = {
            "tp_name": tp_name,
            "tp_doc": class__doc__
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addDealloc(deallocType)
        result = mapper.PyModule_AddObject(modulePtr, itemName, typePtr)
        self.assertEqual(result, 0, "reported failure")

        mappedClass = mapper.Retrieve(typePtr)
        generatedClass = getattr(module, itemName)
        self.assertEqual(mappedClass, generatedClass,
                          "failed to add new type to module")

        self.assertEqual(mappedClass.__doc__, class__doc__, "unexpected docstring")
        self.assertEqual(mappedClass.__name__, class__name__, "unexpected __name__")
        self.assertEqual(mappedClass.__module__, class__module__, "unexpected __module__")


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


    @WithMapper
    def testPyModule_New(self, mapper, _):
        modulePtr = mapper.PyModule_New("forsooth")
        module = mapper.Retrieve(modulePtr)
        self.assertEqual(module.__name__, "forsooth")
        self.assertEqual(module.__doc__, "")
        


class ImportTest(TestCase):
    
    @WithMapper
    def testPyImport_ImportModule(self, mapper, _):
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            IntPtr.Zero,
            "test_docstring",
            IntPtr.Zero,
            12345)
        
        self.assertEqual(mapper.PyImport_ImportModule("test_module"), modulePtr)
        self.assertEqual(mapper.RefCount(modulePtr), 2, "did not incref")
    
    @WithMapper
    def testPyImport_Import(self, mapper, _):
        modulePtr = mapper.Py_InitModule4(
            "test_module",
            IntPtr.Zero,
            "test_docstring",
            IntPtr.Zero,
            12345)
        
        self.assertEqual(mapper.PyImport_Import(mapper.Store("test_module")), modulePtr)
        self.assertEqual(mapper.RefCount(modulePtr), 2, "did not incref")
    
    @WithMapper
    def testPyImport_AddModule(self, mapper, _):
        sysPtr = mapper.PyImport_ImportModule("sys")
        modules = mapper.Retrieve(sysPtr).modules
        
        foobarbazPtr = mapper.PyImport_AddModule("foo.bar.baz")
        self.assertEqual(mapper.Retrieve(foobarbazPtr), modules['foo.bar.baz'])
        self.assertEqual('foo.bar' in modules, True)
        self.assertEqual(modules['foo.bar'].baz, modules['foo.bar.baz'])
        self.assertEqual('foo' in modules, True)
        self.assertEqual(modules['foo'].bar, modules['foo.bar'])

    
    @WithMapper
    def testPyImport_GetModuleDict(self, mapper, _):
        modulesPtr = mapper.PyImport_GetModuleDict()
        modules = mapper.Retrieve(modulesPtr)
        self.assertEqual(modules is sys.modules, True)
        
        mapper.IncRef(modulesPtr)
        mapper.ReleaseGIL()
        self.assertEqual(mapper.RefCount(modulesPtr), 1, 'borrowed reference not cleaned up')
        mapper.EnsureGIL()


    @WithMapper
    def testPyImport_ImportFunctions_Failure(self, mapper, _):
        self.assertEqual(mapper.PyImport_Import(mapper.Store('this_module_does_not_exist')), IntPtr.Zero)
        self.assertMapperHasError(mapper, ImportError)
        
        self.assertEqual(mapper.PyImport_ImportModule('this_module_does_not_exist'), IntPtr.Zero)
        self.assertMapperHasError(mapper, ImportError)



class NastyImportDetailsTest(TestCase):
    
    @WithMapperSubclass
    def testNameFixing_PyImport_AddModule_NamesMatch(self, mapper, _):
        mapper.importNames.Push('hungry.hungry.hippo')
        mapper.PyImport_AddModule("hippo")
        
        self.assertNotIn("hippo", sys.modules)
        self.assertIn('hungry.hungry.hippo', sys.modules)
        
        for key in list(sys.modules.keys()):
            if key.startswith('hungry'):
                del sys.modules[key]
    
    
    @WithMapperSubclass
    def testNameFixing_PyImport_AddModule_NoMatch(self, mapper, _):
        mapper.importNames.Push('hungry.hungry.hippo')
        mapper.importNames.Push('angry.angry.alligator')
        mapper.PyImport_AddModule("hippo")
        
        self.assertIn("hippo", sys.modules)
        self.assertNotIn('angry.angry.alligator', sys.modules)
    
        del sys.modules['hippo']
        
    
    @WithMapperSubclass
    def testNameFixing_Py_InitModule4_NamesMatch(self, mapper, _):
        mapper.importFiles.Push('hippo_file')
        mapper.importNames.Push('hungry.hungry.hippo')
        mapper.Py_InitModule4("hippo", IntPtr.Zero, "test_docstring", IntPtr.Zero, 12345)
        
        self.assertNotIn("hippo", sys.modules)
        self.assertEqual(sys.modules['hungry.hungry.hippo'].__doc__, 'test_docstring')
        self.assertEqual(sys.modules['hungry.hungry.hippo'].__file__, 'hippo_file')
        
        for key in list(sys.modules.keys()):
            if key.startswith('hungry'):
                del sys.modules[key]
    
    
    @WithMapperSubclass
    def testNameFixing_Py_InitModule4_NoMatch(self, mapper, _):
        mapper.importName = 'angry.angry.alligator'
        mapper.Py_InitModule4("hippo", IntPtr.Zero, "test_docstring", IntPtr.Zero, 12345)
        
        self.assertIn("hippo", sys.modules)
        self.assertNotIn('angry.angry.alligator', sys.modules)
    
        del sys.modules['hippo']
        



# not sure this is the right place for these tests
class BuiltinsTest(TestCase):
    
    @WithMapper
    def testPyEval_GetBuiltins(self, mapper, _):
        builtinsPtr = mapper.PyEval_GetBuiltins()
        import builtins
        self.assertEqual(mapper.Retrieve(builtinsPtr), builtins.__dict__)
        
        
        
class SysTest(TestCase):
    
    @WithMapper
    def testPySys_GetObject(self, mapper, _):
        modulesPtr = mapper.PySys_GetObject('modules')
        modules = mapper.Retrieve(modulesPtr)
        self.assertEqual(modules is sys.modules, True)


suite = makesuite(
    Py_InitModule4_SetupTest,
    Py_InitModule4_Test,
    PyModule_Functions_Test,
    ImportTest,
    NastyImportDetailsTest,
    BuiltinsTest, 
    SysTest, 
)

if __name__ == '__main__':
    run(suite)
