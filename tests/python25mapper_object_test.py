
from tests.utils.runtest import makesuite, run

from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPython_destructor_Delegate, Python25Api, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject

    
    
class Python25Mapper_PyObject_Test(TestCase):
    
    def testPyObject_Call(self):
        mapper = Python25Mapper()
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        
        kallablePtr = mapper.Store(lambda x: x * 2)
        argsPtr = mapper.Store((4,))
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, kwargsPtr)
        self.assertEquals(mapper.Retrieve(resultPtr), 8, "didn't call")
            
        mapper.Dispose()
        deallocTypes()


    def testPyCallable_Check(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        callables = map(mapper.Store, [float, len, lambda: None])
        notCallables = map(mapper.Store, ["hullo", 33, ])
        
        for x in callables:
            self.assertEquals(mapper.PyCallable_Check(x), 1, "reported not callable")
        for x in notCallables:
            self.assertEquals(mapper.PyCallable_Check(x), 0, "reported callable")
                
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "bob")
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "ben")
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, according to spec")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyObject_GetIter_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [1, 2, 3]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        iter = mapper.Retrieve(iterPtr)
        self.assertEquals([x for x in iter], testList, "bad iterator")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyObject_GetIter_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testObj = object()
        objPtr = mapper.Store(testObj)
        iterPtr = mapper.PyObject_GetIter(objPtr)
        self.assertEquals(iterPtr, IntPtr.Zero, "returned iterator inappropriately")
        self.assertNotEquals(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except TypeError, e:
            self.assertEquals(str(e), "PyObject_GetIter: object is not iterable", "bad message")
        else:
            self.fail("wrong exception")
                
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyIter_Next_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [0, 1, 2]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        
        for i in range(3):
            itemPtr = mapper.PyIter_Next(iterPtr)
            self.assertEquals(mapper.Retrieve(itemPtr), i, "got wrong object back")
            self.assertEquals(mapper.RefCount(itemPtr), 2, "failed to incref")
            mapper.DecRef(itemPtr)
        
        noItemPtr = mapper.PyIter_Next(iterPtr)
        self.assertEquals(noItemPtr, IntPtr.Zero, "failed to stop iterating")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyIter_Next_NotAnIterator(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        notIterPtr = mapper.Store(object())
        self.assertEquals(mapper.PyIter_Next(notIterPtr), IntPtr.Zero, "bad return")
        self.assertNotEquals(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except TypeError, e:
            self.assertEquals(str(e), "PyIter_Next: object is not an iterator", "bad message")
        else:
            self.fail("wrong exception")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyIter_Next_ExplodingIterator(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class BorkedException(Exception):
            pass
        def GetNext():
            raise BorkedException("Release the hounds!")
        explodingIterator = (GetNext() for _ in range(3))
        
        iterPtr = mapper.Store(explodingIterator)
        self.assertEquals(mapper.PyIter_Next(iterPtr), IntPtr.Zero, "bad return")
        self.assertNotEquals(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except BorkedException, e:
            self.assertEquals(str(e), "Release the hounds!", "unexpected message")
        else:
            self.fail("wrong exception")
            
        mapper.Dispose()
        deallocTypes()
    
    
class Python25Mapper_PyBaseObject_Type_Test(TypeTestCase):

    def testPyBaseObject_Type_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyBaseObject_Type")


    def testPyBaseObject_Type_tp_free(self):
        self.assertUsual_tp_free("PyBaseObject_Type")
            
    
    def testPyBaseObject_TypeDeallocCallsObjTypesFreeFunction(self):
        calls = []
        def Some_FreeFunc(objPtr):
            calls.append(objPtr)
        self.freeDgt = Python25Api.PyObject_Free_Delegate(Some_FreeFunc)
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        baseObjTypeBlock = mapper.PyBaseObject_Type
        objTypeBlock = mapper.PyDict_Type # type not actually important
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        
        CPyMarshal.WriteFunctionPtrField(objTypeBlock, PyTypeObject, "tp_free", self.freeDgt)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", objTypeBlock)
        gcwait() # this should make the function pointers invalid if we forgot to store references to the delegates

        mapper.PyBaseObject_Dealloc(objPtr)
        self.assertEquals(calls, [objPtr], "wrong calls")
            
        mapper.Dispose()
        deallocTypes()
        Marshal.FreeHGlobal(objPtr)


suite = makesuite(
    Python25Mapper_PyObject_Test,
    Python25Mapper_PyBaseObject_Type_Test,
)

if __name__ == '__main__':
    run(suite)