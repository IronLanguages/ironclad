
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from tests.utils.cpython import MakeTypePtr, MakeNumSeqMapMethods
from tests.utils.memory import CreateTypes

from System import IntPtr

from Ironclad import Python25Mapper
from Ironclad.Structs import Py_TPFLAGS, PySequenceMethods

class IterationTest(TestCase):
    
    @WithMapper
    def testPyObject_SelfIter(self, mapper, _):
        objPtr = mapper.Store(object())
        resultPtr = mapper.PyObject_SelfIter(objPtr)
        self.assertEquals(resultPtr, objPtr)
        self.assertEquals(mapper.RefCount(objPtr), 2)
    
    
    @WithMapper
    def testPyObject_GetIter_Success(self, mapper, _):
        testList = [1, 2, 3]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        iter = mapper.Retrieve(iterPtr)
        self.assertEquals(list(iter), testList, "bad iterator")


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
        self.assertEquals(list(_iter), range(10))
        
        classPtr = mapper.Store(iterclass)
        self.assertEquals(mapper.PyObject_GetIter(classPtr), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyObject_GetIter_Failure(self, mapper, _):
        testObj = object()
        objPtr = mapper.Store(testObj)
        iterPtr = mapper.PyObject_GetIter(objPtr)
        self.assertEquals(iterPtr, IntPtr.Zero, "returned iterator inappropriately")
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyIter_Next_Success(self, mapper, _):
        testList = [object(), object(), object()]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        
        for i in range(3):
            itemPtr = mapper.PyIter_Next(iterPtr)
            self.assertEquals(mapper.Retrieve(itemPtr), testList[i])
            self.assertEquals(mapper.RefCount(itemPtr), 2)
            mapper.DecRef(itemPtr)
        
        noItemPtr = mapper.PyIter_Next(iterPtr)
        self.assertEquals(noItemPtr, IntPtr.Zero)


    @WithMapper
    def testPyIter_Next_NotAnIterator(self, mapper, _):
        notIterPtr = mapper.Store(object())
        self.assertEquals(mapper.PyIter_Next(notIterPtr), IntPtr.Zero, "bad return")
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPyIter_Next_ExplodingIterator(self, mapper, _):
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


class SequenceIterationTest(TestCase):
    
    @WithMapper
    def testPySeqIter_New(self, mapper, _):
        class SomeSequence(object):
            def __getitem__(self, i):
                if i < 5: return i * 10
                raise IndexError()
            def __len__(self):
                return 5
    
        seqs = ([5, 4, 3], (2, 1, 0, -1), SomeSequence(), 'rawr!')
        for seq in seqs:
            seqPtr = mapper.Store(seq)
            iterPtr = mapper.PySeqIter_New(seqPtr)
            _iter = mapper.Retrieve(iterPtr)
            for item in seq:
                self.assertEquals(_iter.next(), item)
            mapper.DecRef(iterPtr)
            mapper.DecRef(seqPtr)
    
        notseqs = (3, -2.5e5, object, object(), list)
        for notseq in notseqs:
            notseqPtr = mapper.Store(notseq)
            mapper.LastException = None
            self.assertEquals(mapper.PySeqIter_New(notseqPtr), IntPtr.Zero)
            self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testIterableClassWith__iter__whichCallsPySeqIter_New(self, mapper, addToCleanUp):
        # original implementation used PythonOps.GetEnumerator;
        # the problem is that PythonOps.GetEnumerator will just call __iter__,
        # which will call PySeqIter_New, which will stack overflow in short order.
        def tp_iter(instancePtr):
            return mapper.PySeqIter_New(instancePtr)
        def sq_item(instancePtr, i):
            if i < 3:
                return mapper.Store(i * 10)
            mapper.LastException = IndexError("no. not yours.")
            return IntPtr.Zero
        def sq_length(instancePtr):
            return 3

        seqPtr, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {"sq_item": sq_item, "sq_length": sq_length})
        addToCleanUp(deallocSeq)

        typeSpec = {
            "tp_name": "klass",
            "tp_flags": Py_TPFLAGS.HAVE_CLASS | Py_TPFLAGS.HAVE_ITER,
            "tp_iter": tp_iter,
            "tp_as_sequence": seqPtr,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)

        klass = mapper.Retrieve(typePtr)
        instance = klass()
        self.assertEquals([x for x in instance], [0, 10, 20])


suite = makesuite(
    IterationTest,
    SequenceIterationTest,
)
if __name__ == '__main__':
    run(suite)
