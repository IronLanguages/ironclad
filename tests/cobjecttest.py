
from tests.utils.runtest import makesuite, run

from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, dgt_void_ptr, OpaquePyCObject, Python25Api, Python25Mapper
from Ironclad.Structs import PyCObject, PyObject, PyTypeObject

class CObjectTest(TestCase):
    
    @WithMapper
    def testPyCObject(self, mapper, addToCleanUp):
        cobjData = Marshal.AllocHGlobal(32)
        addToCleanUp(lambda: Marshal.FreeHGlobal(cobjData))

        cobjPtr = mapper.PyCObject_FromVoidPtr(cobjData, IntPtr.Zero)
        
        self.assertEquals(CPyMarshal.ReadPtrField(cobjPtr, PyObject, 'ob_type'), mapper.PyCObject_Type, 'wrong type')
        self.assertEquals(mapper.RefCount(cobjPtr), 2, 'wrong refcount')
        self.assertEquals(mapper.PyCObject_AsVoidPtr(cobjPtr), cobjData, 'wrong pointer stored')
        
        self.assertEquals(isinstance(mapper.Retrieve(cobjPtr), OpaquePyCObject), True, "wrong")

    
    @WithMapper
    def testPyCObjectWithDestructor(self, mapper, addToCleanUp):
        calls = []
        def destructor(destructee):
            calls.append(destructee)
        self.destructorDgt = dgt_void_ptr(destructor)
        
        cobjData = Marshal.AllocHGlobal(32)
        addToCleanUp(lambda: Marshal.FreeHGlobal(cobjData))

        cobjPtr = mapper.PyCObject_FromVoidPtr(cobjData, Marshal.GetFunctionPointerForDelegate(self.destructorDgt))
        cobj = mapper.Retrieve(cobjPtr)
        
        self.assertEquals(CPyMarshal.ReadPtrField(cobjPtr, PyObject, 'ob_type'), mapper.PyCObject_Type, 'wrong type')
        self.assertEquals(mapper.RefCount(cobjPtr), 2, 'wrong refcount')
        self.assertEquals(mapper.PyCObject_AsVoidPtr(cobjPtr), cobjData, 'wrong pointer stored')
        
        del cobj
        gcwait()
        self.assertEquals(calls, [], "destroyed early")
        
        cobj = mapper.Retrieve(cobjPtr)
        mapper.DecRef(cobjPtr)
        self.assertEquals(calls, [], "destroyed early")
        
        del cobj
        gcwait()
        self.assertEquals(calls, [cobjData], "failed to destroy")
        

class PyCObject_Type_Test(TypeTestCase):
        
    def testIC_PyCObject_Dealloc(self):
        VOID_PTR = IntPtr(12345)
        
        def CreateInstance(mapper, calls):
            def destroy(cobj):
                calls.append(("destroy", cobj))
            self.destroyDgt = dgt_void_ptr(destroy)
            cobjPtr = mapper.PyCObject_FromVoidPtr(VOID_PTR, Marshal.GetFunctionPointerForDelegate(self.destroyDgt))
            return cobjPtr
        
        def TestConsequences(_, cobjPtr, calls):
            self.assertEquals(calls, [("destroy", VOID_PTR), ("tp_free", cobjPtr)], "wrong calls")
        
        self.assertTypeDeallocWorks("PyCObject_Type", Python25Mapper, CreateInstance, TestConsequences)
        
    
    def testPyCObject_tp_free(self):
        self.assertUsual_tp_free("PyCObject_Type")



suite = makesuite(
    CObjectTest,
    PyCObject_Type_Test
)

if __name__ == '__main__':
    run(suite)
