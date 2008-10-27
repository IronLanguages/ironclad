
import sys

from tests.utils.runtest import makesuite, run

from tests.utils.cpython import MakeNumSeqMapMethods, MakeTypePtr
from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import Python25Mapper
from Ironclad.Structs import PyNumberMethods, PySequenceMethods
        
        
class SequenceFunctionsTest(TestCase):
    
    def testPySequence_Check(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
                
        mapper.Dispose()
        deallocTypes()
        
        
    def testPySequence_Size(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
        
        mapper.Dispose()
        deallocTypes()


    def testPySequence_GetItem(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
            
        mapper.Dispose()
        deallocTypes()
        

    def testPySequence_Repeat_Easy(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for seq in ([1, 2, 3], ('a', 'b', 'c'), 'bar'):
            seqPtr = mapper.Store(seq)
            for i in range(3):
                resultPtr = mapper.PySequence_Repeat(seqPtr, i)
                self.assertEquals(mapper.Retrieve(resultPtr), seq * i)
        
        mapper.Dispose()
        deallocTypes()
        

    def testPySequence_Repeat_TypeWithSequenceRepeat(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        RESULT_PTR = IntPtr(123)
        calls = []
        def RepeatFunc(selfPtr, count):
            calls.append((selfPtr, count))
            return RESULT_PTR
        
        def Multiply(selfPtr, otherPtr):
            raise Exception("don't multiply if we can repeat!")
        
        seqPtr, deallocSeq = MakeNumSeqMapMethods(PySequenceMethods, {'sq_repeat': RepeatFunc})
        numPtr, deallocNum = MakeNumSeqMapMethods(PyNumberMethods, {'nb_multiply': Multiply})
        typeSpec = {
            "tp_as_sequence": seqPtr,
            "tp_as_number": numPtr,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        instance = mapper.Retrieve(typePtr)()
        instancePtr = mapper.Store(instance)
        
        self.assertEquals(mapper.PySequence_Repeat(instancePtr, 3), RESULT_PTR)
        self.assertEquals(calls, [(instancePtr, 3)])
        
        mapper.Dispose()
        deallocTypes()
        deallocType()
        deallocSeq()
        deallocNum()


    def testPySequence_Repeat_NumberNotSequence(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Number(object):
            def __mul__(self, other):
                raise Exception("this is a number, not a sequence")

        numPtr = mapper.Store(Number())
        self.assertEquals(mapper.PySequence_Repeat(numPtr, 123), IntPtr.Zero)
        self.assertMapperHasError(mapper, TypeError)
        
        mapper.Dispose()
        deallocTypes()



suite = makesuite(
    SequenceFunctionsTest,
)

if __name__ == '__main__':
    run(suite)