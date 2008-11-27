
from tests.utils.runtest import makesuite, run
    
from tests.utils.cpython import MakeGetSetDef, MakeMethodDef, MakeNumSeqMapMethods, MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes
from tests.utils.python25mapper import MakeAndAddEmptyModule
from tests.utils.testcase import TestCase, WithMapper

import System
from System import IntPtr, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import (
    CPyMarshal, CPython_destructor_Delegate, CPython_initproc_Delegate, HGlobalAllocator,
    Python25Api, Python25Mapper
)
from Ironclad.Structs import (
    MemberT, METH, Py_TPFLAGS, PyMemberDef, PyNumberMethods, 
    PyIntObject, PyObject, PyMappingMethods, PySequenceMethods, PyTypeObject
)

class BorkedException(System.Exception):
    pass


ARG1_PTR = IntPtr(111)
ARG2_PTR = IntPtr(222)
ARG3_PTR = IntPtr(333)
ARG1_SSIZE = 111111
ARG2_SSIZE = 222222
RESULT_PTR = IntPtr(999)
RESULT_INT = 999
RESULT_SSIZE = 999999

class DispatchSetupTestCase(TestCase):

    @WithMapper
    def assertTypeSpec(self, typeSpec, TestType, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)
        
        _type = mapper.Retrieve(typePtr)
        TestType(_type, mapper)

    def getUnaryFunc(self, result):
        calls = []
        def Unary(arg1):
            calls.append((arg1,))
            return result
        return Unary, calls
    
    def getBinaryFunc(self, result):
        calls = []
        def Binary(arg1, arg2):
            calls.append((arg1, arg2))
            return result
        return Binary, calls
    
    def getTernaryFunc(self, result):
        calls = []
        def Ternary(arg1, arg2, arg3):
            calls.append((arg1, arg2, arg3))
            return result
        return Ternary, calls

    def getQuaternaryFunc(self, result):
        calls = []
        def Quaternary(arg1, arg2, arg3, arg4):
            calls.append((arg1, arg2, arg3, arg4))
            return result
        return Quaternary, calls
        
    def getNaryFunc(self, result):
        calls = []
        def Nary(*args, **kwargs):
            calls.append((args, kwargs))
            return result
        return Nary, calls
        

    def getUnaryPtrFunc(self):
        return self.getUnaryFunc(RESULT_PTR)

    def getBinaryPtrFunc(self):
        return self.getBinaryFunc(RESULT_PTR)

    def getTernaryPtrFunc(self):
        return self.getTernaryFunc(RESULT_PTR)

    def assertCalls(self, dgt, args, calls, expect_args, result):
        args, kwargs = args
        self.assertEquals(calls, [])
        self.assertEquals(dgt(*args, **kwargs), result)
        self.assertEquals(calls, [expect_args])
    
    def assertCallsUnaryPtrFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR,), {}), calls, (ARG1_PTR,), RESULT_PTR)
    
    def assertCallsBinaryPtrFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG2_PTR), {}), calls, (ARG1_PTR, ARG2_PTR), RESULT_PTR)
    
    def assertCallsTernaryPtrFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG2_PTR, ARG3_PTR), {}), calls, (ARG1_PTR, ARG2_PTR, ARG3_PTR), RESULT_PTR)
    
    def assertCallsSsizeargPtrFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG1_SSIZE), {}), calls, (ARG1_PTR, ARG1_SSIZE), RESULT_PTR)
    
    def assertCallsSsizessizeargPtrFunc(self, dgt, calls):
        self.assertCalls(dgt, ((ARG1_PTR, ARG1_SSIZE, ARG2_SSIZE), {}), calls, (ARG1_PTR, ARG1_SSIZE, ARG2_SSIZE), RESULT_PTR)


class MethodsTest(DispatchSetupTestCase):

    def assertAddTypeObject_withSingleMethod(self, methodDef, TestType):
        typeSpec = {
            "tp_name": "klass",
            "tp_methods": [methodDef]
        }
        self.assertTypeSpec(typeSpec, TestType)


    @WithMapper
    def testSpecialNames(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": "klass"})
        addToCleanUp(deallocType)
        _type = mapper.Retrieve(typePtr)
        self.assertEquals(_type.__new__.__name__, '__new__')
        self.assertEquals(_type.__init__.__name__, '__init__')
        self.assertEquals(_type.__del__.__name__, '__del__')
        


    def testNoArgsMethod(self):
        NoArgs, calls_cfunc = self.getBinaryPtrFunc()
        method, deallocMethod = MakeMethodDef("method", NoArgs, METH.NOARGS)
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_noargs = dispatch
            
            self.assertEquals(instance.method.__name__, "method")
            self.assertCalls(
                instance.method, (tuple(), {}), calls_dispatch, 
                ("klass.method", instance), result)

            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsBinaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


    def testObjArgMethod(self):
        ObjArg, calls_cfunc = self.getBinaryPtrFunc()
        method, deallocMethod = MakeMethodDef("method", ObjArg, METH.O)
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), object()
            _type._dispatcher.method_objarg = dispatch
            self.assertEquals(instance.method.__name__, "method")
            self.assertCalls(
                instance.method, ((arg,), {}), calls_dispatch, 
                ("klass.method", instance, arg), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsBinaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


    def testVarargsMethod(self):
        VarArgs, calls_cfunc = self.getBinaryPtrFunc()
        method, deallocMethod = MakeMethodDef("method", VarArgs, METH.VARARGS)
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, args = _type(), ("for", "the", "horde")
            _type._dispatcher.method_varargs = dispatch
            
            self.assertEquals(instance.method.__name__, "method")
            self.assertCalls(
                instance.method, (args, {}), calls_dispatch, 
                (("klass.method", instance) + args, {}), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsBinaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()
        

    def testVarargsKwargsMethod(self):
        Kwargs, calls_cfunc = self.getTernaryPtrFunc()
        method, deallocMethod = MakeMethodDef("method", Kwargs, METH.VARARGS | METH.KEYWORDS)
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, args, kwargs = _type(), ("for", "the", "horde"), {"g1": "LM", "g2": "BS", "g3": "GM"}
            _type._dispatcher.method_kwargs = dispatch
            self.assertEquals(instance.method.__name__, "method")
            self.assertCalls(
                instance.method, (args, kwargs), calls_dispatch,
                (("klass.method", instance) + args, kwargs), result)
            
            cfunc = _type._dispatcher.table["klass.method"]
            self.assertCallsTernaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertAddTypeObject_withSingleMethod(method, TestType)
        deallocMethod()


class StrReprTest(DispatchSetupTestCase):
    
    def assertReprfunc(self, cpyName, ipyName):
        reprfunc, calls_cfunc = self.getUnaryPtrFunc()
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_selfarg = dispatch
            self.assertCalls(
                getattr(instance, ipyName), (tuple(), {}), calls_dispatch,
                ("klass." + ipyName, instance), result)
            
            cfunc = _type._dispatcher.table["klass." + ipyName]
            self.assertCallsUnaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()

        typeSpec = {
            "tp_name": "klass",
            cpyName: reprfunc,
        }
        self.assertTypeSpec(typeSpec, TestType)
    
    def testStr(self):
        self.assertReprfunc("tp_str", "__str__")
    
    def testRepr(self):
        self.assertReprfunc("tp_repr", "__repr__")
        


class CallTest(DispatchSetupTestCase):
    
    def testCall(self):
        Call, calls_cfunc = self.getTernaryPtrFunc()
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, args, kwargs = _type(), ("for", "the", "horde"), {"g1": "LM", "g2": "BS", "g3": "GM"}
            _type._dispatcher.method_kwargs = dispatch
            self.assertCalls(
                instance, (args, kwargs), calls_dispatch,
                (("klass.__call__", instance) + args, kwargs), result)
            
            cfunc = _type._dispatcher.table["klass.__call__"]
            self.assertCallsTernaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()

        typeSpec = {
            "tp_name": "klass",
            "tp_call": Call,
        }
        self.assertTypeSpec(typeSpec, TestType)


class IterTest(DispatchSetupTestCase):

    def assertSelfTypeMethod(self, typeFlags, keyName, expectedMethodName, TestErrorHandler):
        func, calls_cfunc = self.getUnaryPtrFunc()
        typeSpec = {
            "tp_name": "klass",
            keyName: func,
            "tp_flags": typeFlags
        }
        
        def TestType(_type, mapper):
            result = object()
            calls_dispatch = []
            def dispatch(methodName, selfPtr, errorHandler=None):
                calls_dispatch.append((methodName, selfPtr))
                TestErrorHandler(errorHandler, mapper)
                return result
                
            instance = _type()
            _type._dispatcher.method_selfarg = dispatch
            self.assertEquals(getattr(instance, expectedMethodName)(), result, "bad return")
            self.assertEquals(calls_dispatch, [("klass." + keyName, instance)])
            
            cfunc = _type._dispatcher.table["klass." + keyName]
            self.assertCallsUnaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
        
        self.assertTypeSpec(typeSpec, TestType)


    def test_tp_iter_MethodDispatch(self):
        def TestErrorHandler(errorHandler, _):
            self.assertEquals(errorHandler, None, "no special error handling required")

        self.assertSelfTypeMethod(
            Py_TPFLAGS.HAVE_ITER, "tp_iter", "__iter__", TestErrorHandler)


    def test_tp_iternext_MethodDispatch(self):
        def TestErrorHandler(errorHandler, mapper): 
            errorHandler(IntPtr(12345))
            self.assertRaises(StopIteration, errorHandler, IntPtr.Zero)
            mapper.LastException = ValueError()
            errorHandler(IntPtr.Zero)
        
        self.assertSelfTypeMethod(
            Py_TPFLAGS.HAVE_ITER, "tp_iternext", "next", TestErrorHandler)
        

class RichCompareTest(DispatchSetupTestCase):
    
    def testRichCompare(self):
        func, calls_cfunc = self.getTernaryPtrFunc()
        typeSpec = {
            "tp_name": "klass",
            "tp_richcompare": func,
        }
        result = object()
        dispatch, calls_dispatch = self.getQuaternaryFunc(result)

        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_richcmp = dispatch
            
            magic = {
                "__lt__": 0,
                "__le__": 1,
                "__eq__": 2,
                "__ne__": 3,
                "__gt__": 4,
                "__ge__": 5,
            }
            for (methodname, magicnumber) in magic.items():
                del calls_cfunc[:]
                del calls_dispatch[:]
                comparee = object()
                self.assertCalls(
                    getattr(instance, methodname), ((comparee,), {}), calls_dispatch, 
                    ("klass.tp_richcompare", instance, comparee, magicnumber), result)
            
            cfunc = _type._dispatcher.table["klass.tp_richcompare"]
            self.assertCalls(
                cfunc, ((ARG1_PTR, ARG2_PTR, ARG1_SSIZE,), {}), calls_cfunc, 
                (ARG1_PTR, ARG2_PTR, ARG1_SSIZE,), RESULT_PTR)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)


class HashTest(DispatchSetupTestCase):
    
    def testHash(self):
        func, calls_cfunc = self.getUnaryFunc(RESULT_INT)
        typeSpec = {
            "tp_name": "klass",
            "tp_hash": func
        }
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_hashfunc = dispatch
            self.assertCalls(
                instance.__hash__, (tuple(), {}), calls_dispatch, 
                ("klass.__hash__", instance), result)
            
            cfunc = _type._dispatcher.table["klass.__hash__"]
            self.assertCalls(
                cfunc, ((ARG1_PTR,), {}), calls_cfunc, (ARG1_PTR,), RESULT_INT)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)


class CompareTest(DispatchSetupTestCase):
    
    def testCmp(self):
        func, calls_cfunc = self.getBinaryFunc(RESULT_INT)
        typeSpec = {
            "tp_name": "klass",
            "tp_compare": func
        }
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), object()
            _type._dispatcher.method_cmpfunc = dispatch
            self.assertCalls(
                instance.__cmp__, ((arg,), {}), calls_dispatch, 
                ("klass.__cmp__", instance, arg), result)
            
            cfunc = _type._dispatcher.table["klass.__cmp__"]
            self.assertCalls(
                cfunc, ((ARG1_PTR, ARG2_PTR), {}), calls_cfunc, (ARG1_PTR, ARG2_PTR), RESULT_INT)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)


class NumberTest(DispatchSetupTestCase):
    
    def assertUnaryNumberMethod(self, slotName, methodName):
        func, calls_cfunc = self.getUnaryPtrFunc()
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {slotName: func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_selfarg = dispatch
            self.assertCalls(
                getattr(instance, methodName), (tuple(), {}), calls_dispatch, 
                ("klass." + methodName, instance), result)
            
            cfunc = _type._dispatcher.table["klass." + methodName]
            self.assertCallsUnaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()
    
    def assertBinaryNumberMethod(self, slotName, methodName, swappedMethodName=None):
        func, calls_cfunc = self.getBinaryPtrFunc()
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {slotName: func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), object()
            _type._dispatcher.method_objarg = dispatch
            self.assertCalls(
                getattr(instance, methodName), ((arg,), {}), calls_dispatch, 
                ("klass." + methodName, instance, arg), result)
                
            if swappedMethodName:
                del calls_dispatch[:]
                _type._dispatcher.method_objarg = dispatch
                self.assertCalls(
                    getattr(instance, swappedMethodName), ((arg,), {}), calls_dispatch, 
                    ("klass." + swappedMethodName, arg, instance), result)
                    
            cfunc = _type._dispatcher.table["klass." + methodName]
            self.assertCallsBinaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()

    def testNegative(self):
        self.assertUnaryNumberMethod("nb_negative", "__neg__")

    def testPositive(self):
        self.assertUnaryNumberMethod("nb_positive", "__pos__")

    def testAbs(self):
        self.assertUnaryNumberMethod("nb_absolute", "__abs__")

    def testInvert(self):
        self.assertUnaryNumberMethod("nb_invert", "__invert__")

    def testInt(self):
        self.assertUnaryNumberMethod("nb_int", "__int__")

    def testLong(self):
        self.assertUnaryNumberMethod("nb_long", "__long__")

    def testFloat(self):
        self.assertUnaryNumberMethod("nb_float", "__float__")

    def testOct(self):
        self.assertUnaryNumberMethod("nb_oct", "__oct__")

    def testHex(self):
        self.assertUnaryNumberMethod("nb_hex", "__hex__")

    def testIndex(self):
        self.assertUnaryNumberMethod("nb_index", "__index__")

    def testAdd(self):
        self.assertBinaryNumberMethod("nb_add", "__add__", "__radd__")

    def testSubtract(self):
        self.assertBinaryNumberMethod("nb_subtract", "__sub__", "__rsub__")

    def testMultiply(self):
        self.assertBinaryNumberMethod("nb_multiply", "__mul__", "__rmul__")

    def testDivide(self):
        self.assertBinaryNumberMethod("nb_divide", "__div__", "__rdiv__")

    def testTrueDivide(self):
        self.assertBinaryNumberMethod("nb_true_divide", "__truediv__", "__rtruediv__")

    def testFloorDivide(self):
        self.assertBinaryNumberMethod("nb_floor_divide", "__floordiv__", "__rfloordiv__")

    def testRemainder(self):
        self.assertBinaryNumberMethod("nb_remainder", "__mod__", "__rmod__")

    def testDivmod(self):
        self.assertBinaryNumberMethod("nb_divmod", "__divmod__", "__rdivmod__")

    def testLshift(self):
        self.assertBinaryNumberMethod("nb_lshift", "__lshift__", "__rlshift__")

    def testRshift(self):
        self.assertBinaryNumberMethod("nb_rshift", "__rshift__", "__rrshift__")

    def testAnd(self):
        self.assertBinaryNumberMethod("nb_and", "__and__", "__rand__")

    def testXor(self):
        self.assertBinaryNumberMethod("nb_xor", "__xor__", "__rxor__")

    def testOr(self):
        self.assertBinaryNumberMethod("nb_or", "__or__", "__ror__")

    def testInplaceAdd(self):
        self.assertBinaryNumberMethod("nb_inplace_add", "__iadd__")

    def testInplaceSubtract(self):
        self.assertBinaryNumberMethod("nb_inplace_subtract", "__isub__")

    def testInplaceMultiply(self):
        self.assertBinaryNumberMethod("nb_inplace_multiply", "__imul__")

    def testInplaceDivide(self):
        self.assertBinaryNumberMethod("nb_inplace_divide", "__idiv__")

    def testInplaceTrueDivide(self):
        self.assertBinaryNumberMethod("nb_inplace_true_divide", "__itruediv__")

    def testInplaceFloorDivide(self):
        self.assertBinaryNumberMethod("nb_inplace_floor_divide", "__ifloordiv__")

    def testInplaceRemainder(self):
        self.assertBinaryNumberMethod("nb_inplace_remainder", "__imod__")

    def testInplaceLshift(self):
        self.assertBinaryNumberMethod("nb_inplace_lshift", "__ilshift__")

    def testInplaceRshift(self):
        self.assertBinaryNumberMethod("nb_inplace_rshift", "__irshift__")

    def testInplaceAnd(self):
        self.assertBinaryNumberMethod("nb_inplace_and", "__iand__")

    def testInplaceXor(self):
        self.assertBinaryNumberMethod("nb_inplace_xor", "__ixor__")

    def testInplaceOr(self):
        self.assertBinaryNumberMethod("nb_inplace_or", "__ior__")
    
    def testPower(self):
        func, calls_cfunc = self.getTernaryPtrFunc()
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {'nb_power': func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getQuaternaryFunc(result)
        # handling swapped args with modulus is 'too complex'. phew.
        dispatch_swapped, calls_dispatch_swapped = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg1, arg2 = _type(), object(), object()
            _type._dispatcher.method_ternary = dispatch
            self.assertCalls(
                instance.__pow__, ((arg1, arg2), {}), calls_dispatch, 
                ("klass.__pow__", instance, arg1, arg2), result)
                
            del calls_dispatch[:]
            self.assertCalls(
                lambda x, y: x ** y, ((instance, arg1), {}), calls_dispatch, 
                ("klass.__pow__", instance, arg1, None), result)
                
            _type._dispatcher.method_ternary_swapped = dispatch_swapped
            self.assertCalls(
                lambda x, y: y ** x, ((instance, arg1), {}), calls_dispatch_swapped, 
                ("klass.__rpow__", instance, arg1), result)
            
            cfunc = _type._dispatcher.table["klass.__pow__"]
            self.assertCallsTernaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()
    
    def testInplacePower(self):
        func, calls_cfunc = self.getTernaryPtrFunc()
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {'nb_inplace_power': func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getQuaternaryFunc(result)
        
        def TestType(_type, _):
            instance, arg1, arg2 = _type(), object(), object()
            _type._dispatcher.method_ternary = dispatch
            self.assertCalls(
                instance.__ipow__, ((arg1, arg2), {}), calls_dispatch, 
                ("klass.__ipow__", instance, arg1, arg2), result)
                
            del calls_dispatch[:]
            self.assertCalls(
                instance.__ipow__, ((arg1,), {}), calls_dispatch, 
                ("klass.__ipow__", instance, arg1, None), result)
            
            cfunc = _type._dispatcher.table["klass.__ipow__"]
            self.assertCallsTernaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()
    
    def testNonzero(self):
        func, calls_cfunc = self.getUnaryFunc(RESULT_INT)
        numbersPtr, deallocNumbers = MakeNumSeqMapMethods(PyNumberMethods, {'nb_nonzero': func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_number": numbersPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_inquiry = dispatch
            self.assertCalls(
                instance.__nonzero__, (tuple(), {}), calls_dispatch, 
                ("klass.__nonzero__", instance), result)
            
            cfunc = _type._dispatcher.table["klass.__nonzero__"]
            self.assertCalls(
                cfunc, ((ARG1_PTR,), {}), calls_cfunc, (ARG1_PTR,), RESULT_INT)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocNumbers()


class SequenceTest(DispatchSetupTestCase):
    
    def testItem(self):
        func, calls_cfunc = self.getBinaryPtrFunc()
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(PySequenceMethods, {"sq_item": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_sequence": sequencesPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), 123
            _type._dispatcher.method_ssizearg = dispatch
            self.assertCalls(
                instance.__getitem__, ((arg,), {}), calls_dispatch, 
                ("klass._getitem_sq_item", instance, arg), result)
            
            cfunc = _type._dispatcher.table["klass._getitem_sq_item"]
            self.assertCallsSsizeargPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
    
    
    def testSetItem(self):
        func, calls_cfunc = self.getTernaryFunc(RESULT_INT)
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(PySequenceMethods, {"sq_ass_item": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_sequence": sequencesPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getQuaternaryFunc(result)
        
        def TestType(_type, _):
            instance, arg1, arg2 = _type(), 123, object()
            _type._dispatcher.method_ssizeobjarg = dispatch
            self.assertCalls(
                instance.__setitem__, ((arg1, arg2), {}), calls_dispatch, 
                ("klass._setitem_sq_ass_item", instance, arg1, arg2), result)
            
            cfunc = _type._dispatcher.table["klass._setitem_sq_ass_item"]
            self.assertCalls(
                cfunc, ((ARG1_PTR, ARG1_SSIZE, ARG2_PTR), {}), calls_cfunc, 
                (ARG1_PTR, ARG1_SSIZE, ARG2_PTR), RESULT_INT)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
    
    
    def testSimpleSlice(self):
        func, calls_cfunc = self.getTernaryPtrFunc()
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(PySequenceMethods, {"sq_slice": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_sequence": sequencesPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getQuaternaryFunc(result)
        
        def TestType(_type, _):
            instance, arg1, arg2 = _type(), 123, 456
            _type._dispatcher.method_ssizessizearg = dispatch
            self.assertCalls(
                getattr(instance, "__getslice__"), ((arg1, arg2), {}), calls_dispatch, 
                ("klass.__getslice__", instance, arg1, arg2), result)
            
            cfunc = _type._dispatcher.table["klass.__getslice__"]
            self.assertCallsSsizessizeargPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
    
    
    def testSetSimpleSlice(self):
        func, calls_cfunc = self.getQuaternaryFunc(RESULT_INT)
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(PySequenceMethods, {"sq_ass_slice": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_sequence": sequencesPtr
        }
        result = object()
        dispatch, calls_dispatch = self.getNaryFunc(result)
        
        def TestType(_type, _):
            instance, arg1, arg2, arg3 = _type(), 123, 456, object()
            _type._dispatcher.method_ssizessizeobjarg = dispatch
            self.assertCalls(
                instance.__setslice__, ((arg1, arg2, arg3), {}), calls_dispatch, 
                (("klass.__setslice__", instance, arg1, arg2, arg3), {}), result)
            
            cfunc = _type._dispatcher.table["klass.__setslice__"]
            self.assertCalls(
                cfunc, ((ARG1_PTR, ARG1_SSIZE, ARG2_SSIZE, ARG2_PTR), {}), calls_cfunc, 
                (ARG1_PTR, ARG1_SSIZE, ARG2_SSIZE, ARG2_PTR), RESULT_INT)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
    
    
    def testLen(self):
        lenfunc, calls_cfunc = self.getUnaryFunc(RESULT_SSIZE)
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(PySequenceMethods, {"sq_length": lenfunc})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_sequence": sequencesPtr,
        }
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_lenfunc = dispatch
            self.assertCalls(
                instance.__len__, (tuple(), {}), calls_dispatch,
                ("klass._len_sq_length", instance), result)
            
            cfunc = _type._dispatcher.table["klass._len_sq_length"]
            self.assertCalls(
                cfunc, ((ARG1_PTR,), {}), calls_cfunc, (ARG1_PTR,), RESULT_SSIZE)
            
            del instance
            gcwait()

        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()


class MappingTest(DispatchSetupTestCase):
    
    def testItem(self):
        func, calls_cfunc = self.getBinaryPtrFunc()
        mappingPtr, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {"mp_subscript": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_mapping": mappingPtr,
        }
        result = object()
        dispatch, calls_dispatch = self.getTernaryFunc(result)
        
        def TestType(_type, _):
            instance, arg = _type(), object()
            _type._dispatcher.method_objarg = dispatch
            self.assertCalls(
                instance.__getitem__, ((arg,), {}), calls_dispatch, 
                ("klass._getitem_mp_subscript", instance, arg), result)
            
            cfunc = _type._dispatcher.table["klass._getitem_mp_subscript"]
            self.assertCallsBinaryPtrFunc(cfunc, calls_cfunc)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocMapping()
    
    
    def testSetItem(self):
        func, calls_cfunc = self.getTernaryFunc(RESULT_INT)
        mappingPtr, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {"mp_ass_subscript": func})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_mapping": mappingPtr,
        }
        result = object()
        dispatch, calls_dispatch = self.getQuaternaryFunc(result)
        
        def TestType(_type, _):
            instance, arg1, arg2 = _type(), object(), object()
            _type._dispatcher.method_objobjarg = dispatch
            self.assertCalls(
                instance.__setitem__, ((arg1, arg2), {}), calls_dispatch, 
                ("klass._setitem_mp_ass_subscript", instance, arg1, arg2), result)
            
            cfunc = _type._dispatcher.table["klass._setitem_mp_ass_subscript"]
            self.assertCalls(
                cfunc, ((ARG1_PTR, ARG2_PTR, ARG3_PTR), {}), calls_cfunc, 
                (ARG1_PTR, ARG2_PTR, ARG3_PTR), RESULT_INT)
            
            del instance
            gcwait()
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocMapping()
    
    
    def testLen(self):
        lenfunc, calls_cfunc = self.getUnaryFunc(RESULT_SSIZE)
        mappingPtr, deallocMapping = MakeNumSeqMapMethods(PyMappingMethods, {"mp_length": lenfunc})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_mapping": mappingPtr,
        }
        result = object()
        dispatch, calls_dispatch = self.getBinaryFunc(result)
        
        def TestType(_type, _):
            instance = _type()
            _type._dispatcher.method_lenfunc = dispatch
            self.assertCalls(
                instance.__len__, (tuple(), {}), calls_dispatch,
                ("klass._len_mp_length", instance), result)
            
            cfunc = _type._dispatcher.table["klass._len_mp_length"]
            self.assertCalls(
                cfunc, ((ARG1_PTR,), {}), calls_cfunc, (ARG1_PTR,), RESULT_SSIZE)
            
            del instance
            gcwait()

        self.assertTypeSpec(typeSpec, TestType)
        deallocMapping()


class SequenceMappingInteractionTest(DispatchSetupTestCase):
    
    def testAllSortsOfSubscriptingAtOnce(self):
        calls = []
        common_result_ptr = [IntPtr.Zero]
        
        def sq_item(instancePtr, i):
            calls.append(("sq_item", instancePtr, i))
            return common_result_ptr[0]
        
        def sq_slice(instancePtr, i, j):
            calls.append(("sq_slice", instancePtr, i, j))
            return common_result_ptr[0]
        
        def sq_length(_):
            # must be defined for slicing to work; don't care about calls tho
            return 10
        
        def mp_subscript(instancePtr, objPtr):
            calls.append(("mp_subscript", instancePtr, objPtr))
            return common_result_ptr[0]
            
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(
            PySequenceMethods, {"sq_slice": sq_slice, "sq_item": sq_item, "sq_length": sq_length})
        mappingPtr, deallocMapping = MakeNumSeqMapMethods(
            PyMappingMethods, {"mp_subscript": mp_subscript})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_mapping": mappingPtr,
            "tp_as_sequence": sequencesPtr,
        }
        
        def TestType(_type, mapper):
            instance = _type()
            instancePtr = mapper.Store(instance)
            common_result = object()
            common_result_ptr[0] = mapper.Store(common_result)
            map(mapper.IncRef, common_result_ptr * 3) # decreffed each time it's returned
            
            self.assertEquals(instance[1], common_result)
            self.assertEquals(calls, [("sq_item", instancePtr, 1)])
            del calls[:]
            
            self.assertEquals(instance[1:-3], common_result)
            self.assertEquals(calls, [("sq_slice", instancePtr, 1, 7)])
            del calls[:]
            
            self.assertEquals(instance[1:-3:3], common_result)
            self.assertEquals(len(calls), 1)
            self.assertEquals(calls[0][:-1], ("mp_subscript", instancePtr))
            del calls[:]
            
            self.assertEquals(instance[object()], common_result)
            self.assertEquals(len(calls), 1)
            self.assertEquals(calls[0][:-1], ("mp_subscript", instancePtr))
            del calls[:]
            
            del instance
        
        
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
        deallocMapping()
    
    
    def testAllSortsOfSubscriptAssignmentAtOnce(self):
        calls = []
        
        def sq_ass_item(instancePtr, i, objPtr):
            calls.append(("sq_ass_item", instancePtr, i, objPtr))
            return 0
        
        def sq_ass_slice(instancePtr, i, j, objPtr):
            calls.append(("sq_ass_slice", instancePtr, i, j, objPtr))
            return 0
        
        def sq_length(_):
            # must be defined for slicing to work; don't care about calls atm
            return 10
        
        def mp_ass_subscript(instancePtr, objPtr1, objPtr2):
            calls.append(("mp_ass_subscript", instancePtr, objPtr1, objPtr2))
            return 0
            
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(
            PySequenceMethods, {"sq_ass_slice": sq_ass_slice, "sq_ass_item": sq_ass_item, "sq_length": sq_length})
        mappingPtr, deallocMapping = MakeNumSeqMapMethods(
            PyMappingMethods, {"mp_ass_subscript": mp_ass_subscript})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_mapping": mappingPtr,
            "tp_as_sequence": sequencesPtr,
        }
        
        def TestType(_type, mapper):
            instance = _type()
            instancePtr = mapper.Store(instance)
            obj = object()
            objPtr = mapper.Store(obj)
            
            instance[1] = obj
            self.assertEquals(calls, [("sq_ass_item", instancePtr, 1, objPtr)])
            del calls[:]
            
            instance[1:-3] = obj
            self.assertEquals(calls, [("sq_ass_slice", instancePtr, 1, 7, objPtr)])
            del calls[:]
            
            instance[1:-3:3] = obj
            self.assertEquals(len(calls), 1)
            self.assertEquals(calls[0][:-2], ("mp_ass_subscript", instancePtr))
            self.assertEquals(calls[0][-1], objPtr)
            del calls[:]
            
            instance[object()] = obj
            self.assertEquals(len(calls), 1)
            self.assertEquals(calls[0][:-2], ("mp_ass_subscript", instancePtr))
            self.assertEquals(calls[0][-1], objPtr)
            del calls[:]
            del instance
        
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
        deallocMapping()

    
    def testPrefersSequenceLength(self):
        calls = []
        
        def sq_length(instancePtr):
            calls.append(("sq_length", instancePtr))
            return 123
        
        def mp_length(instancePtr):
            calls.append(("mp_length", instancePtr))
            return 456
            
        sequencesPtr, deallocSequences = MakeNumSeqMapMethods(
            PySequenceMethods, {"sq_length": sq_length})
        mappingPtr, deallocMapping = MakeNumSeqMapMethods(
            PyMappingMethods, {"mp_length": mp_length})
        typeSpec = {
            "tp_name": "klass",
            "tp_as_mapping": mappingPtr,
            "tp_as_sequence": sequencesPtr,
        }
        
        def TestType(_type, mapper):
            instance = _type()
            instancePtr = mapper.Store(instance)
            self.assertEquals(len(instance), 123)
            self.assertEquals(calls, [("sq_length", instancePtr)])
            
        self.assertTypeSpec(typeSpec, TestType)
        deallocSequences()
        deallocMapping()
        
        
class NewInitDelTest(TestCase):

    @WithMapper
    def testMethodTablePopulation(self, mapper, addToCleanUp):
        calls = []
        def test_tp_new(_, __, ___):
            calls.append("tp_new")
            return IntPtr(123)
        def test_tp_init(_, __, ___):
            calls.append("tp_init")
            return 0
        def test_tp_dealloc(_):
            calls.append("tp_dealloc")
            
        typeSpec = {
            "tp_name": "klass",
            "tp_new": test_tp_new,
            "tp_init": test_tp_init,
            "tp_dealloc": test_tp_dealloc,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        addToCleanUp(deallocType)
        
        table = _type._dispatcher.table
        table['klass.tp_new'](IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
        table['klass.tp_init'](IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(calls, ['tp_new', 'tp_init'])
        self.assertFalse(table.has_key('klass.tp_dealloc'), 
            "tp_dealloc should be called indirectly, by the final decref of an instance")


    def testDispatch(self):
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        def tp_dealloc(instancePtr_dealloc):
            calls.append("tp_dealloc")
            self.assertEquals(instancePtr_dealloc, instancePtr, "wrong instance")
            # finish the dealloc to avoid confusing mapper on shutdown
            mapper.PyObject_Free(instancePtr_dealloc)
            
        # creation methods should be patched out
        def Raise(msg):
            raise Exception(msg)
        typeSpec = {
            "tp_name": "klass",
            "tp_new": lambda _, __, ___: Raise("new unpatched"),
            "tp_init": lambda _, __, ___: Raise("init unpatched"),
            "tp_dealloc": tp_dealloc,
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        ARGS = (1, "two")
        KWARGS = {"three": 4}
        instancePtr = allocator.Alloc(Marshal.SizeOf(PyObject))
        CPyMarshal.WriteIntField(instancePtr, PyObject, 'ob_refcnt', 1)
        CPyMarshal.WritePtrField(instancePtr, PyObject, 'ob_type', typePtr)
        
        calls = []
        def tp_new_test(typePtr_new, argsPtr, kwargsPtr):
            calls.append("tp_new")
            self.assertEquals(typePtr_new, typePtr)
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS)
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS)
            return instancePtr
        
        def tp_init_test(instancePtr_init, argsPtr, kwargsPtr):
            calls.append("tp_init")
            self.assertEquals(instancePtr_init, instancePtr)
            self.assertEquals(mapper.Retrieve(argsPtr), ARGS)
            self.assertEquals(mapper.Retrieve(kwargsPtr), KWARGS)
            return 0
            
        _type._dispatcher.table['klass.tp_new'] = Python25Api.PyType_GenericNew_Delegate(tp_new_test)
        _type._dispatcher.table['klass.tp_init'] = CPython_initproc_Delegate(tp_init_test)
        
        instance = _type(*ARGS, **KWARGS)
        self.assertEquals(mapper.Store(instance), instancePtr)
        mapper.DecRef(instancePtr)
        self.assertEquals(calls, ['tp_new', 'tp_init'])
        
        for _ in range(50):
            mapper.CheckBridgePtrs()
        del instance
        gcwait()
        self.assertEquals(calls, ['tp_new', 'tp_init', 'tp_dealloc'])
        
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    @WithMapper
    def testObjectSurvives(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        addToCleanUp(deallocType)
        
        _type = mapper.Retrieve(typePtr)
        
        obj = _type()
        objref = WeakReference(obj, True)
        
        # for unmanaged code to mess with ob_refcnt, it must have been passed a reference
        # from managed code; this shouldn't happen without a Store (which will IncRef)
        objptr = mapper.Store(obj)
        self.assertEquals(mapper.RefCount(objptr), 2)
        CPyMarshal.WriteIntField(objptr, PyObject, 'ob_refcnt', 3)
        mapper.DecRef(objptr)
        
        # managed code forgets obj for a while, while unmanaged code still holds a reference
        del obj
        gcwait()
        self.assertEquals(objref.IsAlive, True, "object died before its time")
        self.assertEquals(mapper.Retrieve(objptr), objref.Target, "mapping broken")


    @WithMapper
    def testObjectDies(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass'})
        _type = mapper.Retrieve(typePtr)
        addToCleanUp(deallocType)
        
        obj = _type()
        objref = WeakReference(obj, True)
        
        # for unmanaged code to mess with ob_refcnt, it must have been passed a reference
        # from managed code; this shouldn't happen without a Store (which will IncRef)
        objptr = mapper.Store(obj)
        self.assertEquals(mapper.RefCount(objptr), 2)
        mapper.DecRef(objptr)
        
        # managed code forgets obj, no refs from unmanaged code
        del obj
        gcwait()
        gcwait()
        self.assertEquals(objref.IsAlive, False, "object didn't die")



class PropertiesTest(TestCase):
    
    def assertGetSet(self, attr, get, set, TestType, closure=IntPtr.Zero):
        doc = "take me to the airport, put me on a plane"
        getset, deallocGetset = MakeGetSetDef(attr, get, set, doc, closure)
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        typeSpec = {
            "tp_name": 'klass',
            "tp_getset": [getset],
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        self.assertEquals(getattr(_type, attr).__doc__, doc, "bad docstring")
        TestType(_type)
        
        deallocGetset()
        mapper.Dispose()
        deallocType()
        deallocTypes()
    
    
    def testGet(self):
        def get(_, __):
            self.fail("this should have been patched out in TestType")
        
        def TestType(_type):
            instance = _type()
            
            calls = []
            result = "see my loafers: former gophers"
            def Getter(name, instancePtr, closurePtr):
                calls.append(('Getter', (name, instancePtr, closurePtr)))
                return result
            _type._dispatcher.method_getter = Getter

            self.assertEquals(instance.boing, result, "bad result")
            self.assertEquals(calls, [('Getter', ('klass.__get_boing', instance, IntPtr.Zero))])
            
            try:
                # not using assertRaises because we can't del instance if it's referenced in nested scope
                instance.boing = 'splat'
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when setting get-only property")
            del instance
            gcwait()
        
        self.assertGetSet("boing", get, None, TestType)


    def testSet(self):
        def set(_, __, ___):
            self.fail("this should have been patched out in TestType")
        
        def TestType(_type):
            instance = _type()
            
            calls = []
            def Setter(name, instancePtr, value, closurePtr):
                calls.append(('Setter', (name, instancePtr, value, closurePtr)))
            _type._dispatcher.method_setter = Setter
            
            try:
                # not using assertRaises because we can't del instance if it's referenced in nested scope
                instance.splat
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when getting set-only property")
                
            value = "see my vest, see my vest, made from real gorilla chest"
            instance.splat = value
            self.assertEquals(calls, [('Setter', ('klass.__set_splat', instance, value, IntPtr.Zero))])
            del instance
            gcwait()
            
        self.assertGetSet("splat", None, set, TestType)
        

    def testClosure(self):
        def get(_, __):
            self.fail("this should have been patched out in TestType")
        def set(_, __, ___):
            self.fail("this should have been patched out in TestType")
        
        CLOSURE_PTR = IntPtr(12345)
        def TestType(_type):
            instance = _type()
            
            calls = []
            result = "They called me a PC thug!"
            def Getter(name, instancePtr, closurePtr):
                calls.append(('Getter', (name, instancePtr, closurePtr)))
                return result
            _type._dispatcher.method_getter = Getter
            
            def Setter(name, instancePtr, value, closurePtr):
                calls.append(('Setter', (name, instancePtr, value, closurePtr)))
            _type._dispatcher.method_setter = Setter
            
            self.assertEquals(instance.click, result, "wrong result")
            value = "I've been called a greasy thug too, and it never stops hurting."
            instance.click = value
            self.assertEquals(calls, 
                [('Getter', ('klass.__get_click', instance, CLOSURE_PTR)),
                 ('Setter', ('klass.__set_click', instance, value, CLOSURE_PTR))],
                "wrong calls")
                
            del instance
            gcwait()
            
        self.assertGetSet("click", get, set, TestType, CLOSURE_PTR)


OFFSET = 16

class MembersTest(TestCase):
    
    def assertMember(self, mapper, attr, memberType, offset, flags, TestType, basicsize=32):
        doc = "hurry hurry hurry, before I go insane"
        typeSpec = {
            "tp_name": 'klass',
            "tp_members": [PyMemberDef(attr, memberType, offset, flags, doc)],
            "tp_basicsize": basicsize
        }
        typePtr, deallocType = MakeTypePtr(mapper, typeSpec)
        _type = mapper.Retrieve(typePtr)
        
        self.assertEquals(getattr(_type, attr).__doc__, doc, "wrong docstring")
        TestType(mapper, _type)
        return deallocType
    
        
    @WithMapper
    def testReadOnlyMember(self, mapper, addToCleanUp):
        def TestType(mapper, _type):
            instance = _type()
            try:
                instance.boing = 54231
            except AttributeError:
                pass
            else:
                self.fail("Failed to raise AttributeError when setting get-only property")
            
            calls = []
            def Get(_instance, offset):
                calls.append(('Get', (_instance, offset)))
                return 12345
            _type._dispatcher.get_member_int = Get
            
            self.assertEquals(instance.boing, 12345)
            self.assertEquals(calls, [('Get', (instance, OFFSET))])
            del instance
            gcwait()
            
        deallocType = self.assertMember(mapper, 'boing', MemberT.INT, OFFSET, 1, TestType)
        addToCleanUp(deallocType)


    def getGetSetTypeTest(self, attr, suffix, offset, value, result):
        def TestType(mapper, _type):
            instance = _type()
            
            calls = []
            def Get(_instance, offset):
                calls.append(('Get', (_instance, offset)))
                return result
            def Set(_instance, offset, value):
                calls.append(('Set', (_instance, offset, value)))
            setattr(_type._dispatcher, 'get_member_' + suffix, Get)
            setattr(_type._dispatcher, 'set_member_' + suffix, Set)
                
            self.assertEquals(getattr(instance, attr), result)
            setattr(instance, attr, value)
            
            self.assertEquals(calls, [
                ('Get', (instance, offset)),
                ('Set', (instance, offset, value)),
            ])
            del instance
            gcwait()
        return TestType
    
    
    @WithMapper
    def assertTypeMember(self, name, value, result, mapper, addToCleanUp):
        attr = 'boing'
        TestType = self.getGetSetTypeTest(attr, name, OFFSET, value, result)
        addToCleanUp(self.assertMember(mapper, attr, getattr(MemberT, name.upper()), OFFSET, 0, TestType))

    def testReadWriteIntMember(self):
        self.assertTypeMember('int', 12345, 54321)
        
    def testReadWriteCharMember(self):
        self.assertTypeMember('char', 'x', 'y')
        
    def testReadWriteUbyteMember(self):
        self.assertTypeMember('ubyte', 0, 255)
        
    def testReadWriteObjectMember(self):
        self.assertTypeMember('object', object(), object())


class InheritanceTest(TestCase):
    
    @WithMapper
    def testBaseClass(self, mapper, addToCleanUp):
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        addToCleanUp(deallocBase)

        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr})
        addToCleanUp(deallocType)
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(issubclass(klass, mapper.Retrieve(basePtr)), True, "didn't notice klass's base class")
        self.assertEquals(mapper.RefCount(mapper.PyType_Type), 3, "types did not keep references to TypeType")
        self.assertEquals(mapper.RefCount(basePtr), 3, "subtype did not keep reference to base")
        self.assertEquals(mapper.RefCount(mapper.PyBaseObject_Type), 2, "base type did not keep reference to its base (even if it wasn't set explicitly)")
        self.assertEquals(CPyMarshal.ReadPtrField(basePtr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type")

    
    @WithMapper
    def testInheritsMethodTable(self, mapper, addToCleanUp):
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': basePtr})
        addToCleanUp(deallocType)

        klass = mapper.Retrieve(klassPtr)
        base = mapper.Retrieve(basePtr)
        for k, v in base._dispatcher.table.items():
            self.assertEquals(klass._dispatcher.table[k], v)

    
    @WithMapper
    def testMultipleBases(self, mapper, addToCleanUp):
        base1Ptr, deallocBase1 = MakeTypePtr(mapper, {'tp_name': 'base1', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        addToCleanUp(deallocBase1)

        base2Ptr, deallocBase2 = MakeTypePtr(mapper, {'tp_name': 'base2', 'ob_type': mapper.PyType_Type, 'tp_base': IntPtr.Zero})
        addToCleanUp(deallocBase2)

        bases = (mapper.Retrieve(base1Ptr,), mapper.Retrieve(base2Ptr))
        basesPtr = mapper.Store(bases)
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': base1Ptr, 'tp_bases': basesPtr})
        addToCleanUp(deallocType)
        
        klass = mapper.Retrieve(klassPtr)
        for base in bases:
            self.assertEquals(issubclass(klass, base), True)
        self.assertEquals(mapper.RefCount(base1Ptr), 5, "subtype did not keep reference to bases")
        self.assertEquals(mapper.RefCount(base2Ptr), 4, "subtype did not keep reference to bases")
        self.assertEquals(CPyMarshal.ReadPtrField(base1Ptr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type 1")
        self.assertEquals(CPyMarshal.ReadPtrField(base2Ptr, PyTypeObject, "tp_base"), mapper.PyBaseObject_Type, "failed to ready base type 2")
    
    
    @WithMapper
    def testInheritMethodTableFromMultipleBases(self, mapper, addToCleanUp):
        "probably won't work quite right with identically-named base classes"
        base1Ptr, deallocBase1 = MakeTypePtr(mapper, {'tp_name': 'base1', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase1)

        base2Ptr, deallocBase2 = MakeTypePtr(mapper, {'tp_name': 'base2', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase2)

        bases = (mapper.Retrieve(base1Ptr,), mapper.Retrieve(base2Ptr))
        basesPtr = mapper.Store(bases)

        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': mapper.PyType_Type, 'tp_base': base1Ptr, 'tp_bases': basesPtr})
        addToCleanUp(deallocType)
        klass = mapper.Retrieve(klassPtr)

        for base in bases:
            for k, v in base._dispatcher.table.items():
                self.assertEquals(klass._dispatcher.table[k], v)

    
    @WithMapper
    def testMultipleBasesIncludingBuiltin(self, mapper, addToCleanUp):
        basePtr, deallocBase = MakeTypePtr(mapper, {'tp_name': 'base', 'ob_type': mapper.PyType_Type})
        addToCleanUp(deallocBase)

        bases = (mapper.Retrieve(basePtr), int)
        basesPtr = mapper.Store(bases)
        typeSpec = {
            'tp_name': 'klass',
            'ob_type': mapper.PyType_Type,
            'tp_base': basePtr,
            'tp_bases': basesPtr
        }
        klassPtr, deallocType = MakeTypePtr(mapper, typeSpec)
        addToCleanUp(deallocType)

        klass = mapper.Retrieve(klassPtr)
        for base in bases:
            self.assertEquals(issubclass(klass, base), True)

        unknownInstancePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        addToCleanUp(lambda: Marshal.FreeHGlobal(unknownInstancePtr))

        CPyMarshal.WriteIntField(unknownInstancePtr, PyObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(unknownInstancePtr, PyObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(unknownInstancePtr, PyIntObject, "ob_ival", 123)
        unknownInstance = mapper.Retrieve(unknownInstancePtr)
        self.assertEquals(isinstance(unknownInstance, klass), True)

    
    def testMetaclass(self):
        # this allocator is necessary because metaclass.tp_dealloc will use the mapper's allocator
        # to dealloc klass, and will complain if it wasn't allocated in the first place. this is 
        # probably not going to work in the long term
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        metaclassPtr, deallocMC = MakeTypePtr(mapper, {'tp_name': 'metaclass'})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': metaclassPtr}, allocator)
        
        klass = mapper.Retrieve(klassPtr)
        self.assertEquals(type(klass), mapper.Retrieve(metaclassPtr), "didn't notice klass's type")
        
        mapper.Dispose()
        deallocType()
        deallocMC()
        deallocTypes()
    
    
    def testInheritMethodTableFromMetaclass(self):
        "probably won't work quite right with identically-named metaclass"
        # this allocator is necessary because metaclass.tp_dealloc will use the mapper's allocator
        # to dealloc klass, and will complain if it wasn't allocated in the first place. this is 
        # probably not going to work in the long term
        allocator = HGlobalAllocator()
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        metaclassPtr, deallocMC = MakeTypePtr(mapper, {'tp_name': 'metaclass'})
        klassPtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'klass', 'ob_type': metaclassPtr}, allocator)

        klass = mapper.Retrieve(klassPtr)
        metaclass = mapper.Retrieve(metaclassPtr)
        for k, v in metaclass._dispatcher.table.items():
            self.assertEquals(klass._dispatcher.table[k], v)

        mapper.Dispose()
        deallocType()
        deallocMC()
        deallocTypes()


class IntSubclassHorrorTest(TestCase):
    
    @WithMapper
    def testRetrievedIntsHaveCorrectValue(self, mapper, deallocLater):
        # this is the only way I can tell what the underlying 'int' value is
        # (as opposed to the value returned from __int__, which does not get called
        # when passed into __getslice__)
        calls = []
        class SequenceLike(object):
            def __getslice__(self, i, j):
                calls.append(('__getslice__', i, j))
                return []

        typeSpec = {
            'tp_name': 'klass',
            'tp_base': mapper.PyInt_Type,
            'tp_basicsize': Marshal.SizeOf(PyIntObject)
        }

        klassPtr, deallocType = MakeTypePtr(mapper, typeSpec)
        deallocLater(deallocType)
        
        _12Ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        deallocLater(lambda: Marshal.FreeHGlobal(_12Ptr))
        CPyMarshal.WriteIntField(_12Ptr, PyIntObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(_12Ptr, PyIntObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(_12Ptr, PyIntObject, "ob_ival", 12)
        
        _44Ptr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        deallocLater(lambda: Marshal.FreeHGlobal(_44Ptr))
        CPyMarshal.WriteIntField(_44Ptr, PyIntObject, "ob_refcnt", 1)
        CPyMarshal.WritePtrField(_44Ptr, PyIntObject, "ob_type", klassPtr)
        CPyMarshal.WriteIntField(_44Ptr, PyIntObject, "ob_ival", 44)
        
        SequenceLike()[mapper.Retrieve(_12Ptr):mapper.Retrieve(_44Ptr)]
        self.assertEquals(calls, [('__getslice__', 12, 44)])
        self.assertEquals(map(type, calls[0]), [str, int, int])


class TypeDictTest(TestCase):
    
    @WithMapper
    def testRetrieveAssignsDictTo_tp_dict(self, mapper, addToCleanUp):
        typePtr, deallocType = MakeTypePtr(mapper, {"tp_name": "klass"})
        addToCleanUp(deallocType)
        
        _type = mapper.Retrieve(typePtr)
        _typeDictPtr = CPyMarshal.ReadPtrField(typePtr, PyTypeObject, "tp_dict")
        self.assertEquals(mapper.Retrieve(_typeDictPtr), _type.__dict__)


suite = makesuite(
    MethodsTest,
    StrReprTest,
    CallTest,
    IterTest,
    RichCompareTest,
    HashTest,
    CompareTest,
    NumberTest,
    SequenceTest,
    MappingTest,
    SequenceMappingInteractionTest,
    NewInitDelTest,
    PropertiesTest,
    MembersTest,
    InheritanceTest,
    IntSubclassHorrorTest,
    TypeDictTest,
)
if __name__ == '__main__':
    run(suite)
