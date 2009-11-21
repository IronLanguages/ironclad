
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from Ironclad import CPyMarshal, dgt_void_ptr, PythonMapper
from Ironclad.Structs import PyTypeObject


class TypeTestCase(TestCase):

    def assertTypeDeallocWorks(self, typename, CreateMapper, CreateInstance, TestConsequences):
        mapper = CreateMapper()
        deallocTypes = CreateTypes(mapper)

        calls = []
        def tp_free(ptr):
            calls.append(("tp_free", ptr))
        self.tp_freeDgt = dgt_void_ptr(tp_free)
        CPyMarshal.WriteFunctionPtrField(getattr(mapper, typename), PyTypeObject, "tp_free", self.tp_freeDgt)

        objPtr = CreateInstance(mapper, calls)
        deallocDgt = CPyMarshal.ReadFunctionPtrField(
            getattr(mapper, typename), PyTypeObject, "tp_dealloc", dgt_void_ptr)
        deallocDgt(objPtr)

        TestConsequences(mapper, objPtr, calls)
        mapper.Dispose()
        deallocTypes()
    
    
    def assertUsual_tp_free(self, typename):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        
        tp_freePtr = CPyMarshal.ReadPtrField(
            getattr(mapper, typename), PyTypeObject, "tp_free")
        self.assertEquals(tp_freePtr, mapper.GetFuncPtr("PyObject_Free"), "wrong tp_free for " + typename)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def assertUsual_tp_dealloc(self, typename):
        mapper = PythonMapper()
        deallocTypes = CreateTypes(mapper)
        
        tp_deallocPtr = CPyMarshal.ReadPtrField(
            getattr(mapper, typename), PyTypeObject, "tp_dealloc")
        self.assertEquals(tp_deallocPtr, mapper.GetFuncPtr("IC_PyBaseObject_Dealloc"), "wrong tp_dealloc for " + typename)
        
        mapper.Dispose()
        deallocTypes()