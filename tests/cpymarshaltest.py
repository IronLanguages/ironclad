
import unittest
from tests.utils.runtest import makesuite, run

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from JumPy import CPyMarshal

class CPyMarshalTest_32(unittest.TestCase):

    def testProperties(self):
        self.assertEquals(CPyMarshal.IntSize, 4, "wrong")
        self.assertEquals(CPyMarshal.PtrSize, 4, "wrong")


    def testOffset(self):
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), 123), IntPtr(477), "wrong")
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), 0), IntPtr(354), "wrong")
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), -123), IntPtr(231), "wrong")

        self.assertEquals(CPyMarshal.Offset(IntPtr(354), IntPtr(123)), IntPtr(477), "wrong")
        self.assertEquals(CPyMarshal.Offset(IntPtr(354), IntPtr(0)), IntPtr(354), "wrong")



    def testWritePtr(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            CPyMarshal.WritePtr(data, IntPtr(0))
            self.assertEquals(Marshal.ReadIntPtr(data), IntPtr(0), "wrong")

            CPyMarshal.WritePtr(data, IntPtr(100001))
            self.assertEquals(Marshal.ReadIntPtr(data), IntPtr(100001), "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testReadPtr(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            Marshal.WriteIntPtr(data, IntPtr(0))
            self.assertEquals(CPyMarshal.ReadPtr(data), IntPtr(0), "wrong")

            Marshal.WriteIntPtr(data, IntPtr(100001))
            self.assertEquals(CPyMarshal.ReadPtr(data), IntPtr(100001), "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testWriteInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            CPyMarshal.WriteInt(data, 0)
            self.assertEquals(Marshal.ReadInt32(data), 0, "wrong")

            CPyMarshal.WriteInt(data, -1)
            self.assertEquals(Marshal.ReadInt32(data), -1, "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testReadInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            Marshal.WriteInt32(data, 0)
            self.assertEquals(CPyMarshal.ReadInt(data), 0, "wrong")

            Marshal.WriteInt32(data, -1)
            self.assertEquals(CPyMarshal.ReadInt(data), -1, "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testWriteUInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            CPyMarshal.WriteUInt(data, 0)
            self.assertEquals(Marshal.ReadInt32(data), 0, "wrong")

            CPyMarshal.WriteUInt(data, 0xFFFFFFFF)
            self.assertEquals(Marshal.ReadInt32(data), -1, "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testReadUInt(self):
        data = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            Marshal.WriteInt32(data, 0)
            self.assertEquals(CPyMarshal.ReadUInt(data), 0, "wrong")

            Marshal.WriteInt32(data, -1)
            self.assertEquals(CPyMarshal.ReadUInt(data), 0xFFFFFFFF, "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testWriteByte(self):
        data = Marshal.AllocHGlobal(1)
        try:
            CPyMarshal.WriteByte(data, 0)
            self.assertEquals(Marshal.ReadByte(data), 0, "wrong")

            CPyMarshal.WriteByte(data, 255)
            self.assertEquals(Marshal.ReadByte(data), 255, "wrong")
        finally:
            Marshal.FreeHGlobal(data)


    def testReadByte(self):
        data = Marshal.AllocHGlobal(1)
        try:
            Marshal.WriteByte(data, 0)
            self.assertEquals(CPyMarshal.ReadByte(data), 0, "wrong")

            Marshal.WriteByte(data, 255)
            self.assertEquals(CPyMarshal.ReadByte(data), 255, "wrong")
        finally:
            Marshal.FreeHGlobal(data)




suite = makesuite(CPyMarshalTest_32)
if __name__ == '__main__':
    run(suite)

