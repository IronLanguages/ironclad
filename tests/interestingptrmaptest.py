
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.gc import gcwait

from System import IntPtr, NullReferenceException, WeakReference
from System.Runtime.InteropServices import Marshal


from Ironclad import CPyMarshal, InterestingPtrMap, PtrFunc, UnmanagedDataMarker
from Ironclad.Structs import PyObject


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
        map, ptr, obj, objref = self.getVars()
        map.Associate(ptr, obj)
        del obj
        gcwait()
        
        def Crazy():
            # trying to run all these tests in the same scope as the release/gc seems to reliably cause
            # the gc not to happen (unless 3 or more of the assertions are commented out). Am upset by this.
            self.assertEquals(objref.IsAlive, True, "unexpected GC")
            self.assertEquals(map.HasObj(objref.Target), True, "wrong")
            self.assertEquals(map.GetObj(ptr), objref.Target, "not mapped")
            self.assertEquals(map.HasPtr(ptr), True, "wrong")
            self.assertEquals(map.GetPtr(objref.Target), ptr, "not mapped")
        Crazy()
        
        map.Release(ptr)
        gcwait()
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(KeyError, map.GetObj, ptr)
        # can't really try to get the ptr, because we don't have the obj any more
        

    def testAssociateUDMGivesOneWayMap(self):
        map = InterestingPtrMap()
        ptr1 = IntPtr(123)
        ptr2 = IntPtr(456)
        udm = UnmanagedDataMarker.PyListObject
        
        map.Associate(ptr1, udm)
        map.Associate(ptr2, udm)
        
        self.assertEquals(map.HasPtr(ptr1), True, "wrong")
        self.assertEquals(map.HasPtr(ptr2), True, "wrong")
        self.assertEquals(map.GetObj(ptr1), udm, "failed to retrieve udm 1")
        self.assertEquals(map.GetObj(ptr2), udm, "failed to retrieve udm 2")
        
        self.assertEquals(map.HasObj(udm), False, "should not claim to have UDMs")
        self.assertRaises(KeyError, map.GetPtr, udm)
        
        map.Release(ptr1)
        map.Release(ptr2)
    
    
    def testBridgeAssociateAssociatesStrongly(self):
        map, ptr, obj, objref = self.getVars()
        map.BridgeAssociate(ptr, obj)
        del obj
        gcwait()
        
        self.assertEquals(objref.IsAlive, True, "unexpected GC")
        self.assertEquals(map.HasObj(objref.Target), True, "wrong")
        self.assertEquals(map.GetPtr(objref.Target), ptr, "not mapped")
        self.assertEquals(map.HasPtr(ptr), True, "wrong")
        self.assertEquals(map.GetObj(ptr), objref.Target, "not mapped")
        map.Release(ptr)
    
    
    def testBridgeAssociateThenUpdate(self):
        map, ptr, obj, objref = self.getVars()
        map.BridgeAssociate(ptr, obj)
        del obj
        gcwait()
        
        self.assertEquals(objref.IsAlive, True, "unexpected GC")
        map.UpdateStrength(ptr)
        gcwait()
        
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(NullReferenceException, map.GetObj, ptr)
        map.Release(ptr)
    
    
    def testUpdateStrengthStrengthensWeakRefWithRefcnt2(self):
        map, ptr, obj, objref = self.getVars()
        self.keepalive = map
        map.BridgeAssociate(ptr, obj)
        map.UpdateStrength(ptr)
        
        # ref should now be weak, but obj is still referenced in this scope
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        map.UpdateStrength(ptr)
        
        # should now be strong; safe to del obj
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "unexpected GC")
    
    
    def testCheckBridgePtrsShouldUpdateAll(self):
        map, ptr1, obj1, obj1ref = self.getVars()
        _, ptr2, obj2, obj2ref = self.getVars()
        map.BridgeAssociate(ptr1, obj1)
        map.BridgeAssociate(ptr2, obj2)
        
        # make both ptrs 'ready to weaken'
        CPyMarshal.WriteIntField(ptr1, PyObject, 'ob_refcnt', 1)
        CPyMarshal.WriteIntField(ptr2, PyObject, 'ob_refcnt', 1)
        
        map.CheckBridgePtrs()
        del obj1
        del obj2
        gcwait()
        self.assertEquals(obj1ref.IsAlive, False, "failed to GC")
        self.assertEquals(obj2ref.IsAlive, False, "failed to GC")
    
    
    def testMapOverBridgePtrs(self):
        map, ptr1, obj1, obj1ref = self.getVars()
        _, ptr2, obj2, obj2ref = self.getVars()
        map.BridgeAssociate(ptr1, obj1)
        map.BridgeAssociate(ptr2, obj2)
        
        ptrs = []
        def MapFunc(ptr):
            ptrs.append(ptr)
        map.MapOverBridgePtrs(PtrFunc(MapFunc))
        self.assertEquals(len(ptrs), 2)
        self.assertEquals(set(ptrs), set([ptr1, ptr2]))
        

    def testReleaseStrongRefWeakens(self):
        map, ptr, obj, objref = self.getVars()
        map.BridgeAssociate(ptr, obj)
        map.Release(ptr)
        
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(KeyError, map.GetObj, ptr)
        self.assertEquals(map.HasPtr(ptr), False, "wrong")


suite = makesuite(InterestingPtrMapTest)
if __name__ == '__main__':
    run(suite)