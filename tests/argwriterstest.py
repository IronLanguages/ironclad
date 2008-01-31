
import unittest

from System import Int32, IntPtr
from System.Runtime.InteropServices import Marshal


ptrSize = Marshal.SizeOf(IntPtr)
intSize = Marshal.SizeOf(Int32)

class ArgWritersTest(unittest.TestCase):

    def testSizedStringArgWriter(self):
        writer = SizedStringArgWriter(0)
        expectedSize = ptrSize * 2
        self.assertEquals(writer.Size, expectedSize, "bad writer size")


    def testIntArgWriter(self):
        writer = IntArgWriter(0)
        expectedSize = ptrSize
        self.assertEquals(writer.Size, expectedSize, "bad writer size")


    def testIntArgWriterWrite(self):
        numWrites = 4
        destPtrs = Marshal.AllocHGlobal(ptrSize * numWrites)
        destPtrsList = []
        for writeNum in range(numWrites):
            destPtrsList.append(Marshal.AllocHGlobal(intSize))
            Marshal.WriteIntPtr(IntPtr(destPtrs.ToInt32() + (writeNum * ptrSize)),
                                destPtrsList[-1])
        try:
            for writeNum in range(numWrites):
                writer = IntArgWriter(writeNum)
                writer.Write(destPtrs, writeNum ** 3)
                self.assertEquals(Marshal.ReadInt32(destPtrsList[writeNum]), writeNum ** 3,
                                  "bad ptr table")
        finally:
            for n in range(numWrites):
                Marshal.FreeHGlobal(destPtrsList[n])
            Marshal.FreeHGlobal(destPtrs)



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(ArgWritersTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)