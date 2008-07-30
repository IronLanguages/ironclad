
from tests.utils.runtest import makesuite, run

from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPython_destructor_Delegate, OpaquePyCObject, Python25Api, Python25Mapper
from Ironclad.Structs import PyCObject, PyObject, PyTypeObject

class CObjectTest(TestCase):
    
    def testPyCObject(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        cobjData = Marshal.AllocHGlobal(32)
        cobjPtr = mapper.PyCObject_FromVoidPtr(cobjData, IntPtr.Zero)
        
        self.assertEquals(CPyMarshal.ReadPtrField(cobjPtr, PyObject, 'ob_type'), mapper.PyCObject_Type, 'wrong type')
        self.assertEquals(mapper.RefCount(cobjPtr), 2, 'wrong refcount')
        self.assertEquals(mapper.PyCObject_AsVoidPtr(cobjPtr), cobjData, 'wrong pointer stored')
        
        self.assertEquals(isinstance(mapper.Retrieve(cobjPtr), OpaquePyCObject), True, "wrong")
        
        Marshal.FreeHGlobal(cobjData)
        mapper.Dispose()
        deallocTypes()


    
    def testPyCObjectWithDestructor(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        calls = []
        def destructor(destructee):
            calls.append(destructee)
        self.destructorDgt = CPython_destructor_Delegate(destructor)
        
        cobjData = Marshal.AllocHGlobal(32)
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
        
        Marshal.FreeHGlobal(cobjData)
        mapper.Dispose()
        deallocTypes()
    



class PyCObject_Type_Test(TypeTestCase):
        
    def testPyCObject_Dealloc(self):
        VOID_PTR = IntPtr(12345)
        
        def CreateInstance(mapper, calls):
            def destroy(cobj):
                calls.append(("destroy", cobj))
            self.destroyDgt = CPython_destructor_Delegate(destroy)
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