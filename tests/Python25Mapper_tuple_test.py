
import unittest
from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr
from tests.utils.runtest import makesuite, run

from System.Runtime.InteropServices import Marshal

from IronPython.Hosting import PythonEngine
from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyTupleObject

class Python25Mapper_Tuple_Test(unittest.TestCase):
    
    
    def assertPyTuple_New_Works(self, length):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        
        typeBlock = Marshal.AllocHGlobal(CPyMarshal.PtrSize)
        try:
            mapper.SetData("PyTuple_Type", typeBlock)

            tuplePtr = mapper.PyTuple_New(length)
            try:
                expectedSize = Marshal.SizeOf(PyTupleObject) + (CPyMarshal.PtrSize * (length - 1))
                self.assertEquals(allocs, [(tuplePtr, expectedSize)], "bad alloc")
                tupleStruct = Marshal.PtrToStructure(tuplePtr, PyTupleObject)
                self.assertEquals(tupleStruct.ob_refcnt, 1, "bad refcount")
                self.assertEquals(tupleStruct.ob_type, mapper.PyTuple_Type, "bad type")
                self.assertEquals(tupleStruct.ob_size, length, "bad size")

                dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
                itemPtrs = []
                for i in range(length):
                    itemPtr = mapper.Store(i + 100)
                    CPyMarshal.WritePtr(dataPtr, itemPtr)
                    itemPtrs.append(itemPtr)
                    dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
                
                try:
                    immutableTuple = mapper.Retrieve(tuplePtr)
                    self.assertEquals(immutableTuple, tuple(i + 100 for i in range(length)), "broken")
                finally:
                    for itemPtr in itemPtrs:
                        mapper.DecRef(itemPtr)
            finally:
                mapper.DecRef(tuplePtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)
    
    
    def testPyTuple_New(self):
        self.assertPyTuple_New_Works(1)
        self.assertPyTuple_New_Works(3)



suite = makesuite(
    Python25Mapper_Tuple_Test,
)

if __name__ == '__main__':
    run(suite)