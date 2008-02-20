
import unittest
from tests.utils.runtest import makesuite, run

import System
from System import IntPtr
from System.Collections.Generic import Dictionary
from System.Runtime.InteropServices import Marshal
from JumPy import (
    ArgWriter, CPyMarshal, CStringArgWriter, IntArgWriter,
    ObjectArgWriter, Python25Mapper, SizedStringArgWriter
)
from IronPython.Hosting import PythonEngine


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
        self.assertGetArgWritersProduces("i;an error message", [(0, IntArgWriter, 1)])
        self.assertGetArgWritersProduces("iii", [(0, IntArgWriter, 1),
                                                 (1, IntArgWriter, 2),
                                                 (2, IntArgWriter, 3),])
        self.assertGetArgWritersProduces("ii|i", [(0, IntArgWriter, 1),
                                                  (1, IntArgWriter, 2),
                                                  (2, IntArgWriter, 3),])

        self.assertGetArgWritersProduces("s#", [(0, SizedStringArgWriter, 2)])
        self.assertGetArgWritersProduces("s#s", [(0, SizedStringArgWriter, 2),
                                                 (1, CStringArgWriter, 3)])
        self.assertGetArgWritersProduces("ss#", [(0, CStringArgWriter, 1),
                                                 (1, SizedStringArgWriter, 3)])
        self.assertGetArgWritersProduces("s#i", [(0, SizedStringArgWriter, 2),
                                                 (1, IntArgWriter, 3)])
        self.assertGetArgWritersProduces("|s#i", [(0, SizedStringArgWriter, 2),
                                                  (1, IntArgWriter, 3)])

        self.assertGetArgWritersProduces("iOs#", [(0, IntArgWriter, 1),
                                                  (1, ObjectArgWriter, 2),
                                                  (2, SizedStringArgWriter, 4)])

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





suite = makesuite(
    Python25Mapper_PyArg_ParseTuple_Test,
    Python25Mapper_PyArg_ParseTupleAndKeywords_Test,
)

if __name__ == '__main__':
    run(suite)