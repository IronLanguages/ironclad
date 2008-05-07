
import unittest
from tests.utils.runtest import makesuite, run

from tests.utils.gc import gcwait

from System import IntPtr, NullReferenceException, WeakReference

from Ironclad import InterestingPtrMap, UnmanagedDataMarker


class InterestingPtrMapTest(unittest.TestCase):
    
    def getVars(self):
        obj = object()
        return InterestingPtrMap(), IntPtr(123), obj, WeakReference(obj)
        
    
    def testAssociateIsStrong(self):
        map, ptr, obj, objref = self.getVars()
        map.Associate(ptr, obj)
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "unexpected GC")
        self.assertEquals(map.HasObj(objref.Target), True, "wrong")
        self.assertEquals(map.GetObj(ptr), objref.Target, "not mapped")
        self.assertEquals(map.HasPtr(ptr), True, "wrong")
        self.assertEquals(map.GetPtr(objref.Target), ptr, "not mapped")
        
        # TODO: find out why map.HasPtr prevents obj from being GCed
        WorkaroundHasPtr = lambda p: map.HasPtr(p)
        map.Release(ptr)
        gcwait()
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertEquals(WorkaroundHasPtr(ptr), False, "wrong")
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
    
    
    def testWeakAssociateIsWeak(self):
        map, ptr, obj, objref = self.getVars()
        map.WeakAssociate(ptr, obj)
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(NullReferenceException, map.GetObj, ptr)
        self.assertEquals(map.HasPtr(ptr), True, "wrong")
        map.Release(ptr)
        
    
    def testWeakAssociateStrengthenWeaken(self):
        map, ptr, obj, objref = self.getVars()
        map.WeakAssociate(ptr, obj)
        
        map.Strengthen(obj)
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "unexpected GC")
        self.assertEquals(map.HasObj(objref.Target), True, "wrong")
        self.assertEquals(map.GetPtr(objref.Target), ptr, "not mapped")
        self.assertEquals(map.HasPtr(ptr), True, "wrong")
        self.assertEquals(map.GetObj(ptr), objref.Target, "not mapped")
        
        # TODO: find out why map.HasPtr prevents obj from being GCed
        WorkaroundHasPtr = lambda p: map.HasPtr(p)
        sameobj = objref.Target
        map.Weaken(sameobj)
        del sameobj
        gcwait()
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(NullReferenceException, map.GetObj, ptr)
        self.assertEquals(WorkaroundHasPtr(ptr), True, "wrong")
        
        map.Release(ptr)
    

    def testReleaseStrongRefWeakens(self):
        map, ptr, obj, objref = self.getVars()
        map.WeakAssociate(ptr, obj)
        map.Strengthen(obj)
        map.Release(ptr)
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(KeyError, map.GetObj, ptr)
        self.assertEquals(map.HasPtr(ptr), False, "wrong")
        


suite = makesuite(InterestingPtrMapTest)
if __name__ == '__main__':
    run(suite)