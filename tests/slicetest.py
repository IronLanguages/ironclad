
import types

from tests.utils.runtest import makesuite, run
from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Api, Python25Mapper
from Ironclad.Structs import PyObject, PySliceObject, PyTypeObject

        
class SliceTest(TestCase):
    
    def testStoreSlice(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        obj = slice(1, 2, 3)
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.RefCount(objPtr), 1)
        self.assertEquals(mapper.Retrieve(objPtr), obj)
        
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PySliceObject, "ob_type"), mapper.PySlice_Type)
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PySliceObject, "ob_refcnt"), 1)
        
        startPtr = CPyMarshal.ReadPtrField(objPtr, PySliceObject, "start")
        self.assertEquals(mapper.Retrieve(startPtr), 1)
        mapper.IncRef(startPtr)
        stopPtr = CPyMarshal.ReadPtrField(objPtr, PySliceObject, "stop")
        self.assertEquals(mapper.Retrieve(stopPtr), 2)
        mapper.IncRef(stopPtr)
        stepPtr = CPyMarshal.ReadPtrField(objPtr, PySliceObject, "step")
        self.assertEquals(mapper.Retrieve(stepPtr), 3)
        mapper.IncRef(stepPtr)
        
        mapper.DecRef(objPtr)
        self.assertEquals(mapper.RefCount(startPtr), 1)
        self.assertEquals(mapper.RefCount(stopPtr), 1)
        self.assertEquals(mapper.RefCount(stepPtr), 1)
        
        mapper.Dispose()
        deallocTypes()


    def testPySlice_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        mapper = Python25Mapper(GetAllocatingTestAllocator([], frees))
        deallocTypes = CreateTypes(mapper)
        
        calls = []
        def CustomFree(ptr):
            calls.append(ptr)
        freeDgt = Python25Api.PyObject_Free_Delegate(CustomFree)
        
        CPyMarshal.WriteFunctionPtrField(mapper.PySlice_Type, PyTypeObject, "tp_free", freeDgt)
        slicePtr = mapper.Store(slice(1, 2, 3))
        
        del frees[:]
        mapper.PySlice_Dealloc(slicePtr)
        self.assertEquals(len(frees), 3, "did not dealloc each item")
        self.assertEquals(calls, [slicePtr], "did not call type's free function")
        mapper.PyObject_Free(slicePtr)

        mapper.Dispose()
        deallocTypes()


    def testCreateEllipsis(self):
        mapper = Python25Mapper()
        ellipsisTypePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        ellipsisPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        mapper.SetData("PyEllipsis_Type", ellipsisTypePtr)
        mapper.SetData("_Py_EllipsisObject", ellipsisPtr)
        
        self.assertEquals(CPyMarshal.ReadPtrField(ellipsisPtr, PyObject, "ob_type"), mapper.PyEllipsis_Type)
        self.assertEquals(CPyMarshal.ReadIntField(ellipsisPtr, PyObject, "ob_refcnt"), 1)
        
        self.assertEquals(mapper.Store(Ellipsis), ellipsisPtr)
        self.assertEquals(mapper.RefCount(ellipsisPtr), 2)
        
        mapper.Dispose()
        Marshal.FreeHGlobal(ellipsisPtr)
        Marshal.FreeHGlobal(ellipsisTypePtr)


suite = makesuite(
    SliceTest,
)
if __name__ == '__main__':
    run(suite)