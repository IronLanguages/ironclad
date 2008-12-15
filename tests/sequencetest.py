
import sys

from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeNumSeqMapMethods, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import Python25Mapper, CPyMarshal
from Ironclad.Structs import PyListObject, PyNumberMethods, PySequenceMethods
        
        
class SequenceFunctionsTest(TestCase):
    
    @WithMapper
    def testPySequence_Check(self, mapper, _):
        class Sequence(object):
            def __len__(self): raise Exception("fooled you!")
            def __getitem__(self, _): raise Exception("fooled you!")
            def __add__(self, _): raise Exception("fooled you!")
            def __radd__(self, _): raise Exception("fooled you!")
            def __mul__(self, _): raise Exception("fooled you!")
            def __rmul__(self, _): raise Exception("fooled you!")
        
        sequences = map(mapper.Store, [(1, 2, 3), ['a'], Sequence(), "foo"])
        notSequences = map(mapper.Store, [tuple, list, object(), {'foo': 'bar'}])
        
        for x in sequences:
            self.assertEquals(mapper.PySequence_Check(x), 1, "reported %r not sequence" % (mapper.Retrieve(x),))
        for x in notSequences:
            self.assertEquals(mapper.PySequence_Check(x), 0, "reported %r sequence" % (mapper.Retrieve(x),))


    @WithMapper
    def testPySequence_Size(self, mapper, _):
        for seq in ("hullo", tuple(), [1, 2, 3], {'foo': 'bar'}, set([1, 2])):
            seqPtr = mapper.Store(seq)
            self.assertEquals(mapper.PySequence_Size(seqPtr), len(seq))
            mapper.DecRef(seqPtr)
        
        for notseq in (object, object(), 37):
            notseqPtr = mapper.Store(notseq)
            mapper.LastException = None
            self.assertEquals(mapper.PySequence_Size(notseqPtr), -1)
            self.assertMapperHasError(mapper, TypeError)
            mapper.DecRef(notseqPtr)


    @WithMapper
    def testPySequence_GetItem(self, mapper, _):
        for seq in ([1, 2, 3], ('a', 'b', 'c'), 'bar'):
            seqPtr = mapper.Store(seq)
            for i in range(-3, 3):
                result = mapper.PySequence_GetItem(seqPtr, i)
                self.assertEquals(mapper.Retrieve(result), seq[i])

            for i in (-5, 66):
                mapper.LastException = None
                self.assertEquals(mapper.PySequence_GetItem(seqPtr, i), IntPtr.Zero)
                self.assertMapperHasError(mapper, IndexError)
            
            mapper.DecRef(seqPtr)
        
        for notseq in (object, object(), 37):
            notseqPtr = mapper.Store(notseq)
            self.assertEquals(mapper.PySequence_GetItem(notseqPtr, 0), IntPtr.Zero)
            self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPySequence_SetItem_List(self, mapper, _):
        seq = [1, 2, 3]
        seqPtr = mapper.Store(seq)
        seqData = CPyMarshal.ReadPtrField(seqPtr, PyListObject, "ob_item")
        for i in range(-3, 3):
            itemPtr = mapper.Store(i)
            self.assertEquals(mapper.PySequence_SetItem(seqPtr, i, itemPtr), 0)
            self.assertEquals(mapper.RefCount(itemPtr), 2)
            index = i
            if index < 0:
                index += 3
            valData = CPyMarshal.Offset(seqData, index * CPyMarshal.PtrSize)
            self.assertEquals(CPyMarshal.ReadPtr(valData), itemPtr)
            self.assertEquals(seq[i], i)

        for i in (-5, 66):
            mapper.LastException = None
            self.assertEquals(mapper.PySequence_SetItem(seqPtr, i, mapper.Store(i)), -1)
            self.assertMapperHasError(mapper, IndexError)
        
    @WithMapper
    def testPySequence_SetItem_Other(self, mapper, _):
        calls = []
        class Seq(object):
            def __setitem__(self, index, value):
                calls.append((index, value))
        seq = Seq()
        seqPtr = mapper.Store(seq)
        for (i, item) in ((3, 'abc'), (-123, 999)):
            itemPtr = mapper.Store(item)
            self.assertEquals(mapper.PySequence_SetItem(seqPtr, i, itemPtr), 0)
            self.assertEquals(mapper.RefCount(itemPtr), 1)
            self.assertEquals(calls[-1], (i, item))
        
    @WithMapper
    def testPySequence_SetItem_Failure(self, mapper, _):
        for bad in (object, object(), 37, 'foo', (1, 2, 3)):
            badPtr = mapper.Store(bad)
            self.assertEquals(mapper.PySequence_SetItem(badPtr, 0, mapper.Store(123)), -1)
            self.assertMapperHasError(mapper, TypeError)
        
    @WithMapper
    def testPySequence_GetSlice(self, mapper, _):
        for seq in ([1, 2, 3], ('a', 'b', 'c'), 'bar'):
            seqPtr = mapper.Store(seq)
            for i, j in ((0, 2), (1, 4), (22, 347)):
                resultPtr = mapper.PySequence_GetSlice(seqPtr, i, j)
                self.assertEquals(mapper.Retrieve(resultPtr), seq[i:j])
            mapper.DecRef(seqPtr)
        
        for notseq in (object, object(), 37):
            notseqPtr = mapper.Store(notseq)
            self.assertEquals(mapper.PySequence_GetSlice(notseqPtr, 0, 1), IntPtr.Zero)
            self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPySequence_Repeat_Easy(self, mapper, _):
        for seq in ([1, 2, 3], ('a', 'b', 'c'), 'bar'):
            seqPtr = mapper.Store(seq)
            for i in range(3):
                resultPtr = mapper.PySequence_Repeat(seqPtr, i)
                self.assertEquals(mapper.Retrieve(resultPtr), seq * i)


    @WithMapper
    def testPySequence_Repeat_TypeWithSequenceRepeat(self, mapper, addToCleanUp):
        RESULT_PTR = IntPtr(123)
        calls = []
        def RepeatFunc(selfPtr, count):
            calls.append((selfPtr, count))
            return RESULT_PTR
        
        def Multiply(selfPtr, otherPtr):
            raise Exception("don't multiply if we can repeat!")
        
        seqPtr, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_repeat': RepeatFunc})
        addToCleanUp(deallocSeq)

        numPtr, deallocNum = MakeNumSeqMapMethods(PyNumberMethods, {'nb_multiply': Multiply})
        addToCleanUp(deallocNum)

        typeSpec = {
            "tp_as_sequence": seqPtr,
            "tp_as_number": numPtr,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)

        instance = mapper.Retrieve(typePtr)()
        instancePtr = mapper.Store(instance)
        
        self.assertEquals(mapper.PySequence_Repeat(instancePtr, 3), RESULT_PTR)
        self.assertEquals(calls, [(instancePtr, 3)])


    @WithMapper
    def testPySequence_Repeat_NumberNotSequence(self, mapper, _):
        class Number(object):
            def __mul__(self, other):
                raise Exception("this is a number, not a sequence")

        numPtr = mapper.Store(Number())
        self.assertEquals(mapper.PySequence_Repeat(numPtr, 123), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


    @WithMapper
    def testPySequence_Tuple_withTuple(self, mapper, _):
        tuplePtr = mapper.Store((1, 2, 3))
        self.assertEquals(mapper.PySequence_Tuple(tuplePtr), tuplePtr)
        self.assertEquals(mapper.RefCount(tuplePtr), 2)
        
    
    @WithMapper
    def testPySequence_Tuple_notTuple(self, mapper, _):
        listPtr = mapper.Store([4, 5, 6])
        tuplePtr = mapper.PySequence_Tuple(listPtr)
        self.assertEquals(mapper.Retrieve(tuplePtr), (4, 5, 6))
    
    
    @WithMapper
    def testPySequence_Tuple_notSequence(self, mapper, _):
        self.assertEquals(mapper.PySequence_Tuple(mapper.Store(123)), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)


suite = makesuite(
    SequenceFunctionsTest,
)

if __name__ == '__main__':
    run(suite)
