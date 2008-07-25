
import sys

from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import Python25Mapper
        
        
class Python25Mapper_Sequence_Test(TestCase):
    
    def testPySequence_Size(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for seq in ("hullo", tuple(), [1, 2, 3], {'foo': 'bar'}, set([1, 2])):
            seqPtr = mapper.Store(seq)
            self.assertEquals(mapper.PySequence_Size(seqPtr), len(seq))
            mapper.DecRef(seqPtr)
        
        for notseq in (object, object(), 37):
            notseqPtr = mapper.Store(notseq)
            self.assertEquals(mapper.PySequence_Size(notseqPtr), -1)
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
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
                self.assertEquals(mapper.PySequence_GetItem(seqPtr, i), IntPtr.Zero)
                def KindaConvertError():
                    raise mapper.LastException
                self.assertRaises(IndexError, KindaConvertError)
            
            mapper.DecRef(seqPtr)
            
        mapper.Dispose()
        deallocTypes()
        



suite = makesuite(
    Python25Mapper_Sequence_Test,
)

if __name__ == '__main__':
    run(suite)