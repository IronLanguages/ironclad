
from tests.utils.runtest import makesuite, run

from tests.utils.dispatcher import GetDispatcherClass
from tests.utils.testcase import TestCase

from System import IntPtr, NullReferenceException
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper


class DispatcherTest(TestCase):
    
    def testMapperCreatesModuleContainingDispatcher(self):
        mapper = Python25Mapper()
        Dispatcher = GetDispatcherClass(mapper)
        self.assertNotEquals(Dispatcher, None, "failed to locate Dispatcher")
        mapper.Dispose()
        
        
    def testDisposeMapperPreventsDispatcherDelete(self):
        mapper = Python25Mapper()
        Dispatcher = GetDispatcherClass(mapper)
        dontDelete = Dispatcher.dontDelete
        mapper.Dispose()
        self.assertEquals(Dispatcher.delete, dontDelete)
        
    
    def assertDispatcherUtilityMethod(self, methodname, args, expectedCalls, exceptionSet=None, exceptionAfter=None, expectedExceptionClass=None):
        realMapper = Python25Mapper()
        Dispatcher = GetDispatcherClass(realMapper)
        
        class MockMapper(object):
            def __init__(self):
                self.LastException = exceptionSet
                self.calls = []
            def FreeTemps(self):
                self.calls.append('FreeTemps')
            def IncRef(self, ptr):
                self.calls.append(('IncRef', ptr))
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
    
    def testMaybeIncRef(self):
        self.assertDispatcherUtilityMethod(
            '_maybe_incref', (IntPtr.Zero,), [])
        self.assertDispatcherUtilityMethod(
            '_maybe_incref', (IntPtr(123),), [('IncRef', IntPtr(123))])
    
    def testMaybeRaise(self):
        error = ValueError('huh?')
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', (IntPtr.Zero,), [], None, None, NullReferenceException)
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', (IntPtr.Zero,), [], error, None, ValueError)
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', (IntPtr(1),), [], error, None, ValueError)
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', tuple(), [])
        self.assertDispatcherUtilityMethod(
            '_maybe_raise', tuple(), [], error, None, ValueError)
    
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
RESULT_INT = 123
RESULT_PTR = IntPtr(999)
RESULT_SSIZE = 99999

INSTANCE_PTR = IntPtr(111)
ARGS = (1, 2, 3)
INSTANCE_ARGS = (INSTANCE_PTR, 1, 2, 3)
ARGS_PTR = IntPtr(222)
KWARGS = {"1": 2, "3": 4}
KWARGS_PTR = IntPtr(333)
ARG = object()
ARG_PTR = IntPtr(444)
CLOSURE = IntPtr(555)
SSIZE = 123456
SSIZE2 = 789012
ARG2 = object()
ARG2_PTR = IntPtr(666)

class DispatcherDispatchTestCase(TestCase):
    
    def getPatchedDispatcher(self, realMapper, callables, calls, _maybe_raise, hasPtr=False, retrieveResult=None, storeMap=None):
        test = self
        class MockMapper(object):
            def __init__(self):
                self.LastException = None
            
            def Store(self, item):
                calls.append(('Store', (item,)))
                if item == ARG: return ARG_PTR
                if item == ARG2: return ARG2_PTR
                if item == ARGS: return ARGS_PTR
                if item == KWARGS: return KWARGS_PTR
                if storeMap:
                    return storeMap[item]
            
            def Retrieve(self, ptr):
                test.assertEquals(ptr, RESULT_PTR, "bad result")
                calls.append(('Retrieve', (ptr,)))
                if retrieveResult is not None:
                    return retrieveResult
                return RESULT
    
            def StoreBridge(self, ptr, item):
                calls.append(('StoreBridge', (ptr, item)))
    
            def Strengthen(self, item):
                calls.append(('Strengthen', (item,)))
                
            def HasPtr(self, ptr):
                calls.append(('HasPtr', (ptr,)))
                return hasPtr
            
            def IncRef(self, ptr):
                calls.append(('IncRef', (ptr,)))
                
        mockMapper = MockMapper()
        dispatcher = GetDispatcherClass(realMapper)(mockMapper, callables)
        dispatcher._maybe_raise = _maybe_raise
        dispatcher._maybe_incref = FuncReturning(None, calls, '_maybe_incref')
        dispatcher._cleanup = FuncReturning(None, calls, '_cleanup')
        return dispatcher
    
    def callDispatcherMethod(self, methodname, *args, **kwargs):
        return self.callDispatcherMethodWithResults(methodname, RESULT_PTR, RESULT, *args, **kwargs)
    
    def callDispatcherMethodWithResults(self, methodname, dgtResult, dispatchResult, *args, **kwargs):
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(dgtResult, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise)
        
        method = getattr(dispatcher, methodname)
        self.assertEquals(method('dgt', *args, **kwargs), dispatchResult)
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
            ('_maybe_incref', (IntPtr.Zero,)),
            ('dgt', (IntPtr.Zero, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR,))
        ])
    
    def testDispatch_function_noargs_error(self):
        calls = self.callDispatcherErrorMethod('function_noargs')
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('dgt', (IntPtr.Zero, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR,))
        ])
    
    
    def testDispatch_method_noargs(self):
        calls = self.callDispatcherMethod('method_noargs', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR))
        ])
    
    
    def testDispatch_method_noargs_error(self):
        calls = self.callDispatcherErrorMethod('method_noargs', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR))
        ])
    
    
class DispatcherVarargsTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_varargs(self):
        calls = self.callDispatcherMethod('function_varargs', *ARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARGS_PTR))
        ])
    
    
    def testDispatch_function_varargs_error(self):
        calls = self.callDispatcherErrorMethod('function_varargs', *ARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARGS_PTR))
        ])
    
    
    def testDispatch_method_varargs(self):
        calls = self.callDispatcherMethod('method_varargs', *INSTANCE_ARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARGS_PTR))
        ])
    
    
    def testDispatch_method_varargs_error(self):
        calls = self.callDispatcherErrorMethod('method_varargs', *INSTANCE_ARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARGS_PTR))
        ])


class DispatcherObjargTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_objarg(self):
        calls = self.callDispatcherMethod('function_objarg', ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARG,)),
            ('dgt', (IntPtr.Zero, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_function_objarg_error(self):
        calls = self.callDispatcherErrorMethod('function_objarg', ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARG,)),
            ('dgt', (IntPtr.Zero, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_objarg(self):
        calls = self.callDispatcherMethod('method_objarg', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_objarg_error(self):
        calls = self.callDispatcherErrorMethod('method_objarg', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_objarg_swapped(self):
        calls = self.callDispatcherMethod('method_objarg_swapped', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (ARG_PTR, INSTANCE_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_objarg_swapped_error(self):
        calls = self.callDispatcherErrorMethod('method_objarg_swapped', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (ARG_PTR, INSTANCE_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])


class DispatcherSelfargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_selfarg(self):
        calls = self.callDispatcherMethod('method_selfarg', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])
    
    def testDispatch_method_selfarg_error(self):
        calls = self.callDispatcherErrorMethod('method_selfarg', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)), 
            ('ErrorHandler', (RESULT_PTR,)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)), 
            ('ErrorHandler', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])
        mapper.Dispose()
    

    
class DispatcherKwargsTest(DispatcherDispatchTestCase):
    
    def testDispatch_function_kwargs(self):
        calls = self.callDispatcherMethod('function_kwargs', *ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_function_kwargs_error(self):
        calls = self.callDispatcherErrorMethod('function_kwargs', *ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_function_kwargs_withoutActualKwargs(self):
        calls = self.callDispatcherMethod('function_kwargs', *ARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (IntPtr.Zero,)),
            ('Store', (ARGS,)),
            ('dgt', (IntPtr.Zero, ARGS_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (IntPtr.Zero, RESULT_PTR, ARGS_PTR, IntPtr.Zero))
        ])
    
    
    def testDispatch_method_kwargs(self):
        calls = self.callDispatcherMethod('method_kwargs', *INSTANCE_ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_method_kwargs_error(self):
        calls = self.callDispatcherErrorMethod('method_kwargs', *INSTANCE_ARGS, **KWARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARGS_PTR, KWARGS_PTR))
        ])
    
    
    def testDispatch_method_kwargs_withoutActualKwargs(self):
        calls = self.callDispatcherMethod('method_kwargs', *INSTANCE_ARGS)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, IntPtr.Zero)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARGS_PTR, IntPtr.Zero))
        ])


class DispatcherSsizeargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_ssizearg(self):
        calls = self.callDispatcherMethod('method_ssizearg', INSTANCE_PTR, SSIZE)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, SSIZE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])
    
    def testDispatch_method_ssizearg_error(self):
        calls = self.callDispatcherErrorMethod('method_ssizearg', INSTANCE_PTR, SSIZE)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, SSIZE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])


class DispatcherSsizeobjargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_ssizeobjarg(self):
        calls = self.callDispatcherMethodWithResults('method_ssizeobjarg', RESULT_INT, RESULT_INT, INSTANCE_PTR, SSIZE, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, SSIZE, ARG_PTR)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,))
        ])
    
    def testDispatch_method_ssizeobjarg_error(self):
        calls = self.callDispatcherErrorMethod('method_ssizeobjarg', INSTANCE_PTR, SSIZE, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, SSIZE, ARG_PTR)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,))
        ])


class DispatcherSsizessizeargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_ssizessizearg(self):
        calls = self.callDispatcherMethod('method_ssizessizearg', INSTANCE_PTR, SSIZE, SSIZE2)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, SSIZE, SSIZE2)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])
    
    def testDispatch_method_ssizessizearg_error(self):
        calls = self.callDispatcherErrorMethod('method_ssizessizearg', INSTANCE_PTR, SSIZE, SSIZE2)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, SSIZE, SSIZE2)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])


class DispatcherSsizessizeobjargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_ssizessizeobjarg(self):
        calls = self.callDispatcherMethodWithResults('method_ssizessizeobjarg', RESULT_INT, RESULT_INT, INSTANCE_PTR, SSIZE, SSIZE2, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, SSIZE, SSIZE2, ARG_PTR)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,))
        ])
    
    def testDispatch_method_ssizessizeobjarg_error(self):
        calls = self.callDispatcherErrorMethod('method_ssizessizeobjarg', INSTANCE_PTR, SSIZE, SSIZE2, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, SSIZE, SSIZE2, ARG_PTR)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,))
        ])


class DispatcherObjobjargTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_objobjarg(self):
        calls = self.callDispatcherMethodWithResults('method_objobjarg', RESULT_INT, RESULT_INT, INSTANCE_PTR, ARG, ARG2)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('Store', (ARG2,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, ARG2_PTR)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR, ARG_PTR, ARG2_PTR))
        ])
    
    def testDispatch_method_objobjarg_error(self):
        calls = self.callDispatcherErrorMethod('method_objobjarg', INSTANCE_PTR, ARG, ARG2)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('Store', (ARG2,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, ARG2_PTR)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR, ARG_PTR, ARG2_PTR))
        ])


class DispatcherInquiryTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_inquiry(self):
        calls = self.callDispatcherMethodWithResults('method_inquiry', RESULT_INT, RESULT_INT, INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR,)),
        ])
    
    def testDispatch_method_inquiry_error(self):
        calls = self.callDispatcherErrorMethod('method_inquiry', INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR,)),
        ])


class DispatcherTernaryTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_ternary(self):
        calls = self.callDispatcherMethod('method_ternary', INSTANCE_PTR, ARG, ARG2)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('Store', (ARG2,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, ARG2_PTR)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR, ARG2_PTR))
        ])
    
    def testDispatch_method_ternary_error(self):
        calls = self.callDispatcherErrorMethod('method_ternary', INSTANCE_PTR, ARG, ARG2)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('Store', (ARG2,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, ARG2_PTR)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR, ARG2_PTR))
        ])
    
    
    # method_ternary_swapped only takes 2 args, but calls a ternaryfunc
    # see __rpow__ docs
    def testDispatch_method_ternary_swapped(self):
        calls = self.callDispatcherMethod('method_ternary_swapped', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (ARG_PTR, INSTANCE_PTR, IntPtr.Zero)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_ternary_swapped_error(self):
        calls = self.callDispatcherErrorMethod('method_ternary_swapped', INSTANCE_PTR, ARG)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (ARG_PTR, INSTANCE_PTR, IntPtr.Zero)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])


class DispatcherRichcmpTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_richcmp(self):
        calls = self.callDispatcherMethod('method_richcmp', INSTANCE_PTR, ARG, SSIZE)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, SSIZE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])
    
    def testDispatch_method_richcmp_error(self):
        calls = self.callDispatcherErrorMethod('method_richcmp', INSTANCE_PTR, ARG, SSIZE)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, SSIZE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR, ARG_PTR))
        ])


class DispatcherLenfuncTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_lenfunc(self):
        calls = self.callDispatcherMethodWithResults('method_lenfunc', RESULT_INT, RESULT_INT, INSTANCE_PTR)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR,)),
            ('_maybe_raise', tuple()),
            ('_cleanup', (INSTANCE_PTR,)),
        ])
        

class DispatcherGetterTest(DispatcherDispatchTestCase):
    
    def testDispatch_method_getter(self):
        calls = self.callDispatcherMethod('method_getter', INSTANCE_PTR, CLOSURE)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, CLOSURE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
        ])
    
    def testDispatch_method_getter_error(self):
        calls = self.callDispatcherErrorMethod('method_getter', INSTANCE_PTR, CLOSURE)
        self.assertEquals(calls, [
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('dgt', (INSTANCE_PTR, CLOSURE)),
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (INSTANCE_PTR, RESULT_PTR,))
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, CLOSURE)), 
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,)),
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, CLOSURE)), 
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,)),
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARG,)),
            ('dgt', (INSTANCE_PTR, ARG_PTR, CLOSURE)), 
            ('_cleanup', (INSTANCE_PTR, ARG_PTR,)),
        ])
        mapper.Dispose()
    

TYPE_PTR = IntPtr(555)

def CallWithFakeObjectInDispatcherModule(mapper, calls, callWithFakeObject):
    class FakeObject(object):
        def __new__(cls):
            calls.append(('__new__', (cls,)))
            return cls()

    mapper.DispatcherModule.object = FakeObject
    try:
        return callWithFakeObject()
    finally:
        mapper.DispatcherModule.object = object


class DispatcherConstructTest(DispatcherDispatchTestCase):
    # NOTE: a failing __new__ will leak memory. However, if __new__ fails,
    # the want of a few bytes is unlikely to be your primary concern.
    
    def testDispatch_construct(self):
        class klass(object):
            pass
        storeMap = {klass: TYPE_PTR}
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise, storeMap=storeMap)
        
        result = CallWithFakeObjectInDispatcherModule(
            mapper, calls, lambda: dispatcher.construct('dgt', klass, *ARGS, **KWARGS))
        
        self.assertEquals(result._instancePtr, RESULT_PTR, "instance lacked reference to its alter-ego")
        self.assertEquals(calls, [
            ('__new__', (klass,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('Store', (klass,)),
            ('dgt', (TYPE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
            ('HasPtr', (RESULT_PTR,)),
            ('StoreBridge', (RESULT_PTR, result)),
            ('Strengthen', (result,))
        ])
        mapper.Dispose()
    
    def testDispatch_construct_singleton(self):
        class klass(object):
            pass
        storeMap = {klass: TYPE_PTR}
        
        originalObj = klass()
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncReturning(None, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(
            mapper, callables, calls, _maybe_raise, hasPtr=True, retrieveResult=originalObj, storeMap=storeMap)
        
        result = CallWithFakeObjectInDispatcherModule(
            mapper, calls, lambda: dispatcher.construct('dgt', klass, *ARGS, **KWARGS))
        
        self.assertEquals(result, originalObj, "did not return original object")
        self.assertEquals(calls, [
            ('__new__', (klass,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('Store', (klass,)),
            ('dgt', (TYPE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_maybe_raise', (RESULT_PTR,)),
            ('_cleanup', (ARGS_PTR, KWARGS_PTR)),
            ('HasPtr', (RESULT_PTR,)),
            ('IncRef', (RESULT_PTR,)),
            ('Retrieve', (RESULT_PTR,)),
        ])
        mapper.Dispose()
    
    def testDispatch_construct_error(self):
        class klass(object):
            pass
        storeMap = {klass: TYPE_PTR}
        
        mapper = Python25Mapper()
        calls = []
        callables = {
            'dgt': FuncReturning(RESULT_PTR, calls, 'dgt'),
        }
        _maybe_raise = FuncRaising(ValueError, calls, '_maybe_raise')
        dispatcher = self.getPatchedDispatcher(mapper, callables, calls, _maybe_raise, storeMap=storeMap)
        
        testCall = lambda: CallWithFakeObjectInDispatcherModule(
            mapper, calls, lambda: dispatcher.construct('dgt', klass, *ARGS, **KWARGS))
        self.assertRaises(ValueError, testCall)
        
        self.assertEquals(calls, [
            ('__new__', (klass,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('Store', (klass,)),
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)),
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)),
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
            ('_maybe_incref', (INSTANCE_PTR,)),
            ('Store', (ARGS,)),
            ('Store', (KWARGS,)),
            ('dgt', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)), 
            ('_cleanup', (INSTANCE_PTR, ARGS_PTR, KWARGS_PTR)),
        ])
        mapper.Dispose()


class DispatcherDeleteTest(TestCase):
    
    def assertDispatchDelete(self, mockMapper, calls, expectedCalls, method='delete'):
        class klass(object):
            pass
        instance = klass()
        instance._instancePtr = INSTANCE_PTR
        
        mapper = Python25Mapper()
        dispatcher = GetDispatcherClass(mapper)(mockMapper, {})
        getattr(dispatcher, method)(instance)
        self.assertEquals(calls, expectedCalls)
        mapper.Dispose()


    def testDispatchDelete(self):
        calls = []
        class MockMapper(object):
            def CheckBridgePtrs(self):
                calls.append(('CheckBridgePtrs',))
            def DecRef(self, ptr):
                calls.append(('DecRef', ptr))
            def Unmap(self, ptr):
                calls.append(('Unmap', ptr))
        
        expectedCalls = [
            ('CheckBridgePtrs',),
            ('DecRef', INSTANCE_PTR),
            ('Unmap', INSTANCE_PTR),
        ]
        self.assertDispatchDelete(MockMapper(), calls, expectedCalls)


    def testDispatchDontDelete(self):
        calls = []
        class MockMapper(object):
            def CheckBridgePtrs(self):
                calls.append(('CheckBridgePtrs',))
            def DecRef(self, ptr):
                calls.append(('DecRef', ptr))
            def Unmap(self, ptr):
                calls.append(('Unmap', ptr))
        
        self.assertDispatchDelete(MockMapper(), calls, [], method='dontDelete')
        

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
    DispatcherSsizeargTest,
    DispatcherSsizeobjargTest,
    DispatcherSsizessizeargTest,
    DispatcherSsizessizeobjargTest,
    DispatcherObjobjargTest,
    DispatcherInquiryTest,
    DispatcherTernaryTest,
    DispatcherRichcmpTest,
    DispatcherLenfuncTest,
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
