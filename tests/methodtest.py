
from types import MethodType

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr, Type
from System.Runtime.InteropServices import Marshal

from Ironclad.Structs import PyMethodObject

# make sure this particular overload PtrToStructure(IntPtr, Type) is called
PtrToStructure = Marshal.PtrToStructure.Overloads[IntPtr, Type]

class MethodTest(TestCase):

    @WithMapper
    def testPyMethod_New(self, mapper, _):
        # if Python doesn't care what you put in a bound method, nor do I
        methPtr = mapper.PyMethod_New(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(methPtr), MethodType(None, None, None))
        self.assertMapperHasError(mapper, None)

        methPtr = mapper.PyMethod_New(mapper.Store(1), mapper.Store(2), mapper.Store(3))
        self.assertEquals(mapper.Retrieve(methPtr), MethodType(1, 2, 3))
        self.assertMapperHasError(mapper, None)


    @WithMapper
    def testStoreMethod(self, mapper, _):
        meth = MethodType('foo', 'bar', 'baz')
        methPtr = mapper.Store(meth)
        
        stored = PtrToStructure(methPtr, PyMethodObject)
        self.assertEquals(stored.ob_refcnt, 1)
        self.assertEquals(stored.ob_type, mapper.PyMethod_Type)
        self.assertEquals(stored.im_weakreflist, IntPtr.Zero)
        
        attrs = {
            'im_func': 'foo',
            'im_self': 'bar',
            'im_class': 'baz',
        }
        attrPtrs = []
        for (attr, expected) in attrs.items():
            attrPtr = getattr(stored, attr)
            self.assertEquals(mapper.RefCount(attrPtr), 1)
            mapper.IncRef(attrPtr)
            attrPtrs.append(attrPtr)
            value = mapper.Retrieve(attrPtr)
            self.assertEquals(value, expected)
        
        mapper.DecRef(methPtr)
        for attrPtr in attrPtrs:
            self.assertEquals(mapper.RefCount(attrPtr), 1)
            
        



suite = makesuite(MethodTest)
if __name__ == '__main__':
    run(suite)