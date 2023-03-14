
from types import MethodType

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.memory import PtrToStructure

from System import IntPtr, Type
from System.Runtime.InteropServices import Marshal

from Ironclad.Structs import PyMethodObject


class MethodTest(TestCase):

    @WithMapper
    def testPyMethod_New(self, mapper, _):
        # if Python doesn't care what you put in a bound method, nor do I
        methPtr = mapper.PyMethod_New(IntPtr.Zero, mapper.Store(0), IntPtr.Zero)
        self.assertEqual(mapper.Retrieve(methPtr), MethodType(None, 0))
        self.assertMapperHasError(mapper, None)

        methPtr = mapper.PyMethod_New(mapper.Store(1), mapper.Store(2), mapper.Store(3))
        self.assertEqual(mapper.Retrieve(methPtr), MethodType(1, 2))
        self.assertMapperHasError(mapper, None)


    @WithMapper
    def testStoreMethod(self, mapper, _):
        meth = MethodType('foo', 'bar')
        methPtr = mapper.Store(meth)
        
        stored = PtrToStructure(methPtr, PyMethodObject)
        self.assertEqual(stored.ob_refcnt, 1)
        self.assertEqual(stored.ob_type, mapper.PyMethod_Type)
        self.assertEqual(stored.im_weakreflist, IntPtr.Zero)
        
        attrs = {
            'im_func': 'foo',
            'im_self': 'bar',
        }
        attrPtrs = []
        for (attr, expected) in attrs.items():
            attrPtr = getattr(stored, attr)
            self.assertEqual(mapper.RefCount(attrPtr), 1)
            mapper.IncRef(attrPtr)
            attrPtrs.append(attrPtr)
            value = mapper.Retrieve(attrPtr)
            self.assertEqual(value, expected)
        
        mapper.DecRef(methPtr)
        for attrPtr in attrPtrs:
            self.assertEqual(mapper.RefCount(attrPtr), 1)
            
        



suite = makesuite(MethodTest)
if __name__ == '__main__':
    run(suite)
