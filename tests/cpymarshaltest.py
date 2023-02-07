
from tests.utils.runtest import makesuite, run

from tests.utils.memory import OffsetPtr, PtrToStructure
from tests.utils.testcase import TestCase

from System import IntPtr, Int32, UInt32
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_int_ptrptrptr, DoubleStruct
from Ironclad.Structs import PyObject, PyFloatObject, PyIntObject, PyListObject, PyTypeObject


class CPyMarshalTest_32(TestCase):

    def testProperties(self):
        self.assertEquals(CPyMarshal.IntSize, 4)
        self.assertEquals(CPyMarshal.PtrSize, IntPtr.Size)


    def testOffset(self):
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), 123), IntPtr(477))
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), 0), IntPtr(354))
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), -123), IntPtr(231))
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), UInt32(123)), IntPtr(477))

        self.assertEquals(CPyMarshal.Offset(IntPtr(354), IntPtr(123)), IntPtr(477))
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), IntPtr(0)), IntPtr(354))


    def testZero(self):
        bufferlen = 200
        zerolen = 173
        
        data = Marshal.AllocHGlobal(bufferlen)
        this = data
        for _ in xrange(bufferlen):
            CPyMarshal.WriteByte(this, 255)
            this = OffsetPtr(this, 1)
        
        CPyMarshal.Zero(data, zerolen)
        
        this = data
        for i in xrange(bufferlen):
            actual = CPyMarshal.ReadByte(this)
            expected = (255, 0)[i < zerolen]
            self.assertEquals(actual, expected, "wrong value at %d (%d, %d)" % (i, actual, expected))
            this = OffsetPtr(this, 1)
            
        Marshal.FreeHGlobal(data)
    
    
    def testWritePtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyObject()))
        
        CPyMarshal.WritePtrField(data, PyObject, "ob_type", IntPtr(12345))
        dataStruct = PtrToStructure(data, PyObject)
        self.assertEquals(dataStruct.ob_type, IntPtr(12345), "failed to write")
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadPtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", IntPtr(12345))
        self.assertEquals(CPyMarshal.ReadPtrField(data, PyTypeObject, "tp_doc"), IntPtr(12345), "failed to read")
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteIntField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyIntObject()))
        
        for value in (Int32.MaxValue, Int32.MinValue):
            CPyMarshal.WriteIntField(data, PyIntObject, "ob_ival", value)
            dataStruct = PtrToStructure(data, PyIntObject)
            self.assertEquals(dataStruct.ob_ival, value, "failed to write")
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadIntField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyIntObject()))
        
        for value in (Int32.MaxValue, Int32.MinValue):
            CPyMarshal.WriteIntField(data, PyIntObject, "ob_ival", value)
            self.assertEquals(CPyMarshal.ReadIntField(data, PyIntObject, "ob_ival"), value, "failed to read")
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteUIntField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        
        for value in (UInt32.MaxValue, UInt32.MinValue):
            CPyMarshal.WriteUIntField(data, PyTypeObject, "tp_version_tag", value)
            dataStruct = PtrToStructure(data, PyTypeObject)
            self.assertEquals(dataStruct.tp_version_tag, value, "failed to write")
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadUIntField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        
        for value in (UInt32.MaxValue, UInt32.MinValue):
            CPyMarshal.WriteUIntField(data, PyTypeObject, "tp_version_tag", value)
            self.assertEquals(CPyMarshal.ReadUIntField(data, PyTypeObject, "tp_version_tag"), value, "failed to read")
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteDoubleField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyFloatObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyFloatObject()))
        
        CPyMarshal.WriteDoubleField(data, PyFloatObject, "ob_fval", 7.6e-5)
        dataStruct = PtrToStructure(data, PyFloatObject)
        self.assertEquals(dataStruct.ob_fval, 7.6e-5)
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadDoubleField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyFloatObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyFloatObject()))
        
        CPyMarshal.WriteDoubleField(data, PyFloatObject, "ob_fval", -1.2e34)
        self.assertEquals(CPyMarshal.ReadDoubleField(data, PyFloatObject, "ob_fval"), -1.2e34)
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteCStringField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        string = "Hey, I am a string. I have tricksy \\escapes\\."
        CPyMarshal.WriteCStringField(data, PyTypeObject, "tp_doc", string)
        
        self.assertEquals(CPyMarshal.ReadCStringField(data, PyTypeObject, "tp_doc"), string, "failed to read correctly")
        Marshal.FreeHGlobal(CPyMarshal.ReadPtrField(data, PyTypeObject, "tp_doc"))
        Marshal.FreeHGlobal(data)
    
    
    def testReadCStringField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        string = "Hey, I am a string. I have tricksy \\escapes\\."
        strPtr = Marshal.StringToHGlobalAnsi(string)
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", strPtr)
        
        self.assertEquals(CPyMarshal.ReadCStringField(data, PyTypeObject, "tp_doc"), string, "failed to read correctly")
        
        Marshal.FreeHGlobal(data)
        Marshal.FreeHGlobal(strPtr)
    
    
    def testReadCStringFieldEmpty(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", IntPtr.Zero)
        
        self.assertEquals(CPyMarshal.ReadCStringField(data, PyTypeObject, "tp_doc"), "", "failed to read correctly")
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteFunctionPtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        
        calls = []
        def TestFunc(selfPtr, argsPtr, kwargsPtr):
            calls.append((selfPtr, argsPtr, kwargsPtr))
            return 123
        self.testDgt = dgt_int_ptrptrptr(TestFunc)
        CPyMarshal.WriteFunctionPtrField(data, PyTypeObject, "tp_init", self.testDgt)
        
        writtenFP = CPyMarshal.ReadPtrField(data, PyTypeObject, "tp_init")
        writtenDgt = Marshal.GetDelegateForFunctionPointer(writtenFP, dgt_int_ptrptrptr)
        
        args = (IntPtr(111), IntPtr(222), IntPtr(333))
        self.assertEquals(writtenDgt(*args), 123, "not hooked up")
        self.assertEquals(calls, [args], "not hooked up")
        
    
    def testReadFunctionPtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject()))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject()))
        
        calls = []
        def TestFunc(selfPtr, argsPtr, kwargsPtr):
            calls.append((selfPtr, argsPtr, kwargsPtr))
            return 123
        self.testDgt = dgt_int_ptrptrptr(TestFunc)
        CPyMarshal.WriteFunctionPtrField(data, PyTypeObject, "tp_init", self.testDgt)
        
        readDgt = CPyMarshal.ReadFunctionPtrField(data, PyTypeObject, "tp_init", dgt_int_ptrptrptr)
        
        args = (IntPtr(111), IntPtr(222), IntPtr(333))
        self.assertEquals(readDgt(*args), 123, "not hooked up")
        self.assertEquals(calls, [args], "not hooked up")


    def testWritePtr(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        CPyMarshal.WritePtr(data, IntPtr(0))
        self.assertEquals(Marshal.ReadIntPtr(data), IntPtr(0), "wrong")

        CPyMarshal.WritePtr(data, IntPtr(100001))
        self.assertEquals(Marshal.ReadIntPtr(data), IntPtr(100001), "wrong")
        
        Marshal.FreeHGlobal(data)


    def testReadPtr(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        Marshal.WriteIntPtr(data, IntPtr(0))
        self.assertEquals(CPyMarshal.ReadPtr(data), IntPtr(0), "wrong")

        Marshal.WriteIntPtr(data, IntPtr(100001))
        self.assertEquals(CPyMarshal.ReadPtr(data), IntPtr(100001), "wrong")
        
        Marshal.FreeHGlobal(data)


    def testWriteInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.IntSize)
        
        CPyMarshal.WriteInt(data, 0)
        self.assertEquals(Marshal.ReadInt32(data), 0, "wrong")

        CPyMarshal.WriteInt(data, -1)
        self.assertEquals(Marshal.ReadInt32(data), -1, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testReadInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.IntSize)
        
        Marshal.WriteInt32(data, 0)
        self.assertEquals(CPyMarshal.ReadInt(data), 0, "wrong")

        Marshal.WriteInt32(data, -1)
        self.assertEquals(CPyMarshal.ReadInt(data), -1, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testWriteUInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.IntSize)
        
        CPyMarshal.WriteUInt(data, 0)
        self.assertEquals(Marshal.ReadInt32(data), 0, "wrong")

        CPyMarshal.WriteUInt(data, 0xFFFFFFFF)
        self.assertEquals(Marshal.ReadInt32(data), -1, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testReadUInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.IntSize)
        
        Marshal.WriteInt32(data, 0)
        self.assertEquals(CPyMarshal.ReadUInt(data), 0, "wrong")

        Marshal.WriteInt32(data, -1)
        self.assertEquals(CPyMarshal.ReadUInt(data), 0xFFFFFFFF, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testWriteDouble(self):
        data = Marshal.AllocHGlobal(CPyMarshal.DoubleSize)
        
        CPyMarshal.WriteDouble(data, 2.2e22)
        doubleStruct = PtrToStructure(data, DoubleStruct)
        self.assertEquals(doubleStruct.value, 2.2e22)
        
        Marshal.FreeHGlobal(data)


    def testReadDouble(self):
        data = Marshal.AllocHGlobal(CPyMarshal.DoubleSize)
        
        doubleStruct = DoubleStruct(2.2e22)
        Marshal.StructureToPtr(doubleStruct, data, False)
        self.assertEquals(CPyMarshal.ReadDouble(data), 2.2e22)
        
        Marshal.FreeHGlobal(data)


    def testWriteByte(self):
        data = Marshal.AllocHGlobal(1)
        
        CPyMarshal.WriteByte(data, 0)
        self.assertEquals(Marshal.ReadByte(data), 0, "wrong")

        CPyMarshal.WriteByte(data, 255)
        self.assertEquals(Marshal.ReadByte(data), 255, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testReadByte(self):
        data = Marshal.AllocHGlobal(1)
        
        Marshal.WriteByte(data, 0)
        self.assertEquals(CPyMarshal.ReadByte(data), 0, "wrong")

        Marshal.WriteByte(data, 255)
        self.assertEquals(CPyMarshal.ReadByte(data), 255, "wrong")
        
        Marshal.FreeHGlobal(data)




suite = makesuite(CPyMarshalTest_32)
if __name__ == '__main__':
    run(suite)

