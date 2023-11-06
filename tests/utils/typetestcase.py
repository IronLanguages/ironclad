
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from Ironclad import CPyMarshal, dgt_void_ptr, PythonMapper
from Ironclad.Structs import PyTypeObject


class TypeTestCase(TestCase):

    def assertTypeDeallocWorks(self, typename, CreateMapper, CreateInstance, TestConsequences):
        with CreateMapper() as mapper:
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
        deallocTypes()
    
    
    def assertUsual_tp_free(self, typename):
        with PythonMapper() as mapper:
            deallocTypes = CreateTypes(mapper)
            
            tp_freePtr = CPyMarshal.ReadPtrField(
                getattr(mapper, typename), PyTypeObject, "tp_free")
            self.assertEqual(tp_freePtr, mapper.GetFuncPtr("PyObject_Free"), "wrong tp_free for " + typename)
            
        deallocTypes()
    
    
    def assertUsual_tp_dealloc(self, typename):
        with PythonMapper() as mapper:
            deallocTypes = CreateTypes(mapper)
            
            tp_deallocPtr = CPyMarshal.ReadPtrField(
                getattr(mapper, typename), PyTypeObject, "tp_dealloc")
            self.assertEqual(tp_deallocPtr, mapper.GetFuncPtr("IC_PyBaseObject_Dealloc"), "wrong tp_dealloc for " + typename)
            
        deallocTypes()
