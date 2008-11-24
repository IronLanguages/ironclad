
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr, NullReferenceException
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject
    
# many constants, and EvilHackDict
from tests.utils.dispatcherhelpers import *

def FuncReturning(resultPtr, calls, identifier):
    def RecordCall(*args):
        calls.append((identifier, args))
        return resultPtr
    return RecordCall

def FuncRaising(exc, calls, identifier):
    def RecordCall(*args):
        calls.append((identifier, args))
        raise exc()
    return RecordCall


class DispatcherTest(TestCase):
    
    @WithMapper
    def testMapperCreatesModuleContainingDispatcher(self, mapper, _):
        Dispatcher = mapper.DispatcherModule.Dispatcher
        self.assertNotEquals(Dispatcher, None, "failed to locate Dispatcher")
        
    def testDisposeMapperPreventsDispatcherDelete(self):
        mapper = Python25Mapper()
        Dispatcher = mapper.DispatcherModule.Dispatcher
        dontDelete = Dispatcher.dontDelete
        mapper.Dispose()
        self.assertEquals(Dispatcher.delete, dontDelete)
    
    def assertDispatcherUtilityMethod(
            self, methodname, args, expectedCalls, 
            exceptionSet=None, expectedExceptionClass=None, 
            result=None, dispatcherMembers=None):
        realMapper = Python25Mapper()
        Dispatcher = realMapper.DispatcherModule.Dispatcher
        realMapper.DispatcherModule.Null = NULL
        
        outer = self
        class MockMapper(object):
            def __init__(self):
                self.LastException = exceptionSet
                outer.calls = []
            def Store(_, obj):
                outer.calls.append(('Store', obj))
                return OBJ_PTR
            def FreeTemps(_):
                outer.calls.append('FreeTemps')
            def DecRef(_, ptr):
                outer.calls.append(('DecRef', ptr))
            def Retrieve(_, ptr):
                outer.calls.append(('Retrieve', ptr))
                return result
        
        mockMapper = MockMapper()
        dispatcher = Dispatcher(mockMapper, {})
        if dispatcherMembers:
            for name, value in dispatcherMembers.items():
                setattr(dispatcher, name, value)
        method = getattr(dispatcher, methodname)
        if expectedExceptionClass:
            self.assertRaises(expectedExceptionClass, method, *args)
        else:
            self.assertEquals(method(*args), result)
        self.assertEquals(self.calls, expectedCalls, 'unexpected behaviour')
        self.assertEquals(mockMapper.LastException, None, 'unexpected exception set after call')
        realMapper.Dispose()
        
    def testStore(self):
        self.assertDispatcherUtilityMethod(
            "_store", (OBJ,), [('Store', OBJ)], result=OBJ_PTR)
        test_null = object()
        self.assertDispatcherUtilityMethod(
            "_store", (NULL,), [], result=NULL_PTR)
    
    def testCleanup(self):
        error = ValueError('huh?')
        self.assertDispatcherUtilityMethod(
            '_cleanup', (), ['FreeTemps'])
        self.assertDispatcherUtilityMethod(
            '_cleanup', (OBJ_PTR, NULL_PTR, OBJ_PTR), 
            ['FreeTemps', ('DecRef', OBJ_PTR), ('DecRef', OBJ_PTR)])
    
    def testCheckError(self):
        self.assertDispatcherUtilityMethod(
            '_check_error', (), [])
        self.assertDispatcherUtilityMethod(
            '_check_error', (), [], ValueError('huh?'), ValueError)
    
    def testRaise(self):
        error1 = ValueError('huh?')
        error2 = TypeError('meh')
        self.assertDispatcherUtilityMethod(
            "_raise", (error1,), [], None, ValueError)
        self.assertDispatcherUtilityMethod(
            "_raise", (error1,), [], error2, TypeError)
    
    def testReturn(self):
        def _check_error():
            self.calls.append('_check_error')
        members = {'_check_error': _check_error}
        
        self.assertDispatcherUtilityMethod(
            "_return", (), ['_check_error'], dispatcherMembers=members)
        self.assertDispatcherUtilityMethod(
            "_return", (OBJ,), ['_check_error'], result=OBJ, dispatcherMembers=members)
    
    def testReturnRetrieve(self):
        def _check_error_safe():
            self.calls.append('_check_error')
        def _check_error_bad():
            self.calls.append('_check_error')
            raise ValueError('not yours')
        members_safe = {'_check_error': _check_error_safe}
        members_bad = {'_check_error': _check_error_bad}
        
        self.assertDispatcherUtilityMethod(
            "_return_retrieve", (OBJ_PTR,), ['_check_error', ('Retrieve', OBJ_PTR)], dispatcherMembers=members_safe)
        self.assertDispatcherUtilityMethod(
            "_return_retrieve", (OBJ_PTR,), ['_check_error', ('Retrieve', OBJ_PTR)], result=OBJ, dispatcherMembers=members_safe)
        self.assertDispatcherUtilityMethod(
            "_return_retrieve", (NULL_PTR,), ['_check_error'], expectedExceptionClass=NullReferenceException, dispatcherMembers=members_safe)
        self.assertDispatcherUtilityMethod(
            "_return_retrieve", (OBJ_PTR,), ['_check_error'], expectedExceptionClass=ValueError, dispatcherMembers=members_bad)


class TrivialDispatchTest(TestCase):
    
    @WithMapper
    def assertDispatcherMethodDelegates(self, methodname, args, kwargs, implname, expectedArgs, mapper, addToCleanUp):
        mapper.DispatcherModule.Null = NULL
        dispatcher = mapper.DispatcherModule.Dispatcher(mapper, [])
        calls = []
        setattr(dispatcher, implname, FuncReturning(OBJ, calls, implname))
        self.assertEquals(getattr(dispatcher, methodname)(*args, **kwargs), OBJ)
        self.assertEquals(calls, [(implname, expectedArgs)])
    
    def testEasyDelegations(self):
        self.assertDispatcherMethodDelegates(
            'function_noargs', (NAME,), {}, '_call_O_OO', (NAME, NULL, NULL))
        self.assertDispatcherMethodDelegates(
            'method_noargs', (NAME, OBJ), {}, '_call_O_OO', (NAME, OBJ, NULL))
        self.assertDispatcherMethodDelegates(
            'function_objarg', (NAME, ARG), {}, '_call_O_OO', (NAME, NULL, ARG))
        self.assertDispatcherMethodDelegates(
            'method_objarg', (NAME, OBJ, ARG), {}, '_call_O_OO', (NAME, OBJ, ARG))
        self.assertDispatcherMethodDelegates(
            'function_varargs', (NAME,) + ARGS, {}, '_call_O_OO', (NAME, NULL, ARGS))
        self.assertDispatcherMethodDelegates(
            'method_varargs', (NAME, ARG,) + ARGS, {}, '_call_O_OO', (NAME, ARG, ARGS))
            
        self.assertDispatcherMethodDelegates(
            'method_ternary', (NAME, OBJ, ARG, ARG2), {}, '_call_O_OOO', (NAME, OBJ, ARG, ARG2))
        self.assertDispatcherMethodDelegates( # this one is for __rpow__
            'method_ternary_swapped', (NAME, OBJ, ARG), {}, '_call_O_OOO', (NAME, ARG, OBJ, NULL))
        
        self.assertDispatcherMethodDelegates(
            'function_kwargs', (NAME,) + ARGS, {}, '_call_O_OOO', (NAME, NULL, ARGS, NULL))
        self.assertDispatcherMethodDelegates(
            'function_kwargs', (NAME,) + ARGS, KWARGS, '_call_O_OOO', (NAME, NULL, ARGS, KWARGS))
        self.assertDispatcherMethodDelegates(
            'method_kwargs', (NAME, OBJ,) + ARGS, {}, '_call_O_OOO', (NAME, OBJ, ARGS, NULL))
        self.assertDispatcherMethodDelegates(
            'method_kwargs', (NAME, OBJ,) + ARGS, KWARGS, '_call_O_OOO', (NAME, OBJ, ARGS, KWARGS))
    

class DispatchTestCase(TestCase):
    
    def getPatchedDispatcher(self, mapper, calls, dgtResult, _returnFails=False, mockMapper=None):
        mapper.DispatcherModule.Null = NULL
        dispatcher = mapper.DispatcherModule.Dispatcher(mockMapper or mapper, {NAME: FuncReturning(dgtResult, calls, NAME)})
        
        def getmapmethod(name):
            def mapmethod(item):
                calls.append((name, (item,)))
                return PTRMAP[item]
            return mapmethod
        
        dispatcher._store = getmapmethod('_store')
        dispatcher._cleanup = FuncReturning(None, calls, '_cleanup')
        dispatcher._check_error = FuncReturning(None, calls, '_check_error')
        if _returnFails:
            dispatcher._return = FuncRaising(ValueError, calls, '_return')
            dispatcher._return_retrieve = FuncRaising(ValueError, calls, '_return_retrieve')
        else:
            dispatcher._return = FuncReturning(dgtResult, calls, '_return')
            dispatcher._return_retrieve = getmapmethod('_return_retrieve')
        
        return dispatcher
    
    @WithMapper
    def assertDispatcherMethod(self, methodname, args, expectedCalls, mapper, _):
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, RESULT_PTR)
        method = getattr(dispatcher, methodname)
        self.assertEquals(method(*args), RESULT)
        self.assertEquals(calls, expectedCalls)
        
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, RESULT_PTR, _returnFails=True)
        method = getattr(dispatcher, methodname)
        self.assertRaises(ValueError, method, *args)
        self.assertEquals(calls, expectedCalls)


    @WithMapper
    def assertDispatcherMethodWithResult(self, methodname, result, args, expectedCalls, mapper, _):
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, result)
        method = getattr(dispatcher, methodname)
        self.assertEquals(method(*args), result)
        self.assertEquals(calls, expectedCalls)
        
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, result, _returnFails=True)
        method = getattr(dispatcher, methodname)
        self.assertRaises(ValueError, method, *args)
        self.assertEquals(calls, expectedCalls)


class SimpleDispatchTest(DispatchTestCase):

    def testDispatch__call_O_OO(self):
        self.assertDispatcherMethod(
            '_call_O_OO',  (NAME, ARG, ARG2),
            [('_store', (ARG,)),
             ('_store', (ARG2,)),
             (NAME, (ARG_PTR, ARG2_PTR)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (ARG_PTR, ARG2_PTR, RESULT_PTR,))
            ])
    
    def testDispatch__call_O_OOO(self):
        self.assertDispatcherMethod(
            '_call_O_OOO', (NAME, ARG, ARG2, ARG3),
            [('_store', (ARG,)),
             ('_store', (ARG2,)),
             ('_store', (ARG3,)),
             (NAME, (ARG_PTR, ARG2_PTR, ARG3_PTR)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (ARG_PTR, ARG2_PTR, ARG3_PTR, RESULT_PTR,))
            ])
    
    def testDispatch_method_ssizearg(self):
        self.assertDispatcherMethod(
            'method_ssizearg', (NAME, OBJ, SSIZE),
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR, SSIZE)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, RESULT_PTR,))
            ])
    
    def testDispatch_method_ssizessizearg(self):
        self.assertDispatcherMethod(
            'method_ssizessizearg', (NAME, OBJ, SSIZE, SSIZE2),
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR, SSIZE, SSIZE2)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, RESULT_PTR,))
            ])
    
    def testDispatch_method_richcmp(self):
        self.assertDispatcherMethod(
            'method_richcmp', (NAME, OBJ, ARG, SSIZE),
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             (NAME, (OBJ_PTR, ARG_PTR, SSIZE)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, ARG_PTR, RESULT_PTR))
            ])
    
    def testDispatch_method_hashfunc(self):
        self.assertDispatcherMethodWithResult(
            'method_hashfunc', RESULT_INT, (NAME, OBJ),
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR,)), 
             ('_return', (RESULT_INT,)),
             ('_cleanup', (OBJ_PTR,))
            ])
    
    def testDispatch_method_cmpfunc(self):
        self.assertDispatcherMethodWithResult(
            'method_cmpfunc', RESULT_INT, (NAME, OBJ, ARG),
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             (NAME, (OBJ_PTR, ARG_PTR)), 
             ('_return', (RESULT_INT,)),
             ('_cleanup', (OBJ_PTR, ARG_PTR))
            ])
    
    def testDispatch_method_ssizeobjarg(self):
        self.assertDispatcherMethodWithResult(
            'method_ssizeobjarg', RESULT_INT, (NAME, OBJ, SSIZE, ARG),
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             (NAME, (OBJ_PTR, SSIZE, ARG_PTR)), 
             ('_return', (RESULT_INT,)),
             ('_cleanup', (OBJ_PTR, ARG_PTR,))
            ])
    
    def testDispatch_method_ssizessizeobjarg(self):
        self.assertDispatcherMethodWithResult(
            'method_ssizessizeobjarg', RESULT_INT, (NAME, OBJ, SSIZE, SSIZE2, ARG), 
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             (NAME, (OBJ_PTR, SSIZE, SSIZE2, ARG_PTR)), 
             ('_return', (RESULT_INT,)),
             ('_cleanup', (OBJ_PTR, ARG_PTR,))
            ])
    
    def testDispatch_method_objobjarg(self):
        self.assertDispatcherMethodWithResult(
            'method_objobjarg', RESULT_INT, (NAME, OBJ, ARG, ARG2), 
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             ('_store', (ARG2,)),
             (NAME, (OBJ_PTR, ARG_PTR, ARG2_PTR)), 
             ('_return', (RESULT_INT,)),
             ('_cleanup', (OBJ_PTR, ARG_PTR, ARG2_PTR))
            ])
    
    def testDispatch_method_inquiry(self):
        self.assertDispatcherMethodWithResult(
            'method_inquiry', RESULT_INT, (NAME, OBJ), 
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR,)), 
             ('_return', (RESULT_INT,)),
             ('_cleanup', (OBJ_PTR,))
            ])
    
    def testDispatch_method_lenfunc(self):
        self.assertDispatcherMethodWithResult(
            'method_lenfunc', RESULT_SSIZE, (NAME, OBJ), 
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR,)), 
             ('_return', (RESULT_SSIZE,)),
             ('_cleanup', (OBJ_PTR,))
            ])
    
    def testDispatch_method_getter(self):
        self.assertDispatcherMethod(
            'method_getter', (NAME, OBJ, CLOSURE),
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR, CLOSURE)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, RESULT_PTR))
            ])
    
    def testDispatch_method_selfarg(self):
        self.assertDispatcherMethod(
            'method_selfarg', (NAME, OBJ),
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR,)), 
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, RESULT_PTR,))
            ])
        
    @WithMapper
    def testDispatch_method_selfarg_errorHandler(self, mapper, _):
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, RESULT_PTR)
        self.assertEquals(
            dispatcher.method_selfarg(NAME, OBJ, FuncReturning(None, calls, 'ErrorHandler')), 
            RESULT)
        self.assertEquals(
            calls,
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR,)), 
             ('ErrorHandler', (RESULT_PTR,)),
             ('_return_retrieve', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, RESULT_PTR,))
            ])

    @WithMapper
    def testDispatch_method_selfarg_errorHandlerError(self, mapper, _):
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, RESULT_PTR)
        self.assertRaises(
            ValueError, 
            dispatcher.method_selfarg,
            NAME, OBJ, FuncRaising(ValueError, calls, 'ErrorHandler'))
        self.assertEquals(
            calls,
            [('_store', (OBJ,)),
             (NAME, (OBJ_PTR,)), 
             ('ErrorHandler', (RESULT_PTR,)),
             ('_cleanup', (OBJ_PTR, RESULT_PTR,))
            ])

    @WithMapper
    def testDispatch_method_setter(self, mapper, _):
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, 0)
        dispatcher.method_setter(NAME, OBJ, ARG, CLOSURE)
        self.assertEquals(
            calls, 
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             (NAME, (OBJ_PTR, ARG_PTR, CLOSURE)), 
             ('_cleanup', (OBJ_PTR, ARG_PTR)),
             ('_check_error', ()),
             ('_return', ()),
            ])

    @WithMapper
    def testDispatch_method_setter_error(self, mapper, _):
        calls = []
        dispatcher = self.getPatchedDispatcher(mapper, calls, -1)
        self.assertRaises(Exception, dispatcher.method_setter, NAME, OBJ, ARG, CLOSURE)
        self.assertEquals(
            calls, 
            [('_store', (OBJ,)),
             ('_store', (ARG,)),
             (NAME, (OBJ_PTR, ARG_PTR, CLOSURE)), 
             ('_cleanup', (OBJ_PTR, ARG_PTR)),
             ('_check_error', ()),
            ])

class IckyDispatchTest(DispatchTestCase):
    
    def getVars(self):
        class klass(object):
            pass
        instance = klass()
        storeMap = {
            klass: TYPE_PTR,
            instance: INSTANCE_PTR,
            INSTANCE_PTR: instance}
        return klass, instance, storeMap
    
    def getMapperPatchedDispatcher(
            self, realMapper, calls, dgtResult, hasPtr=False, _checkErrorFails=False, storeMap=None):
        class MockMapper(object):
            def StoreBridge(self, ptr, item):
                calls.append(('StoreBridge', (ptr, item)))
            def Strengthen(self, item):
                calls.append(('Strengthen', (item,)))
            def HasPtr(self, ptr):
                calls.append(('HasPtr', (ptr,)))
                return hasPtr
            def IncRef(self, ptr):
                calls.append(('IncRef', (ptr,)))
            def DecRef(self, ptr):
                calls.append(('DecRef', (ptr,)))
            def RefCount(self, ptr):
                calls.append(('RefCount', (ptr,)))
                return 2
            def Unmap(self, ptr):
                calls.append(('Unmap', (ptr,)))
            def CheckBridgePtrs(self):
                calls.append(('CheckBridgePtrs', ()))
                
        _ptrmap = dict(PTRMAP)
        if storeMap:
            _ptrmap.update(storeMap)
        def _store(item):
            calls.append(('_store', (item,)))
            if isinstance(item, dict):
                item = EvilHackDict(item)
            if item is NULL:
                return NULL_PTR
            return _ptrmap[item]

        
        dispatcher = self.getPatchedDispatcher(realMapper, calls, dgtResult, mockMapper=MockMapper())
        dispatcher._store = _store
        if _checkErrorFails:
            dispatcher._check_error = FuncRaising(ValueError, calls, '_check_error')
        return dispatcher
        
    
    @WithMapper
    def testDispatch_construct_singleton(self, mapper, _):
        klass, _, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(
            mapper, calls, RESULT_PTR, hasPtr=True, storeMap=storeMap)
        
        self.assertEquals(
            dispatcher.construct(NAME, klass, *ARGS, **KWARGS),
            RESULT)

        self.assertEquals(calls, [
            ('_store', (klass,)),
            ('_store', (ARGS,)),
            ('_store', (KWARGS,)),
            (NAME, (TYPE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_check_error', ()),
            ('_return_retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, KWARGS_PTR)),
        ])


    @WithMapper
    def testDispatch_construct_nokwargs(self, mapper, _):
        klass, _, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(
            mapper, calls, RESULT_PTR, hasPtr=True, storeMap=storeMap)
        mapper.DispatcherModule.Null = NULL
        self.assertEquals(
            dispatcher.construct(NAME, klass, *ARGS),
            RESULT)

        self.assertEquals(calls, [
            ('_store', (klass,)),
            ('_store', (ARGS,)),
            ('_store', (NULL,)),
            (NAME, (TYPE_PTR, ARGS_PTR, NULL_PTR)), 
            ('_check_error', ()),
            ('_return_retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, NULL_PTR)),
        ])


    @WithMapper
    def testDispatch_construct_error(self, mapper, _):
        klass, _, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(
            mapper, calls, RESULT_PTR, _checkErrorFails=True, storeMap=storeMap)
        
        self.assertRaises(ValueError,
            dispatcher.construct, NAME, klass, *ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('_store', (klass,)),
            ('_store', (ARGS,)),
            ('_store', (KWARGS,)),
            (NAME, (TYPE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_check_error', ()),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, KWARGS_PTR)),
        ])

    @WithMapper
    def testDispatch_init(self, mapper, _):
        _, instance, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(mapper, calls, 0, storeMap=storeMap)
        dispatcher.init(NAME, instance, *ARGS, **KWARGS)
        mapper.DispatcherModule.Null = NULL
        self.assertEquals(calls, [
            ('_store', (instance,)),
            ('_store', (ARGS,)),
            ('_store', (KWARGS,)),
            (NAME, (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)),
            ('_check_error', ())
        ])


    @WithMapper
    def testDispatch_init_nokwargs(self, mapper, _):
        _, instance, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(mapper, calls, 0, storeMap=storeMap)
        dispatcher.init(NAME, instance, *ARGS)
        mapper.DispatcherModule.Null = NULL
        self.assertEquals(calls, [
            ('_store', (instance,)),
            ('_store', (ARGS,)),
            ('_store', (NULL,)),
            (NAME, (INSTANCE_PTR, ARGS_PTR, NULL_PTR)), 
            ('_cleanup', (INSTANCE_PTR, ARGS_PTR, NULL_PTR)),
            ('_check_error', ())
        ])


    @WithMapper
    def testDispatch_init_noimplementation(self, mapper, _):
        klass, instance, storeMap = self.getVars()
        calls = []
        
        dispatcher = self.getMapperPatchedDispatcher(mapper, calls, -1, storeMap=storeMap)
        dispatcher.init('dgt_not_there', instance, *ARGS, **KWARGS)
        self.assertEquals(calls, [])


    @WithMapper
    def testDispatch_init_error(self, mapper, _):
        klass, instance, storeMap = self.getVars()
        calls = []
        
        dispatcher = self.getMapperPatchedDispatcher(mapper, calls, -1, _checkErrorFails=True, storeMap=storeMap)
        self.assertRaises(ValueError, lambda: dispatcher.init(NAME, instance, *ARGS, **KWARGS))
        self.assertEquals(calls, [
            ('_store', (instance,)),
            ('_store', (ARGS,)),
            ('_store', (KWARGS,)),
            (NAME, (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)),
            ('_check_error', ())
        ])


    @WithMapper
    def testDispatchDelete(self, mapper, _):
        _, instance, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(mapper, calls, None, storeMap=storeMap)
        dispatcher.delete(instance)
        self.assertEquals(calls, [
            ('_store', (instance,)),
            ('RefCount', (INSTANCE_PTR,)),
            ('CheckBridgePtrs', ()),
            ('DecRef', (INSTANCE_PTR,)),
            ('DecRef', (INSTANCE_PTR,)),
            ('Unmap', (INSTANCE_PTR,)),
            ('_check_error', ()),
        ])


    @WithMapper
    def testDispatchDontDelete(self, mapper, _):
        _, instance, storeMap = self.getVars()
        calls = []
        dispatcher = self.getMapperPatchedDispatcher(mapper, calls, None)
        dispatcher.dontDelete(instance)
        self.assertEquals(calls, [])



class EasyMembersTest(TestCase):
    
    def assertGetsAndSets(self, name, value):
        mapper = Python25Mapper()
        dispatcher = mapper.DispatcherModule.Dispatcher(mapper, {})
        
        ptr = Marshal.AllocHGlobal(SIZE)
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        mapper.StoreBridge(ptr, OBJ)
        
        getattr(dispatcher, 'set_member_' + name)(OBJ, OFFSET, value)
        self.assertEquals(getattr(dispatcher, 'get_member_' + name)(OBJ, OFFSET), value)
        Marshal.FreeHGlobal(ptr)
        mapper.Dispose()
        
    def testDispatch_member_int(self):
        self.assertGetsAndSets('int', 300000)
        
    def testDispatch_member_char(self):
        self.assertGetsAndSets('char', 'x')
        
    def testDispatch_member_ubyte(self):
        self.assertGetsAndSets('ubyte', 200)


class ObjectMembersTest(TestCase):

    @WithMapper
    def testDispatch_set_member_object1(self, mapper, _):
        # was null, set to non-null
        dispatcher = mapper.DispatcherModule.Dispatcher(mapper, {})
        
        value = object()
        valuePtr = mapper.Store(value)
        
        ptr = Marshal.AllocHGlobal(SIZE)
        CPyMarshal.Zero(ptr, SIZE)
        fieldPtr = CPyMarshal.Offset(ptr, OFFSET)
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        mapper.StoreBridge(ptr, OBJ)
        
        dispatcher.set_member_object(OBJ, OFFSET, value)
        self.assertEquals(CPyMarshal.ReadPtr(fieldPtr), valuePtr)
        self.assertEquals(mapper.RefCount(valuePtr), 2, "failed to incref")
        Marshal.FreeHGlobal(ptr)


    @WithMapper
    def testDispatch_set_member_object2(self, mapper, addToCleanUp):
        # was non-null, set to non-null
        dispatcher = mapper.DispatcherModule.Dispatcher(mapper, {})
        
        value1 = object()
        value1Ptr = mapper.Store(value1)
        mapper.IncRef(value1Ptr)
        value2 = object()
        value2Ptr = mapper.Store(value2)
        
        ptr = Marshal.AllocHGlobal(SIZE)
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        fieldPtr = CPyMarshal.Offset(ptr, OFFSET)
        CPyMarshal.WritePtr(fieldPtr, value1Ptr)
        mapper.StoreBridge(ptr, OBJ)
        
        dispatcher.set_member_object(OBJ, OFFSET, value2)
        self.assertEquals(CPyMarshal.ReadPtr(fieldPtr), value2Ptr)
        self.assertEquals(mapper.RefCount(value1Ptr), 1, "failed to decref old object")
        self.assertEquals(mapper.RefCount(value2Ptr), 2, "failed to incref new object")
        Marshal.FreeHGlobal(ptr)


    @WithMapper
    def testDispatch_get_member_object1(self, mapper, addToCleanUp):
        # non-null
        dispatcher = mapper.DispatcherModule.Dispatcher(mapper, {})
        
        value = object()
        valuePtr = mapper.Store(value)
        
        ptr = Marshal.AllocHGlobal(SIZE)
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        fieldPtr = CPyMarshal.Offset(ptr, OFFSET)
        CPyMarshal.WritePtr(fieldPtr, valuePtr)
        mapper.StoreBridge(ptr, OBJ)
        
        self.assertEquals(dispatcher.get_member_object(OBJ, OFFSET), value)
        self.assertEquals(mapper.RefCount(valuePtr), 2, "failed to incref returned object")
        Marshal.FreeHGlobal(ptr)


    @WithMapper
    def testDispatch_get_member_object2(self, mapper, addToCleanUp):
        # null should become None here
        dispatcher = mapper.DispatcherModule.Dispatcher(mapper, {})
        
        ptr = Marshal.AllocHGlobal(SIZE)
        CPyMarshal.Zero(ptr, SIZE)
        CPyMarshal.WriteIntField(ptr, PyObject, 'ob_refcnt', 2)
        fieldPtr = CPyMarshal.Offset(ptr, OFFSET)
        mapper.StoreBridge(ptr, OBJ)
        
        self.assertEquals(dispatcher.get_member_object(OBJ, OFFSET), None)
        Marshal.FreeHGlobal(ptr)
        

suite = makesuite(
    DispatcherTest,
    TrivialDispatchTest,
    SimpleDispatchTest,
    IckyDispatchTest,
    EasyMembersTest, 
    ObjectMembersTest, 
)

if __name__ == '__main__':
    run(suite)
