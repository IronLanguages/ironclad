
from tests.utils.runtest import makesuite, run

from tests.utils.python25mapper import ModuleWrapper
from tests.utils.testcase import TestCase

from System import IntPtr, NullReferenceException
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper

def GetDispatcherClass(mapper):
    moduleDict = mapper.DispatcherModule.Scope.Dict
    moduleScope = mapper.Engine.CreateScope(moduleDict)
    return moduleScope.GetVariable[object]("Dispatcher")


class DispatcherTest(TestCase):
    
    def testMapperCreatesModuleContainingDispatcher(self):
        mapper = Python25Mapper()
        Dispatcher = GetDispatcherClass(mapper)
        self.assertNotEquals(Dispatcher, None, "failed to locate Dispatcher")
        mapper.Dispose()
        
    
    def assertDispatcherUtilityMethod(self, methodname, args, expectedCalls, exceptionSet=None, exceptionAfter=None, expectedExceptionClass=None):
        realMapper = Python25Mapper()
        Dispatcher = GetDispatcherClass(realMapper)
        
        class MockMapper(object):
            def __init__(self):
                self.LastException = exceptionSet
                self.calls = []
            def FreeTemps(self):
                self.calls.append('FreeTemps')
            def DecRef(self, ptr):
                self.calls.append(('DecRef', ptr))
        
        mockMapper = MockMapper()
        dispatcher = Dispatcher(mockMapper, {})
        callmethod = lambda: getattr(dispatcher, methodname)(*args)
        if expectedExceptionClass:
            self.assertRaises(expectedExceptionClass, callmethod)
        else:
            callmethod()
        self.assertEquals(mockMapper.calls, expectedCalls, 'unexpected behaviour')
        self.assertEquals(mockMapper.LastException, exceptionAfter, 'unexpected exception set after call')
        realMapper.Dispose()
        
    
    def testCleanup(self):
        error = ValueError('huh?')
        self.assertDispatcherUtilityMethod(
            '_cleanup', tuple(), ['FreeTemps'])
        self.assertDispatcherUtilityMethod(
            '_cleanup', tuple(), ['FreeTemps'], error, error)
        self.assertDispatcherUtilityMethod(
            '_cleanup', (IntPtr(1), IntPtr.Zero, IntPtr(2)), 
            ['FreeTemps', ('DecRef', IntPtr(1)), ('DecRef', IntPtr(2))], error, error)
    
    def testMaybeRaise(self):
        error = ValueError('huh?')
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', (IntPtr.Zero,), [], None, None, NullReferenceException)
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', (IntPtr.Zero,), [], error, None, ValueError)
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', (IntPtr(1),), [], error, None, ValueError)
    
    def testSurelyRaise(self):
        # this should raise the mapper's LastException, if present;
        # if no LastException, raise the error passed in
        error1 = ValueError('huh?')
        error2 = TypeError('meh')
        self.assertDispatcherUtilityMethod(
            "_surely_raise", (error1,), [], None, None, ValueError)
        self.assertDispatcherUtilityMethod(
            "_surely_raise", (error1,), [], error2, None, TypeError)
    
    

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


RESULT = object()
RESULT_PTR = IntPtr(999)

INSTANCE_PTR = IntPtr(111)
ARGS = (1, 2, 3)
INSTANCE_ARGS = (INSTANCE_PTR, 1, 2, 3)
ARGS_PTR = IntPtr(222)
KWARGS = {"1": 2, "3": 4}
KWARGS_PTR = IntPtr(333)
ARG = object()
ARG_PTR = IntPtr(444)
CLOSURE = IntPtr(555)

class DispatcherDispatchTestCase(TestCase):
    
    def getPatchedDispatcher(self, realMapper, callables, calls, _maybe_raise):
        test = self
        class MockMapper(object):
            def __init__(self):
                self.LastException = None
            
            def Store(self, item):
                calls.append(('Store', (item,)))
                if item == ARG: return ARG_PTR
                if item == ARGS: return ARGS_PTR
                if item == KWARGS: return KWARGS_PTR
            
            def Retrieve(self, ptr):
                test.assertEquals(ptr, RESULT_PTR, "bad result")
                calls.append(('Retrieve', (ptr,)))
                return RESULT
    
            def StoreBridge(self, ptr, item):
                calls.append(('StoreBridge', (ptr, item)))
            
            def RefCount(self, _):
                return reportedRefCount
                
        mockMapper = MockMapper()
        dispatcher = GetDispatcherClass(realMapper)(mockMapper, callables)
        dispatcher._maybe_raise = _maybe_raise
        dispatcher._cleanup = FuncReturning(None, calls, '_cleanup')
        return dispatcher
    
    
    def callDispatcherMethod(self, methodname, *args, **kwargs):
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        method = getattr(dispatcher, methodname)
        self.assertEquals(method('dgt', *args, **kwargs), RESULT, "unexpected result")
        mapper.Dispose()
        return calls
    
    
    def callDispatcherErrorMethod(self, methodname, *args, **kwargs):
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncRaising(ValueError, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        method = getattr(dispatcher, methodname)
        self.assertRaises(ValueError, lambda: method('dgt', *args, **kwargs))
        mapper.Dispose()
        return calls


class DispatcherNoargsTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_noargs(self):
        calls = self.callDispatcherMethod('function_noargs')
        self.assertEquals(calls, [
            ('dgt', (IntPtr.Zero, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
    
    
    def testDispatch_function_noargs_error(self):
        calls = self.callDispatcherErrorMethod('function_noargs')
        self.assertEquals(calls, [
            ('dgt', (IntPtr.Zero, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
    
    
    def testDispatch_method_noargs(self):
        calls = self.callDispatcherMethod('method_noargs', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
    
    
    def testDispatch_method_noargs_error(self):
        calls = self.callDispatcherErrorMethod('method_noargs', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
    
    
class DispatcherVarargsTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_varargs(self):
        calls = self.callDispatcherMethod('function_varargs', *ARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR))
        ])
    
    
    def testDispatch_function_varargs_error(self):
        calls = self.callDispatcherErrorMethod('function_varargs', *ARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR))
        ])
    
    
    def testDispatch_method_varargs(self):
        calls = self.callDispatcherMethod('method_varargs', *INSTANCE_ARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR))
        ])
    
    
    def testDispatch_method_varargs_error(self):
        calls = self.callDispatcherErrorMethod('method_varargs', *INSTANCE_ARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR))
        ])


class DispatcherObjargTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_objarg(self):
        calls = self.callDispatcherMethod('function_objarg', ARG)
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (IntPtr.Zero, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_function_objarg_error(self):
        calls = self.callDispatcherErrorMethod('function_objarg', ARG)
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (IntPtr.Zero, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_objarg(self):
        calls = self.callDispatcherMethod('method_objarg', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_objarg_error(self):
        calls = self.callDispatcherErrorMethod('method_objarg', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARG_PTR))
        ])


class DispatcherSelfargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_selfarg(self):
        calls = self.callDispatcherMethod('method_selfarg', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR,)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
    
    def testDispatch_method_selfarg_error(self):
        calls = self.callDispatcherErrorMethod('method_selfarg', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR,)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
        
    def testDispatch_method_selfarg_errorHandler(self):
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        def ErrorHandler(ptr):
            calls.append(("ErrorHandler", (ptr,)))
        
        self.assertEquals(dispatcher.method_selfarg('dgt', INSTANCE_PTR, ErrorHandler), RESULT, "unexpected result")
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR,)), 
            ('ErrorHandler', (RESULT_PTR,)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
        mapper.Dispose()
        
    def testDispatch_method_selfarg_errorHandlerError(self):
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        def ErrorHandler(ptr):
            calls.append(("ErrorHandler", (ptr,)))
            raise Exception()
        
        self.assertRaises(Exception, lambda: dispatcher.method_selfarg('dgt', INSTANCE_PTR, ErrorHandler))
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR,)), 
            ('ErrorHandler', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
        mapper.Dispose()
    

    
class DispatcherKwargsTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_kwargs(self):
        calls = self.callDispatcherMethod('function_kwargs', *ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_function_kwargs_error(self):
        calls = self.callDispatcherErrorMethod('function_kwargs', *ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_function_kwargs_withoutActualKwargs(self):
        calls = self.callDispatcherMethod('function_kwargs', *ARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, IntPtr.Zero))
        ])
    
    
    def testDispatch_method_kwargs(self):
        calls = self.callDispatcherMethod('method_kwargs', *INSTANCE_ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_method_kwargs_error(self):
        calls = self.callDispatcherErrorMethod('method_kwargs', *INSTANCE_ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_method_kwargs_withoutActualKwargs(self):
        calls = self.callDispatcherMethod('method_kwargs', *INSTANCE_ARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR, ARGS_PTR, IntPtr.Zero))
        ])


class DispatcherGetterTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_getter(self):
        calls = self.callDispatcherMethod('method_getter', INSTANCE_PTR, CLOSURE)
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR, CLOSURE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])
    
    def testDispatch_method_getter_error(self):
        calls = self.callDispatcherErrorMethod('method_getter', INSTANCE_PTR, CLOSURE)
        self.assertEquals(calls, [
            ('dgt', (INSTANCE_PTR, CLOSURE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (RESULT_PTR,))
        ])


class DispatcherSetterTest(DispatcherDispatchTestCase):

    def testDispatch_method_setter(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(0, calls, 'dgt'),
        }
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        dispatcher.method_setter('dgt', INSTANCE_PTR, ARG, CLOSURE)
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, CLOSURE)), 
            ('_cleanup', (ARG_PTR,)),
        ])
        mapper.Dispose()

    def testDispatch_method_setter_error(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(-1, calls, 'dgt'),
        }
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        self.assertRaises(Exception, lambda: dispatcher.method_setter('dgt', INSTANCE_PTR, ARG, CLOSURE))
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, CLOSURE)), 
            ('_cleanup', (ARG_PTR,)),
        ])
        mapper.Dispose()

    def testDispatch_method_setter_specificError(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(-1, calls, 'dgt'),
        }
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        dispatcher.mapper.LastException = ValueError("arrgh!")
        self.assertRaises(ValueError, lambda: dispatcher.method_setter('dgt', INSTANCE_PTR, ARG, CLOSURE))
        self.assertEquals(dispatcher.mapper.LastException, None, "failed to clear error")
        self.assertEquals(calls, [
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, CLOSURE)), 
            ('_cleanup', (ARG_PTR,)),
        ])
        mapper.Dispose()
    

TYPE_PTR = IntPtr(555)

def CallWithFakeObjectInDispatcherModule(mapper, calls, callWithFakeObject):
    class FakeObject(object):
        def __new__(cls):
            calls.append(('__new__', (cls,)))
            return cls()

    moduleDict = mapper.DispatcherModule.Scope.Dict
    moduleScope = mapper.Engine.CreateScope(moduleDict)
    moduleScope.SetVariable('object', FakeObject)
    try:
        return callWithFakeObject()
    finally:
        moduleScope.SetVariable('object', object)


class DispatcherConstructTest(DispatcherDispatchTestCase):
    # NOTE: a failing __new__ will leak memory. However, if __new__ fails,
    # the want of a few bytes is unlikely to be your primary concern.
    
    def testDispatch_construct(self):
        class klass(object):
            _typePtr = TYPE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        result = CallWithFakeObjectInDispatcherModule(
            mapper, calls, lambda: dispatcher.construct('dgt', klass, *ARGS, **KWARGS))
        
        self.assertEquals(result._instancePtr, RESULT_PTR, "instance lacked reference to its alter-ego")
        self.assertEquals(calls, [
            ('__new__', (klass,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (TYPE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
            ('StoreBridge', (RESULT_PTR, result))
        ])
        mapper.Dispose()
    
    def testDispatch_construct_error(self):
        class klass(object):
            _typePtr = TYPE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncRaising(ValueError, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        testCall = lambda: CallWithFakeObjectInDispatcherModule(
            mapper, calls, lambda: dispatcher.construct('dgt', klass, *ARGS, **KWARGS))
        self.assertRaises(ValueError, testCall)
        
        self.assertEquals(calls, [
            ('__new__', (klass,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (TYPE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
        ])
        mapper.Dispose()

        
class DispatcherInitTest(DispatcherDispatchTestCase):
    # NOTE: we couldn't work out how to test that object.__init__ was called...
    # but we also couldn't work out what would go wrong, so we don't actually call it.
    # This will probably change at some stage.
    
    def testDispatch_init(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(0, calls, 'dgt'),
        }
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        dispatcher.init('dgt', instance, *ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
        ])
        mapper.Dispose()
    
    def testDispatch_init_null(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {}
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        dispatcher.init('dgt_not_there', instance, *ARGS, **KWARGS)
        self.assertEquals(calls, [])
        mapper.Dispose()
        
    
    def testDispatch_init_error(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(-1, calls, 'dgt'),
        }
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        self.assertRaises(Exception, lambda: dispatcher.init('dgt', instance, *ARGS, **KWARGS))
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
        ])
        mapper.Dispose()
    
    def testDispatch_init_specificError(self):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(-1, calls, 'dgt'),
        }
        
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, lambda _: None)
        dispatcher.mapper.LastException = ValueError('arrgh!')
        self.assertRaises(ValueError, lambda: dispatcher.init('dgt', instance, *ARGS, **KWARGS))
        self.assertEquals(dispatcher.mapper.LastException, None, "failed to clear error")
        self.assertEquals(calls, [
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
        ])
        mapper.Dispose()


class DispatcherDeleteTest(TestCase):
        
    def assertDispatchDelete(self, mockMapper, calls, expectedCalls):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mockMapper, {})
        dispatcher.delete(instance)
        self.assertEquals(calls, expectedCalls)
        mapper.Dispose()


    def testDispatchDeleteNormal(self):
        calls = []
        class MockMapper(object):
            Alive = True
            def CheckBridgePtrs(self):
                calls.append(('CheckBridgePtrs',))
            def DecRef(self, ptr):
                calls.append(('DecRef', ptr))
        
        expectedCalls = [
            ('CheckBridgePtrs',),
            ('DecRef', INSTANCE_PTR),
        ]
        self.assertDispatchDelete(MockMapper(), calls, expectedCalls)
    
    def testDispatchDeleteDeadMapper(self):
        class MockMapper(object):
            Alive = False
        self.assertDispatchDelete(MockMapper(), [], [])
        



class DispatcherSimpleMembersTest(TestCase):
    
    def assertGetsAndSets(self, name, value):
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mapper, {})
        
        ptr = Marshal.AllocHGlobal(16)
        getattr(dispatcher, 'set_member_' + name)(ptr, value)
        self.assertEquals(getattr(dispatcher, 'get_member_' + name)(ptr), value)
        Marshal.FreeHGlobal(ptr)
        
        mapper.Dispose()
        
        
    def testDispatch_member_int(self):
        self.assertGetsAndSets('int', 30000)
        
        
    def testDispatch_member_char(self):
        self.assertGetsAndSets('char', 'x')
        
        
    def testDispatch_member_ubyte(self):
        self.assertGetsAndSets('ubyte', 200)


class DispatcherObjectMembersTest(TestCase):

    def testDispatch_set_member_object1(self):
        # was null, set to non-null
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mapper, {})
        
        value = object()
        valuePtr = mapper.Store(value)
        
        ptr = Marshal.AllocHGlobal(4)
        CPyMarshal.Zero(ptr, 4)
        dispatcher.set_member_object(ptr, value)
        self.assertEquals(CPyMarshal.ReadPtr(ptr), valuePtr)
        self.assertEquals(mapper.RefCount(valuePtr), 2, "failed to incref")
        Marshal.FreeHGlobal(ptr)
        
        mapper.Dispose()

    def testDispatch_set_member_object2(self):
        # was non-null, set to non-null
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mapper, {})
        
        value1 = object()
        value1Ptr = mapper.Store(value1)
        mapper.IncRef(value1Ptr)
        value2 = object()
        value2Ptr = mapper.Store(value2)
        
        ptr = Marshal.AllocHGlobal(4)
        CPyMarshal.WritePtr(ptr, value1Ptr)
        
        dispatcher.set_member_object(ptr, value2)
        self.assertEquals(CPyMarshal.ReadPtr(ptr), value2Ptr)
        self.assertEquals(mapper.RefCount(value1Ptr), 1, "failed to decref old object")
        self.assertEquals(mapper.RefCount(value2Ptr), 2, "failed to incref new object")
        Marshal.FreeHGlobal(ptr)
        
        mapper.Dispose()

    def testDispatch_get_member_object1(self):
        # non-null
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mapper, {})
        
        value = object()
        valuePtr = mapper.Store(value)
        
        ptr = Marshal.AllocHGlobal(4)
        CPyMarshal.WritePtr(ptr, valuePtr)
        self.assertEquals(dispatcher.get_member_object(ptr), value)
        Marshal.FreeHGlobal(ptr)
        
        mapper.Dispose()

    def testDispatch_get_member_object2(self):
        # null should become None here
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mapper, {})
        
        ptr = Marshal.AllocHGlobal(4)
        CPyMarshal.Zero(ptr, 4)
        self.assertEquals(dispatcher.get_member_object(ptr), None)
        Marshal.FreeHGlobal(ptr)
        
        mapper.Dispose()
        
        


suite  = makesuite(
    DispatcherTest,
    DispatcherNoargsTest, 
    DispatcherVarargsTest, 
    DispatcherObjargTest,
    DispatcherSelfargTest,
    DispatcherKwargsTest, 
    DispatcherGetterTest,
    DispatcherSetterTest,
    DispatcherConstructTest,
    DispatcherInitTest,
    DispatcherDeleteTest,
    DispatcherSimpleMembersTest,
    DispatcherObjectMembersTest,
)

if __name__ == '__main__':
    run(suite)