
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from tests.utils.cpython import MakeTypePtr, MakeNumSeqMapMethods
from tests.utils.memory import CreateTypes

from System import IntPtr

from Ironclad import PythonMapper
from Ironclad.Structs import Py_TPFLAGS, PySequenceMethods

class IterationTest(TestCase):
    
    @WithMapper
    def testPyObject_SelfIter(self, mapper, _):
        objPtr = mapper.Store(object())
        resultPtr = mapper.PyObject_SelfIter(objPtr)
        self.assertEqual(resultPtr, objPtr)
        self.assertEqual(mapper.RefCount(objPtr), 2)
    
    
    @WithMapper
    def testPyObject_GetIter_Success(self, mapper, _):
        testList = [1, 2, 3]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        iter = mapper.Retrieve(iterPtr)
        self.assertEqual(list(iter), testList, "bad iterator")


    @WithMapper
    def testPyObject_GetIter_NotIEnumerable(self, mapper, _):
        class iterclass(object):
            def __iter__(self):
                for i in range(10):
                    yield i
        
        obj = iterclass()
        objPtr = mapper.Store(obj)
        iterPtr = mapper.PyObject_GetIter(objPtr)
        _iter = mapper.Retrieve(iterPtr)
        self.assertEqual(list(_iter), list(range(10)))
        
        classPtr = mapper.Store(iterclass)
        self.assertEqual(mapper.PyObject_GetIter(classPtr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyObject_GetIter_Failure(self, mapper, _):
        testObj = object()
        objPtr = mapper.Store(testObj)
        iterPtr = mapper.PyObject_GetIter(objPtr)
        self.assertEqual(iterPtr, IntPtr.Zero, "returned iterator inappropriately")
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyIter_Next_Success(self, mapper, _):
        testList = [object(), object(), object()]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        
        for i in range(3):
            itemPtr = mapper.PyIter_Next(iterPtr)
            self.assertEqual(mapper.Retrieve(itemPtr), testList[i])
            self.assertEqual(mapper.RefCount(itemPtr), 2)
            mapper.DecRef(itemPtr)
        
        noItemPtr = mapper.PyIter_Next(iterPtr)
        self.assertEqual(noItemPtr, IntPtr.Zero)


    @WithMapper
    def testPyIter_Next_NotAnIterator(self, mapper, _):
        notIterPtr = mapper.Store(object())
        self.assertEqual(mapper.PyIter_Next(notIterPtr), IntPtr.Zero, "bad return")
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyIter_Next_ExplodingIterator(self, mapper, _):
        class BorkedException(Exception):
            pass
        def GetNext():
            raise BorkedException("Release the hounds!")
        explodingIterator = (GetNext() for _ in range(3))
        
        iterPtr = mapper.Store(explodingIterator)
        self.assertEqual(mapper.PyIter_Next(iterPtr), IntPtr.Zero, "bad return")
        self.assertNotEqual(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except BorkedException as e:
            self.assertEqual(str(e), "Release the hounds!", "unexpected message")
        else:
            self.fail("wrong exception")

suite = makesuite(
    IterationTest,
)
if __name__ == '__main__':
    run(suite)
