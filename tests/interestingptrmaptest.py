
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.gc import gcwait

from System import IntPtr, NullReferenceException, WeakReference

from Ironclad import InterestingPtrMap, UnmanagedDataMarker


class InterestingPtrMapTest(TestCase):
    
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
    
    
    def testWeakAssociateAssociates(self):
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
        map.Release(ptr)
    
    
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
        map.Weaken(objref.Target)
        gcwait()
        
        self.assertEquals(objref.IsAlive, False, "failed to GC")
        self.assertRaises(NullReferenceException, map.GetObj, ptr)
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
        
        
    def testGetStrongRefs(self):
        map, ptr1, obj1, obj1ref = self.getVars()
        _, ptr2, obj2, obj2ref = self.getVars()
        
        def GetStrongRefsSet():
            return set([x for x in map.GetStrongRefs()])
        
        map.WeakAssociate(ptr1, obj1)
        map.WeakAssociate(ptr2, obj2)
        
        self.assertEquals(GetStrongRefsSet(), set(), "should be no strong refs")
        map.Strengthen(obj1)
        self.assertEquals(GetStrongRefsSet(), set([obj1]), "should be one strong ref")
        map.Strengthen(obj2)
        self.assertEquals(GetStrongRefsSet(), set([obj1, obj2]), "should be two strong refs")
        map.Weaken(obj1)
        self.assertEquals(GetStrongRefsSet(), set([obj2]), "should be one strong ref")
        


suite = makesuite(InterestingPtrMapTest)
if __name__ == '__main__':
    run(suite)