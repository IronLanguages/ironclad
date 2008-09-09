
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.cpython import MakeTypePtr, MakeNumSeqMapMethods
from tests.utils.memory import CreateTypes

from System import IntPtr

from Ironclad import Python25Mapper
from Ironclad.Structs import Py_TPFLAGS, PySequenceMethods

class IterationTest(TestCase):
    
    def testPyObject_GetIter_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [1, 2, 3]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        iter = mapper.Retrieve(iterPtr)
        self.assertEquals(list(iter), testList, "bad iterator")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyObject_GetIter_NotIEnumerable(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(TypeError, KindaConvertError)
        
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
        
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(TypeError, KindaConvertError)
                
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
        
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(TypeError, KindaConvertError)
            
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

class SequenceIterationTest(TestCase):
    
    def testPySeqIter_New(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
    
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
    
        notseqs = (3, -2.5e5, object, object())
        for notseq in notseqs:
            notseqPtr = mapper.Store(notseq)
            mapper.LastException = None
            self.assertEquals(mapper.PySeqIter_New(notseqPtr), IntPtr.Zero)
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
    
        mapper.Dispose()
        deallocTypes()


    def testIterableClassWith__iter__whichCallsPySeqIter_New(self):
        # original implementation used PythonOps.GetEnumerator;
        # the problem is that PythonOps.GetEnumerator will just call __iter__,
        # which will call PySeqIter_New, which will stack overflow in short order.
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        def tp_iter(instancePtr):
            return mapper.PySeqIter_New(instancePtr)
        def sq_item(instancePtr, i):
            if i < 3:
                return mapper.Store(i * 10)
            mapper.LastException = IndexError("no. not yours.")
            return IntPtr.Zero
        def sq_length(instancePtr):
            return mapper.Store(3)
        seqPtr, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {"sq_item": sq_item, "sq_length": sq_length})
        typeSpec = {
            "tp_name": "klass",
            "tp_flags": Py_TPFLAGS.HAVE_CLASS | Py_TPFLAGS.HAVE_ITER,
            "tp_iter": tp_iter,
            "tp_as_sequence": seqPtr,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        klass = mapper.Retrieve(typePtr)
        instance = klass()
        
        self.assertEquals([x for x in instance], [0, 10, 20])
    
        mapper.Dispose()
        deallocType()
        deallocSeq()
        deallocTypes()
        
        
        


suite = makesuite(
    IterationTest,
    SequenceIterationTest,
)
if __name__ == '__main__':
    run(suite, 2)