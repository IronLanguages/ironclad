
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes, OffsetPtr

from System import GC, IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPython_destructor_Delegate, PythonMapper, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject

    
    
class Python25Mapper_PyObject_Test(unittest.TestCase):
    
    def testPyObject_Call(self):
        mapper = Python25Mapper()
        
        kwargsPtr = IntPtr.Zero
        deallocTypes = CreateTypes(mapper)
        try:
            kallablePtr = mapper.Store(lambda x: x * 2)
            argsPtr = mapper.Store((4,))
            resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, kwargsPtr)
            try:
                self.assertEquals(mapper.Retrieve(resultPtr), 8, "didn't call")
            finally:
                mapper.DecRef(kallablePtr)
                mapper.DecRef(argsPtr)
                mapper.DecRef(resultPtr)
        finally:
            deallocTypes()


    def testPyCallable_Check(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        callables = map(mapper.Store, [float, len, lambda: None])
        notCallables = map(mapper.Store, ["hullo", 33, ])
        
        try:
            for x in callables:
                self.assertEquals(mapper.PyCallable_Check(x), 1, "reported not callable")
            for x in notCallables:
                self.assertEquals(mapper.PyCallable_Check(x), 0, "reported callable")
        finally:
            deallocTypes()


    def testPyObject_GetAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
        objPtr = mapper.Store(Thingum("Poe"))
        try:
            resultPtr = mapper.PyObject_GetAttrString(objPtr, "bob")
            try:
                self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")
            finally:
                mapper.DecRef(resultPtr)
        finally:
            mapper.DecRef(objPtr)
            deallocTypes()


    def testPyObject_GetAttrStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
        objPtr = mapper.Store(Thingum("Poe"))
        try:
            resultPtr = mapper.PyObject_GetAttrString(objPtr, "ben")
            self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
            self.assertEquals(mapper.LastException, None, "no need to set exception, according to spec")
        finally:
            mapper.DecRef(objPtr)
            deallocTypes()
    
    
    def testPyObject_GetIter_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [1, 2, 3]
        listPtr = mapper.Store(testList)
        try:
            iterPtr = mapper.PyObject_GetIter(listPtr)
            iter = mapper.Retrieve(iterPtr)
            self.assertEquals([x for x in iter], testList, "bad iterator")
            mapper.DecRef(iterPtr)
        finally:
            mapper.DecRef(listPtr)
            deallocTypes()
    
    
    def testPyObject_GetIter_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testObj = object()
        objPtr = mapper.Store(testObj)
        try:
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
        finally:
            mapper.DecRef(objPtr)
            deallocTypes()
    
    
    def testPyIter_Next_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [0, 1, 2]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        try:
            for i in range(3):
                itemPtr = mapper.PyIter_Next(iterPtr)
                self.assertEquals(mapper.Retrieve(itemPtr), i, "got wrong object back")
                self.assertEquals(mapper.RefCount(itemPtr), 2, "failed to incref")
                mapper.DecRef(itemPtr)
            
            noItemPtr = mapper.PyIter_Next(iterPtr)
            self.assertEquals(noItemPtr, IntPtr.Zero, "failed to stop iterating")
            
        finally:
            mapper.DecRef(iterPtr)
            mapper.DecRef(listPtr)
            deallocTypes()
    
    
    def testPyIter_Next_NotAnIterator(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        notIterPtr = mapper.Store(object())
        try:
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
            
        finally:
            mapper.DecRef(notIterPtr)
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
        try:
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
            
        finally:
            mapper.DecRef(iterPtr)
            deallocTypes()
    
    
class Python25Mapper_PyBaseObject_Type_Test(unittest.TestCase):

    def testPyBaseObject_Type(self):
        mapper = Python25Mapper()
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyBaseObject_Type", typeBlock)
            self.assertEquals(mapper.PyBaseObject_Type, typeBlock, "failed to remember address")
            self.assertEquals(mapper.Retrieve(mapper.PyBaseObject_Type), object, "failed to map correctly")
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def testPyBaseObject_TypeField_tp_dealloc(self):
        calls = []
        class MyPM(Python25Mapper):
            def PyBaseObject_Dealloc(self, objPtr):
                calls.append(objPtr)
        
        self.mapper = MyPM()
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            self.mapper.SetData("PyBaseObject_Type", typeBlock)
            GC.Collect() # this will make the function pointers invalid if we forgot to store references to the delegates

            deallocFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
            deallocFP = CPyMarshal.ReadPtr(deallocFPPtr)
            deallocDgt = Marshal.GetDelegateForFunctionPointer(deallocFP, CPython_destructor_Delegate)
            deallocDgt(IntPtr(12345))
            self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def testPyBaseObject_TypeField_tp_free(self):
        calls = []
        class MyPM(Python25Mapper):
            def PyObject_Free(self, objPtr):
                calls.append(objPtr)
        
        self.mapper = MyPM()
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            self.mapper.SetData("PyBaseObject_Type", typeBlock)
            GC.Collect() # this will make the function pointers invalid if we forgot to store references to the delegates

            freeDgt = CPyMarshal.ReadFunctionPtrField(typeBlock, PyTypeObject, "tp_free", CPython_destructor_Delegate)
            freeDgt(IntPtr(12345))
            self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        finally:
            Marshal.FreeHGlobal(typeBlock)
            
    
    def testPyBaseObject_TypeDeallocCallsObjTypesFreeFunction(self):
        calls = []
        def Some_FreeFunc(objPtr):
            calls.append(objPtr)
        self.freeDgt = PythonMapper.PyObject_Free_Delegate(Some_FreeFunc)
        
        mapper = Python25Mapper()
        
        baseObjTypeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        objTypeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        try:
            mapper.SetData("PyBaseObject_Type", baseObjTypeBlock)
            mapper.SetData("PyDict_Type", objTypeBlock) # type not actually important
            CPyMarshal.WriteFunctionPtrField(objTypeBlock, PyTypeObject, "tp_free", self.freeDgt)
            CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", objTypeBlock)
            
            GC.Collect() # this should make the function pointers invalid if we forgot to store references to the delegates

            mapper.PyBaseObject_Dealloc(objPtr)
            self.assertEquals(calls, [objPtr], "wrong calls")
        finally:
            Marshal.FreeHGlobal(baseObjTypeBlock)
            Marshal.FreeHGlobal(objTypeBlock)
            Marshal.FreeHGlobal(objPtr)


suite = makesuite(
    Python25Mapper_PyObject_Test,
    Python25Mapper_PyBaseObject_Type_Test,
)

if __name__ == '__main__':
    run(suite)