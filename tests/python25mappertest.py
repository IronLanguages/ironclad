
import unittest
from tests.utils.allocators import GetAllocatingTestAllocator, GetDoNothingTestAllocator
from tests.utils.memory import OffsetPtr
from tests.utils.runtest import makesuite, run

import System
from System import Array, Byte, Char, Int32, IntPtr, OutOfMemoryException
from System.Collections.Generic import Dictionary
from System.Reflection import BindingFlags
from System.Runtime.InteropServices import Marshal
from JumPy import (
    ArgWriter, CPyMarshal, CPythonVarargsFunction_Delegate, CPythonVarargsKwargsFunction_Delegate,
    IntArgWriter, Python25Mapper, SizedStringArgWriter, StubReference
)
from JumPy.Structs import METH, PyMethodDef, PyStringObject
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


class TempPtrCheckingPython25Mapper(Python25Mapper):
    def __init__(self, *args):
        Python25Mapper.__init__(self, *args)
        self.tempPtrsFreed = False
    def FreeTempPtrs(self):
        Python25Mapper.FreeTempPtrs(self)
        self.tempPtrsFreed = True



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


    def testIncRefDecRef(self):
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


    def testNullPointers(self):
        engine = PythonEngine()
        allocator = GetDoNothingTestAllocator([])
        mapper = Python25Mapper(engine, allocator)

        self.assertRaises(KeyError, lambda: mapper.IncRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.DecRef(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.RefCount(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Retrieve(IntPtr.Zero))
        self.assertRaises(KeyError, lambda: mapper.Delete(IntPtr.Zero))


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

    def assert_Py_InitModule4_withSingleMethod(self, engine, mapper, method, moduleTest):
        size = Marshal.SizeOf(PyMethodDef)
        methods = Marshal.AllocHGlobal(size * 2)
        try:
            Marshal.StructureToPtr(method, methods, False)
            terminator = IntPtr(methods.ToInt32() + size)
            CPyMarshal.WriteInt(terminator, 0)

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
            mapper.FreeTempPtrs()


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
        mapper = TempPtrCheckingPython25Mapper(engine)
        retval = mapper.Store("jedi")
        calls = []
        def CModuleFunction(_selfPtr, argPtr):
            calls.append((_selfPtr, argPtr))
            mapper.IncRef(argPtr)
            return retval
        cModuleDelegate = CPythonVarargsFunction_Delegate(CModuleFunction)

        method = PyMethodDef(
            "harold",
            Marshal.GetFunctionPointerForDelegate(cModuleDelegate),
            METH.VARARGS,
            "harold's documentation",
        )

        def testModule(test_module, mapper):
            try:
                self.assertEquals(test_module.harold(1, 2, 3), "jedi", "bad result")
                self.assertRaises(KeyError, lambda: mapper.Retrieve(retval))
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
        cModuleDelegate = CPythonVarargsKwargsFunction_Delegate(CModuleFunction)

        method = PyMethodDef(
            "harold",
            Marshal.GetFunctionPointerForDelegate(cModuleDelegate),
            METH.VARARGS | METH.KEYWORDS,
            "harold's documentation",
        )

        def testModule(test_module, mapper):
            try:
                self.assertEquals(test_module.harold(1, 2, 3, four=4, five=5), "sith", "bad result")
                self.assertRaises(KeyError, lambda: mapper.Retrieve(retval))
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

        mapper = MyP25M(PythonEngine())
        result = mapper.PyArg_ParseTupleAndKeywords(argsPtr, kwargsPtr, format, kwlistPtr, outPtr)
        self.assertEquals(result, True, "should return true on 'success'")
        self.assertEquals(calls, ["GetArgValues", "GetArgWriters", "SetArgValues"])


    def assertGetArgValuesWorks(self, args, kwargs, kwlist, expectedResults):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        ptrsize = Marshal.SizeOf(IntPtr)
        intsize = Marshal.SizeOf(Int32)

        # alloc
        argsPtr = mapper.Store(args)
        kwargsPtr = mapper.Store(kwargs)
        kwlistPtr = Marshal.AllocHGlobal(ptrsize * (len(kwlist) + 1))
        current = kwlistPtr
        for s in kwlist:
            addressWritten = Marshal.StringToHGlobalAnsi(s)
            CPyMarshal.WritePtr(current, addressWritten)
            current = IntPtr(current.ToInt32() + ptrsize)
        CPyMarshal.WritePtr(current, IntPtr.Zero)

        try:
            # actual test
            results = dict(mapper.GetArgValues(argsPtr, kwargsPtr, kwlistPtr))
            self.assertEquals(results, expectedResults, "something, somewhere, broke")
        finally:
            # dealloc
            mapper.DecRef(argsPtr)
            mapper.DecRef(kwargsPtr)
            for i in range(len(kwlist)):
                Marshal.FreeHGlobal(Marshal.ReadIntPtr(IntPtr(kwlistPtr.ToInt32() + (i * ptrsize))))
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


class Python25Mapper_PyString_FromStringAndSize_Test(unittest.TestCase):

    def testCreateEmptyString(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))

        testString = "beset on all sides" + "".join(chr(c) for c in range(256))
        testLength = len(testString)

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, testLength)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(data, testLength + baseSize)], "allocated wrong")
            stringObject = Marshal.PtrToStructure(data, PyStringObject)
            self.assertEquals(stringObject.ob_refcnt, 1, "unexpected refcount")
            self.assertEquals(stringObject.ob_type, IntPtr.Zero, "unexpected type")
            self.assertEquals(stringObject.ob_size, testLength, "unexpected ob_size")
            self.assertEquals(stringObject.ob_shash, -1, "unexpected useless-field")
            self.assertEquals(stringObject.ob_sstate, 0, "unexpected useless-field")
            strDataPtr = OffsetPtr(data, Marshal.OffsetOf(PyStringObject, "ob_sval"))
            terminatorPtr = OffsetPtr(strDataPtr, testLength)
            self.assertEquals(Marshal.ReadByte(terminatorPtr), 0, "string not terminated")

            chars = testString.ToCharArray()
            bytes = Array.ConvertAll[Char, Byte](chars, lambda c: ord(c))
            Marshal.Copy(bytes, 0, strDataPtr, testLength)

            self.assertEquals(mapper.Retrieve(data), testString, "failed to read string data")

        finally:
            Marshal.FreeHGlobal(data)


class Python25Mapper__PyString_Resize_Test(unittest.TestCase):

    def testErrorHandling(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, 365)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, data)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(data, 365 + baseSize)], "allocated wrong")
            self.assertEquals(mapper._PyString_Resize(ptrPtr, 2000000000), -1, "bad return on error")
            self.assertEquals(type(mapper.LastException), OutOfMemoryException, "wrong exception type")
            self.assertTrue(data in frees, "did not deallocate")
        finally:
            if data not in frees:
                Marshal.FreeHGlobal(data)
            Marshal.FreeHGlobal(ptrPtr)


    def testShrink(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, 365)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, data)
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(data, 365 + baseSize)], "allocated wrong")
            self.assertEquals(mapper._PyString_Resize(ptrPtr, 20), 0, "bad return on success")
            stringObject = Marshal.PtrToStructure(data, PyStringObject)
            self.assertEquals(stringObject.ob_size, 20, "unexpected ob_size")
            strDataPtr = OffsetPtr(data, Marshal.OffsetOf(PyStringObject, "ob_sval"))
            terminatorPtr = OffsetPtr(strDataPtr, 20)
            self.assertEquals(Marshal.ReadByte(terminatorPtr), 0, "string not terminated")
            self.assertEquals(allocs, [(data, 365 + baseSize)], "unexpected extra alloc")
            self.assertEquals(frees, [], "unexpected frees")
        finally:
            Marshal.FreeHGlobal(data)
            Marshal.FreeHGlobal(ptrPtr)


    def testGrow(self):
        allocs = []
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, frees))

        data = mapper.PyString_FromStringAndSize(IntPtr.Zero, 365)
        ptrPtr = Marshal.AllocHGlobal(Marshal.SizeOf(IntPtr))
        Marshal.WriteIntPtr(ptrPtr, data)
        newData = IntPtr.Zero
        try:
            baseSize = Marshal.SizeOf(PyStringObject)
            self.assertEquals(allocs, [(data, 365 + baseSize)], "allocated wrong")
            self.assertEquals(mapper._PyString_Resize(ptrPtr, 2000), 0, "bad return on success")
            newData = Marshal.ReadIntPtr(ptrPtr)
            expectedAllocs = [(data, 365 + baseSize), (newData, 2000 + baseSize)]
            self.assertEquals(allocs, expectedAllocs,
                              "allocated wrong")
            self.assertEquals(frees, [data], "did not free unused memory")

            stringObject = Marshal.PtrToStructure(newData, PyStringObject)
            self.assertEquals(stringObject.ob_size, 2000, "unexpected ob_size")
            strDataPtr = OffsetPtr(newData, Marshal.OffsetOf(PyStringObject, "ob_sval"))
            terminatorPtr = OffsetPtr(strDataPtr, 2000)
            self.assertEquals(Marshal.ReadByte(terminatorPtr), 0, "string not terminated")
        finally:
            if data not in frees:
                Marshal.FreeHGlobal(data)
            Marshal.FreeHGlobal(ptrPtr)
            if newData != IntPtr.Zero and newData not in frees:
                Marshal.FreeHGlobal(newData)


class Python25Mapper_Exception_Test(unittest.TestCase):

    def testException(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        self.assertEquals(mapper.LastException, None, "exception should default to nothing")

        mapper.LastException = System.Exception("doozy")
        self.assertEquals(type(mapper.LastException), System.Exception,
                          "get should retrieve last set exception type")
        self.assertEquals(mapper.LastException.Message, "doozy",
                          "get should retrieve last set exception msg")



suite = makesuite(
    Python25MapperTest,
    Python25Mapper_Py_InitModule4_Test,
    Python25Mapper_PyArg_ParseTupleAndKeywords_Test,
    Python25Mapper_PyString_FromStringAndSize_Test,
    Python25Mapper__PyString_Resize_Test,
    Python25Mapper_Exception_Test,
)

if __name__ == '__main__':
    run(suite)