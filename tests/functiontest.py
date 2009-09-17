
from types import FunctionType

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal
from Ironclad.Structs import PyFunctionObject, PyTypeObject

attrs = (
    'func_code', 'func_globals', 'func_defaults', 'func_closure', 'func_doc',
    'func_name', 'func_dict', 'func_weakreflist', 'func_module'
)

class FunctionTest(TestCase):

    @WithMapper
    def testStoreFunction(self, mapper, _):
        # note: can't be bothered to set any fields for now,
        # because they're not actually needed at the moment
        def f(): pass
        fPtr = mapper.Store(f)
        
        stored = Marshal.PtrToStructure(fPtr, PyFunctionObject)
        self.assertEquals(stored.ob_refcnt, 1)
        self.assertEquals(stored.ob_type, mapper.PyFunction_Type)
        
        for attr in attrs:
            self.assertEquals(getattr(stored, attr), IntPtr.Zero)
    
    @WithMapper
    def testStoreType(self, mapper, _):
        self.assertEquals(mapper.Retrieve(mapper.PyFunction_Type), FunctionType)
        self.assertEquals(CPyMarshal.ReadIntField(mapper.PyFunction_Type, PyTypeObject, 'tp_basicsize'), Marshal.SizeOf(PyFunctionObject))

suite = makesuite(FunctionTest)
if __name__ == '__main__':
    run(suite)