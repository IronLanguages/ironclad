
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.gc import gcwait

from System import NullReferenceException, WeakReference
from System.Runtime.InteropServices import Marshal


from Ironclad import BadMappingException, CPyMarshal, InterestingPtrMap, PtrFunc
from Ironclad.Structs import PyObject


# NOTE: certain tests wrap some of their execution in a do() function;
# either to ensure that things-which-should-be-GCed really do get GCed,
# rather than hanging around until out of scope, or to ensure that 
# inappropriate gc gets a chance to happen and cause a failure.

class InterestingPtrMapTest(TestCase):
    
    def setUp(self):
        TestCase.setUp(self)
        self.ptrs = []
    
    
    def tearDown(self):
        for ptr in self.ptrs:
            Marshal.FreeHGlobal(ptr)
        TestCase.tearDown(self)
    
    
    def getVars(self):
        obj = object()
        ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 1)
        self.ptrs.append(ptr)
        return InterestingPtrMap(), ptr, obj, WeakReference(obj)
        
        
    def testAssociateIsStrong(self):
        def do():
            # see NOTE
            map, ptr, obj, ref = self.getVars()
            map.Associate(ptr, obj)
            del obj
            return map, ptr, ref
        map, ptr, ref = do()
        gcwait()
        
        self.assertEquals(ref.IsAlive, True, "unexpected GC")
        self.assertEquals(map.HasObj(ref.Target), True, "wrong")
        self.assertEquals(map.GetObj(ptr), ref.Target, "not mapped")
        self.assertEquals(map.HasPtr(ptr), True, "wrong")
        self.assertEquals(map.GetPtr(ref.Target), ptr, "not mapped")
        
        
    def testAssociateCanWeaken(self):
        def do():
            # see NOTE
            map, ptr, obj, ref = self.getVars()
            map.Associate(ptr, obj)

            self.assertEquals(map.HasPtr(ptr), True)
            self.assertEquals(ref.IsAlive, True, "unexpected GC")

            del obj
            map.Release(ptr)
            return map, ptr, ref
        map, ptr, ref = do()
        gcwait()
    
        self.assertEquals(map.HasPtr(ptr), False)
        self.assertEquals(ref.IsAlive, False, "failed to GC")
        self.assertRaises(BadMappingException, map.GetObj, ptr)
        # can't really try to get the ptr, because we don't have the obj any more
    
    
    def testBridgeAssociateIsStrong(self):
        def do():
            # see NOTE
            map, ptr, obj, ref = self.getVars()
            map.BridgeAssociate(ptr, obj)
            del obj
            return map, ptr, ref
        map, ptr, ref = do()
        gcwait()
        
        self.assertEquals(ref.IsAlive, True, "unexpected GC")
        self.assertEquals(map.HasObj(ref.Target), True, "wrong")
        self.assertEquals(map.GetPtr(ref.Target), ptr, "not mapped")
        self.assertEquals(map.HasPtr(ptr), True, "wrong")
        self.assertEquals(map.GetObj(ptr), ref.Target, "not mapped")
        map.Release(ptr)
    
    
    def testBridgeAssociateCanWeaken(self):
        def do():
            # see NOTE
            map, ptr, obj, ref = self.getVars()
            map.BridgeAssociate(ptr, obj)
            map.UpdateStrength(ptr)
            del obj
            return map, ptr, ref
        map, ptr, ref = do()
        gcwait()
        
        self.assertEquals(ref.IsAlive, False, "failed to GC")
        self.assertRaises(NullReferenceException, map.GetObj, ptr)
        map.Release(ptr)
    
    
    def testUpdateStrengthStrengthensWeakRefWithRefcnt2(self):
        def do():
            # see NOTE
            map, ptr, obj, ref = self.getVars()
            self.keepalive = map
            map.BridgeAssociate(ptr, obj)
            map.UpdateStrength(ptr)

            # ref should now be weak, but obj is still referenced in this scope
            CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
            map.UpdateStrength(ptr)

            # should now be strong; safe to del obj
            del obj
            return ref
        ref = do()
        gcwait()
        
        self.assertEquals(ref.IsAlive, True, "unexpected GC")
    
    
    def testCheckBridgePtrsShouldUpdateAll(self):
        def do():
            # see NOTE
            map, ptr1, obj1, ref1 = self.getVars()
            _, ptr2, obj2, ref2 = self.getVars()
            map.BridgeAssociate(ptr1, obj1)
            map.BridgeAssociate(ptr2, obj2)

            # make both ptrs 'ready to weaken'
            CPyMarshal.WriteIntField(ptr1, PyObject, 'ob_refcnt', 1)
            CPyMarshal.WriteIntField(ptr2, PyObject, 'ob_refcnt', 1)

            map.CheckBridgePtrs(True)
            del obj1
            del obj2
            return map, ref1, ref2
        map, ref1, ref2 = do()
        gcwait()
        
        self.assertEquals(ref1.IsAlive, False, "failed to GC")
        self.assertEquals(ref2.IsAlive, False, "failed to GC")
    
    
    def testMapOverBridgePtrs(self):
        map, ptr1, obj1, _ = self.getVars()
        __, ptr2, obj2, ___ = self.getVars()
        map.BridgeAssociate(ptr1, obj1)
        map.BridgeAssociate(ptr2, obj2)
        
        ptrs = []
        def MapFunc(ptr):
            ptrs.append(ptr)
        map.MapOverBridgePtrs(PtrFunc(MapFunc))
        self.assertEquals(len(ptrs), 2)
        self.assertEquals(set(ptrs), set([ptr1, ptr2]))
        
        

suite = makesuite(InterestingPtrMapTest)
if __name__ == '__main__':
    run(suite)