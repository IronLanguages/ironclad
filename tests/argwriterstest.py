
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr

from System.Runtime.InteropServices import Marshal

from IronPython.Hosting import PythonEngine

from Ironclad import (
    CPyMarshal, CStringArgWriter, IntArgWriter, ObjectArgWriter,
    Python25Mapper, SizedStringArgWriter
)


def GetSetter(item, attr, value):
    def Setter():
        setattr(item, attr, value)
    return Setter

class ArgWriterSizeTest(unittest.TestCase):

    def testIntArgWriter(self):
        writer = IntArgWriter(3)
        self.assertEquals(writer.PointersConsumed, 1, "bad writer size")
        self.assertEquals(writer.NextWriterStartIndex, 3 + 1, "bad next writer start")
        self.assertRaises(Exception, GetSetter(writer, "PointersConsumed", 6))
        self.assertRaises(Exception, GetSetter(writer, "NextWriterStartIndex", 6))

    def testObjectArgWriter(self):
        writer = ObjectArgWriter(3, Python25Mapper(PythonEngine()))
        self.assertEquals(writer.PointersConsumed, 1, "bad writer size")
        self.assertEquals(writer.NextWriterStartIndex, 3 + 1, "bad next writer start")
        self.assertRaises(Exception, GetSetter(writer, "PointersConsumed", 6))
        self.assertRaises(Exception, GetSetter(writer, "NextWriterStartIndex", 6))

    def testCStringArgWriter(self):
        writer = CStringArgWriter(3, Python25Mapper(PythonEngine()))
        self.assertEquals(writer.PointersConsumed, 1, "bad writer size")
        self.assertEquals(writer.NextWriterStartIndex, 3 + 1, "bad next writer start")
        self.assertRaises(Exception, GetSetter(writer, "PointersConsumed", 6))
        self.assertRaises(Exception, GetSetter(writer, "NextWriterStartIndex", 6))

    def testSizedStringArgWriter(self):
        writer = SizedStringArgWriter(3, Python25Mapper(PythonEngine()))
        self.assertEquals(writer.PointersConsumed, 2, "bad writer size")
        self.assertEquals(writer.NextWriterStartIndex, 3 + 2, "bad next writer start")
        self.assertRaises(Exception, GetSetter(writer, "PointersConsumed", 6))
        self.assertRaises(Exception, GetSetter(writer, "NextWriterStartIndex", 6))


class ArgWriterWriteTest(unittest.TestCase):

    def assertWritesIntToAddress(self, writer, writeValue, expectedValue, ptrsAddress, dstAddress):
        writer.Write(ptrsAddress, writeValue)
        self.assertEquals(CPyMarshal.ReadInt(dstAddress), expectedValue,
                          "int write incorrect")


    def assertWritesStringToAddress(self, writer, string, ptrsAddress, dstAddress):
        writer.Write(ptrsAddress, string)
        ptr = CPyMarshal.ReadPtr(dstAddress)

        for c in string:
            self.assertEquals(CPyMarshal.ReadByte(ptr), ord(c), "mismatched character")
            ptr = OffsetPtr(ptr, 1)
        self.assertEquals(CPyMarshal.ReadByte(ptr), 0, "missing terminator")


class IntArgWriterTest(ArgWriterWriteTest):

    def testIntArgWriterWrite(self):
        destPtrs = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 4)
        dest = Marshal.AllocHGlobal(CPyMarshal.IntSize)
        CPyMarshal.WritePtr(OffsetPtr(destPtrs, (2 * CPyMarshal.PtrSize)), dest)
        try:
            self.assertWritesIntToAddress(
                IntArgWriter(2), 12345, 12345, destPtrs, dest)
        finally:
            Marshal.FreeHGlobal(dest)
            Marshal.FreeHGlobal(destPtrs)


class ObjectArgWriterTest(ArgWriterWriteTest):

    def testWritesObjectPtr(self):
        destPtrs = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 4)
        dest = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        CPyMarshal.WritePtr(OffsetPtr(destPtrs, (2 * CPyMarshal.PtrSize)), dest)
        mapper = Python25Mapper(PythonEngine())
        obj = object()

        try:
            ObjectArgWriter(2, mapper).Write(destPtrs, obj)
            objPtr = CPyMarshal.ReadPtr(dest)
            self.assertEquals(mapper.RefCount(objPtr), 1, "did not store object ptr")
            self.assertEquals(mapper.Retrieve(objPtr), obj, "stored wrong object")

            mapper.FreeTemps()
            self.assertEquals(mapper.RefCount(objPtr), 0, "did not clean up temporary object ptr")
        finally:
            Marshal.FreeHGlobal(dest)
            Marshal.FreeHGlobal(destPtrs)
            mapper.FreeTemps()


class CStringArgWriterTest(ArgWriterWriteTest):

    def assertCStringArgWriterWrite(self, string):
        destPtrs = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 4)
        destStr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        CPyMarshal.WritePtr(OffsetPtr(destPtrs, (2 * CPyMarshal.PtrSize)), destStr)
        frees = []
        tempStrings = []
        mapper = Python25Mapper(PythonEngine(), GetAllocatingTestAllocator([], frees))
        try:
            self.assertWritesStringToAddress(
                CStringArgWriter(2, mapper), string, destPtrs, destStr)
            tempStrings.append(Marshal.ReadIntPtr(destStr))
        finally:
            Marshal.FreeHGlobal(destStr)
            Marshal.FreeHGlobal(destPtrs)
            mapper.FreeTemps()
        self.assertEquals(set(frees), set(tempStrings),
                          "failed to deallocate temporary buffers when instructed")

    def testWriteEasyString(self):
        s = "Lock the cellar door"
        self.assertCStringArgWriterWrite(s)

    def testWriteTrickyString(self):
        s = ''.join(chr(c) for c in range(1, 256))
        self.assertCStringArgWriterWrite(s)

    def testWriteInvalidString_EmbeddedNull(self):
        s = u'I contain an embedded \0. Hahaha!'
        self.assertRaises(TypeError,
            lambda: self.assertCStringArgWriterWrite(s))

    def testWriteInvalidString_Unicode(self):
        s = u'ph34r my pron\u0639nciation'
        self.assertRaises(UnicodeError,
            lambda: self.assertCStringArgWriterWrite(s))


class SizedStringArgWriterTest(ArgWriterWriteTest):

    def assertSizedStringArgWriterWrite(self, string, length):
        destPtrs = Marshal.AllocHGlobal(CPyMarshal.PtrSize * 4)
        destStr = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        CPyMarshal.WritePtr(OffsetPtr(destPtrs, (2 * CPyMarshal.PtrSize)), destStr)
        destInt = Marshal.AllocHGlobal(CPyMarshal.IntSize)
        CPyMarshal.WritePtr(OffsetPtr(destPtrs, (3 * CPyMarshal.PtrSize)), destInt)
        frees = []
        tempStrings = []
        mapper = Python25Mapper(PythonEngine(), GetAllocatingTestAllocator([], frees))
        try:
            self.assertWritesStringToAddress(
                SizedStringArgWriter(2, mapper), string, destPtrs, destStr)
            tempStrings.append(Marshal.ReadIntPtr(destStr))
            self.assertWritesIntToAddress(
                SizedStringArgWriter(2, mapper), string, length, destPtrs, destInt)
            tempStrings.append(Marshal.ReadIntPtr(destStr))
        finally:
            Marshal.FreeHGlobal(destStr)
            Marshal.FreeHGlobal(destInt)
            Marshal.FreeHGlobal(destPtrs)
            mapper.FreeTemps()
        self.assertEquals(set(frees), set(tempStrings),
                          "failed to deallocate temporary buffers when instructed")

    def testWriteEasyString(self):
        s = "Lock the cellar door"
        self.assertSizedStringArgWriterWrite(s, len(s))

    def testWriteTrickyString(self):
        s = ''.join(chr(c) for c in range(256))
        self.assertSizedStringArgWriterWrite(s, len(s))

    def testWriteInvalidString(self):
        s = u'ph34r my pron\u0639nciation'
        self.assertRaises(UnicodeError,
            lambda: self.assertSizedStringArgWriterWrite(s, len(s)))


suite = makesuite(
    ArgWriterSizeTest,
    IntArgWriterTest,
    ObjectArgWriterTest,
    CStringArgWriterTest,
    SizedStringArgWriterTest
)

if __name__ == '__main__':
    run(suite)