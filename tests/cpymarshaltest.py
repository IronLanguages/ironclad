
from tests.utils.runtest import makesuite, run

from tests.utils.memory import OffsetPtr
from tests.utils.testcase import TestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPython_initproc_Delegate
from Ironclad.Structs import PyObject, PyTypeObject

class CPyMarshalTest_32(TestCase):

    def testProperties(self):
        self.assertEquals(CPyMarshal.IntSize, 4, "wrong")
        self.assertEquals(CPyMarshal.PtrSize, 4, "wrong")


    def testOffset(self):
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), 123), IntPtr(477), "wrong")
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), 0), IntPtr(354), "wrong")
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), -123), IntPtr(231), "wrong")

        self.assertEquals(CPyMarshal.Offset(IntPtr(354), IntPtr(123)), IntPtr(477), "wrong")
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), IntPtr(0)), IntPtr(354), "wrong")


    def testZero(self):
        bytes = 200
        data = Marshal.AllocHGlobal(bytes)
        
        this = data
        for _ in xrange(bytes):
            CPyMarshal.WriteByte(this, 255)
            this = OffsetPtr(this, 1)
        
        CPyMarshal.Zero(data, bytes)
        
        this = data
        for _ in xrange(bytes):
            self.assertEquals(CPyMarshal.ReadByte(this), 0, "failed to zero")
            this = OffsetPtr(this, 1)
            
        Marshal.FreeHGlobal(data)
    
    
    def testWritePtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject))
        
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", IntPtr(12345))
        dataStruct = Marshal.PtrToStructure(data, PyTypeObject)
        self.assertEquals(dataStruct.tp_doc, IntPtr(12345), "failed to write")
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadPtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject))
        
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", IntPtr(12345))
        self.assertEquals(CPyMarshal.ReadPtrField(data, PyTypeObject, "tp_doc"), IntPtr(12345), "failed to read")
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteIntField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyObject))
        
        CPyMarshal.WriteIntField(data, PyObject, "ob_refcnt", 123)
        dataStruct = Marshal.PtrToStructure(data, PyObject)
        self.assertEquals(dataStruct.ob_refcnt, 123, "failed to write")
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadIntField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyObject))
        
        CPyMarshal.WriteIntField(data, PyObject, "ob_refcnt", 123)
        self.assertEquals(CPyMarshal.ReadIntField(data, PyObject, "ob_refcnt"), 123, "failed to read")
        
        Marshal.FreeHGlobal(data)
    
    
    def testReadCStringField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject))
        string = "Hey, I am a string. I have tricksy \\escapes\\."
        strPtr = Marshal.StringToHGlobalAnsi(string)
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", strPtr)
        
        self.assertEquals(CPyMarshal.ReadCStringField(data, PyTypeObject, "tp_doc"), string, "failed to read correctly")
        
        Marshal.FreeHGlobal(data)
        Marshal.FreeHGlobal(strPtr)
    
    
    def testReadCStringFieldEmpty(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject))
        CPyMarshal.WritePtrField(data, PyTypeObject, "tp_doc", IntPtr.Zero)
        
        self.assertEquals(CPyMarshal.ReadCStringField(data, PyTypeObject, "tp_doc"), "", "failed to read correctly")
        
        Marshal.FreeHGlobal(data)
    
    
    def testWriteFunctionPtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject))
        
        calls = []
        def TestFunc(selfPtr, argsPtr, kwargsPtr):
            calls.append((selfPtr, argsPtr, kwargsPtr))
            return 123
        self.testDgt = CPython_initproc_Delegate(TestFunc)
        CPyMarshal.WriteFunctionPtrField(data, PyTypeObject, "tp_init", self.testDgt)
        
        writtenFP = CPyMarshal.ReadPtrField(data, PyTypeObject, "tp_init")
        writtenDgt = Marshal.GetDelegateForFunctionPointer(writtenFP, CPython_initproc_Delegate)
        
        args = (IntPtr(111), IntPtr(222), IntPtr(333))
        self.assertEquals(writtenDgt(*args), 123, "not hooked up")
        self.assertEquals(calls, [args], "not hooked up")
        
    
    def testReadFunctionPtrField(self):
        data = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        CPyMarshal.Zero(data, Marshal.SizeOf(PyTypeObject))
        
        calls = []
        def TestFunc(selfPtr, argsPtr, kwargsPtr):
            calls.append((selfPtr, argsPtr, kwargsPtr))
            return 123
        self.testDgt = CPython_initproc_Delegate(TestFunc)
        CPyMarshal.WriteFunctionPtrField(data, PyTypeObject, "tp_init", self.testDgt)
        
        readDgt = CPyMarshal.ReadFunctionPtrField(data, PyTypeObject, "tp_init", CPython_initproc_Delegate)
        
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
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        CPyMarshal.WriteInt(data, 0)
        self.assertEquals(Marshal.ReadInt32(data), 0, "wrong")

        CPyMarshal.WriteInt(data, -1)
        self.assertEquals(Marshal.ReadInt32(data), -1, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testReadInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        Marshal.WriteInt32(data, 0)
        self.assertEquals(CPyMarshal.ReadInt(data), 0, "wrong")

        Marshal.WriteInt32(data, -1)
        self.assertEquals(CPyMarshal.ReadInt(data), -1, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testWriteUInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        CPyMarshal.WriteUInt(data, 0)
        self.assertEquals(Marshal.ReadInt32(data), 0, "wrong")

        CPyMarshal.WriteUInt(data, 0xFFFFFFFF)
        self.assertEquals(Marshal.ReadInt32(data), -1, "wrong")
        
        Marshal.FreeHGlobal(data)


    def testReadUInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        
        Marshal.WriteInt32(data, 0)
        self.assertEquals(CPyMarshal.ReadUInt(data), 0, "wrong")

        Marshal.WriteInt32(data, -1)
        self.assertEquals(CPyMarshal.ReadUInt(data), 0xFFFFFFFF, "wrong")
        
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

