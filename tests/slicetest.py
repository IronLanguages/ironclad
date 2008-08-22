
import types

from tests.utils.runtest import makesuite, run
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject

        
class SliceTest(TestCase):
    
    def testStoreSlice(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        obj = slice(1, 2, 3)
        objPtr = mapper.Store(obj)
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type"), mapper.PySlice_Type)
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PyObject, "ob_refcnt"), 1)
        self.assertEquals(mapper.Retrieve(objPtr), obj)
        
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