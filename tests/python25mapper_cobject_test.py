
from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPython_destructor_Delegate, OpaquePyCObject, Python25Api, Python25Mapper
from Ironclad.Structs import PyCObject, PyObject, PyTypeObject

class Python25Mapper_PyCObject_Test(TestCase):
    
    def testPyCObject_FromVoidPtr(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        cobj = Marshal.AllocHGlobal(32)
        cobjPtr = mapper.PyCObject_FromVoidPtr(cobj, IntPtr.Zero)
        
        self.assertEquals(CPyMarshal.ReadPtrField(cobjPtr, PyObject, 'ob_type'), mapper.PyCObject_Type, 'wrong type')
        self.assertEquals(mapper.RefCount(cobjPtr), 1, 'wrong refcount')
        
        self.assertEquals(isinstance(mapper.Retrieve(cobjPtr), OpaquePyCObject), True, "wrong")
        
        mapper.Dispose()
        deallocTypes()


    
    def testPyCObject_FromVoidPtr_WithDestructor(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        calls = []
        def destructor(destructee):
            calls.append(destructee)
        self.destructorDgt = CPython_destructor_Delegate(destructor)
        
        cobj = Marshal.AllocHGlobal(32)
        cobjPtr = mapper.PyCObject_FromVoidPtr(cobj, Marshal.GetFunctionPointerForDelegate(self.destructorDgt))
        
        self.assertEquals(CPyMarshal.ReadPtrField(cobjPtr, PyObject, 'ob_type'), mapper.PyCObject_Type, 'wrong type')
        self.assertEquals(mapper.RefCount(cobjPtr), 1, 'wrong refcount')
        self.assertEquals(calls, [], "destroyed early")
        
        mapper.DecRef(cobjPtr)
        self.assertEquals(calls, [cobj], "failed to destroy")
        
        Marshal.FreeHGlobal(cobj)
        mapper.Dispose()
        deallocTypes()
    



class Python25Mapper_PyCObject_TypeTest(TypeTestCase):
        
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
    Python25Mapper_PyCObject_Test,
    Python25Mapper_PyCObject_TypeTest
)

if __name__ == '__main__':
    run(suite)