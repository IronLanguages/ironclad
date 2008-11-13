
import operator

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.numbers import NumberI, NumberL, NumberF, NUMBER_VALUE

from System import Int32, Int64, IntPtr, UInt32, UInt64
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPythonVarargsKwargsFunction_Delegate, Python25Mapper
from Ironclad.Structs import Py_complex, PyObject, PyIntObject, PyFloatObject, PyComplexObject, PyTypeObject
        

class PyBool_Test(TestCase):
    
    @WithMapper
    def testTrueFalse(self, mapper, _):
        truePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        mapper.SetData("_Py_TrueStruct", truePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(truePtr, PyIntObject, 'ob_type'), mapper.PyBool_Type)
        self.assertEquals(CPyMarshal.ReadIntField(truePtr, PyIntObject, 'ob_refcnt'), 1)
        self.assertEquals(CPyMarshal.ReadIntField(truePtr, PyIntObject, 'ob_ival'), 1)
        truePtr2 = mapper.Store(True)
        self.assertEquals(truePtr2, truePtr)
        self.assertEquals(mapper.RefCount(truePtr), 2)
        
        falsePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyIntObject))
        mapper.SetData("_Py_ZeroStruct", falsePtr)
        self.assertEquals(CPyMarshal.ReadPtrField(falsePtr, PyIntObject, 'ob_type'), mapper.PyBool_Type)
        self.assertEquals(CPyMarshal.ReadIntField(falsePtr, PyIntObject, 'ob_refcnt'), 1)
        self.assertEquals(CPyMarshal.ReadIntField(falsePtr, PyIntObject, 'ob_ival'), 0)
        falsePtr2 = mapper.Store(False)
        self.assertEquals(falsePtr2, falsePtr)
        self.assertEquals(mapper.RefCount(falsePtr), 2)


    @WithMapper
    def testPyBool_FromLong(self, mapper, _):
        truePtr = mapper.PyBool_FromLong(23151)
        self.assertEquals(truePtr, mapper._Py_TrueStruct)
        self.assertEquals(mapper.RefCount(truePtr), 2)
        
        falsePtr = mapper.PyBool_FromLong(0)
        self.assertEquals(falsePtr, mapper._Py_ZeroStruct)
        self.assertEquals(mapper.RefCount(falsePtr), 2)
        

class PyInt_Test(TestCase):

    @WithMapper
    def testStoreInt(self, mapper, _):
        for value in (0, Int32.MaxValue, Int32.MinValue):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyIntObject, "ob_type"), mapper.PyInt_Type)
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyIntObject, "ob_ival"), value)
            mapper.DecRef(ptr)
    
    
    @WithMapper
    def testPyInt_FromLong(self, mapper, _):
        for value in (0, Int32.MaxValue, Int32.MinValue):
            ptr = mapper.PyInt_FromLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyIntObject, "ob_type"), mapper.PyInt_Type)
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyIntObject, "ob_ival"), value)
            mapper.DecRef(ptr)
                
    
    @WithMapper
    def testPyInt_FromSsize_t(self, mapper, _):
        for value in (0, Int32.MaxValue, Int32.MinValue):
            ptr = mapper.PyInt_FromSsize_t(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyIntObject, "ob_type"), mapper.PyInt_Type)
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyIntObject, "ob_ival"), value)
            mapper.DecRef(ptr)


    @WithMapper
    def testPyInt_AsSsize_t(self, mapper, _):
        for value in (0, UInt32.MaxValue):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyInt_AsSsize_t(ptr), value, "failed to map back")
            self.assertMapperHasError(mapper, None)
            
        for (value, error) in ((UInt32.MaxValue + 1, OverflowError), (-1, OverflowError), (object(), TypeError)):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyInt_AsSsize_t(ptr), UInt32.MaxValue)
            self.assertMapperHasError(mapper, error)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyInt_AsSsize_t(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)
        
        
    @WithMapper
    def testPyInt_AsLong(self, mapper, _):
        for value in (0, Int32.MaxValue, Int32.MinValue):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyInt_AsLong(ptr), value, "failed to map back")
            self.assertMapperHasError(mapper, None)
            
        for (value, error) in ((Int32.MaxValue + 1, OverflowError), (Int32.MinValue - 1, OverflowError), (object(), TypeError)):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyInt_AsLong(ptr), -1)
            self.assertMapperHasError(mapper, error)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyInt_AsLong(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)

        
    @WithMapper
    def testPyInt_UnManagedNew(self, mapper, _):
        tp_new = CPyMarshal.ReadFunctionPtrField(mapper.PyInt_Type, PyTypeObject, "tp_new", CPythonVarargsKwargsFunction_Delegate)
        for value in (0, 1, -1, "17"):
            unmanaged_int = tp_new(mapper.PyInt_Type, mapper.Store((value,)), IntPtr.Zero)
            actualType = CPyMarshal.ReadPtrField(unmanaged_int, PyObject, "ob_type")
            self.assertEquals(actualType, mapper.PyInt_Type)
            self.assertEquals(mapper.Retrieve(unmanaged_int), int(value))
            
        for bad_value in ("hello", object(), object):
            unmanaged_int = tp_new(mapper.PyInt_Type, mapper.Store((bad_value,)), IntPtr.Zero)
            self.assertEquals(unmanaged_int, IntPtr.Zero)
            error = None
            try:
                int(bad_value)
            except Exception, e:
                error = type(e)
            self.assertMapperHasError(mapper, error)
    

class PyLong_Test(TestCase):

    @WithMapper
    def testStoreLong(self, mapper, _):
        for value in (5555555555, -5555555555, long(0)):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
            mapper.DecRef(ptr)
                
    
    @WithMapper
    def testPyLong_FromLongLong(self, mapper, _):
        for value in map(Int64, (5555555555, -5555555555, 0)):
            ptr = mapper.PyLong_FromLongLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
                
    
    @WithMapper
    def testPyLong_FromUnsignedLong(self, mapper, _):
        for value in map(UInt32, (4000000000, 0)):
            ptr = mapper.PyLong_FromUnsignedLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
                
                
    @WithMapper
    def testPyLong_FromUnsignedLongLong(self, mapper, _):
        for value in map(UInt64, (18000000000000000000, 0)):
            ptr = mapper.PyLong_FromUnsignedLongLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
                

    @WithMapper
    def testPyLong_AsLongLong(self, mapper, _):
        for value in (0, 9223372036854775807, -9223372036854775808):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyLong_AsLongLong(ptr), value)
        
        for value in (9223372036854775808, -9223372036854775809):
            ptr = mapper.Store(value)
            mapper.LastException = None
            self.assertEquals(mapper.PyLong_AsLongLong(ptr), -1)
            self.assertMapperHasError(mapper, OverflowError)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyLong_AsLongLong(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)
                

    @WithMapper
    def testPyLong_AsUnsignedLongLong(self, mapper, _):
        for value in (0, 2**64-1):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyLong_AsUnsignedLongLong(ptr), value)
            self.assertMapperHasError(mapper, None)
      
        ptr = mapper.Store(2**64)
        self.assertEquals(mapper.PyLong_AsUnsignedLongLong(ptr), UInt64.MaxValue)
        self.assertMapperHasError(mapper, OverflowError)
        
        ptr = mapper.Store(-1)
        self.assertEquals(mapper.PyLong_AsUnsignedLongLong(ptr), UInt64.MaxValue)
        self.assertMapperHasError(mapper, TypeError)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyLong_AsUnsignedLongLong(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)
                

    @WithMapper
    def testPyLong_AsLong(self, mapper, _):
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.Store(long(value))
            self.assertEquals(mapper.PyLong_AsLong(ptr), value)
        
        for value in (2147483648, -2147483649):
            ptr = mapper.Store(long(value))
            mapper.LastException = None
            self.assertEquals(mapper.PyLong_AsLong(ptr), -1)
            self.assertMapperHasError(mapper, OverflowError)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyLong_AsLong(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)
                

    @WithMapper
    def testPyLong_AsUnsignedLong(self, mapper, _):
        for value in (0, (2**31) + 1):
            ptr = mapper.Store(long(value))
            self.assertEquals(mapper.PyLong_AsUnsignedLong(ptr), value)
        
        for value in (-2, 2**33):
            ptr = mapper.Store(long(value))
            mapper.LastException = None
            self.assertEquals(mapper.PyLong_AsUnsignedLong(ptr), UInt32.MaxValue)
            self.assertMapperHasError(mapper, OverflowError)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyLong_AsUnsignedLong(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)


class PyFloat_Test(TestCase):

    @WithMapper
    def testStoreFloat(self, mapper, _):
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyFloatObject, "ob_refcnt"), 1)
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyFloatObject, "ob_type"), mapper.PyFloat_Type)
            self.assertEquals(CPyMarshal.ReadDoubleField(ptr, PyFloatObject, "ob_fval"), value)
            mapper.DecRef(ptr)
    

    @WithMapper    
    def testPyFloat_FromDouble(self, mapper, _):
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.PyFloat_FromDouble(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyFloatObject, "ob_refcnt"), 1)
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyFloatObject, "ob_type"), mapper.PyFloat_Type)
            self.assertEquals(CPyMarshal.ReadDoubleField(ptr, PyFloatObject, "ob_fval"), value)
            mapper.DecRef(ptr)


    @WithMapper
    def testPyFloat_AsDouble(self, mapper, _):
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyFloat_AsDouble(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)
        
        for value in ("cheese", object, object()):
            ptr = mapper.Store(value)
            mapper.LastException = None
            self.assertEquals(mapper.PyFloat_AsDouble(ptr), -1, "did not return expected 'error' value")
            self.assertMapperHasError(mapper, TypeError)
            mapper.DecRef(ptr)

        for cls in (NumberI, NumberL, NumberF):
            ptr = mapper.Store(cls())
            result = mapper.PyFloat_AsDouble(ptr)
            self.assertMapperHasError(mapper, None)
            self.assertEquals(result, NUMBER_VALUE)


    @WithMapper
    def testPyFloat_UnManagedNew(self, mapper, _):
        tp_new = CPyMarshal.ReadFunctionPtrField(mapper.PyFloat_Type, PyTypeObject, "tp_new", CPythonVarargsKwargsFunction_Delegate)
        for value in (0, 1, 1.5, "1.0"):
            unmanaged_float = tp_new(mapper.PyFloat_Type, mapper.Store((value,)), IntPtr.Zero)
            actualType = CPyMarshal.ReadPtrField(unmanaged_float, PyObject, "ob_type")
            self.assertEquals(actualType, mapper.PyFloat_Type)
            self.assertEquals(mapper.Retrieve(unmanaged_float), float(value))
            
        for bad_value in ("hello", object(), object):
            unmanaged_float = tp_new(mapper.PyFloat_Type, mapper.Store((bad_value,)), IntPtr.Zero)
            self.assertEquals(unmanaged_float, IntPtr.Zero)
            error = None
            try:
                float(bad_value)
            except Exception, e:
                error = type(e)
            self.assertMapperHasError(mapper, error)
            


class PyComplex_Test(TestCase):

    @WithMapper
    def testStoreFloat(self, mapper, _):
        for value in (0 + 0j, 1 + 3.3e33j, -3.3e-33 - 1j):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyComplexObject, "ob_refcnt"), 1)
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyComplexObject, "ob_type"), mapper.PyComplex_Type)
            self.assertEquals(CPyMarshal.ReadDoubleField(ptr, PyComplexObject, "real"), value.real)
            self.assertEquals(CPyMarshal.ReadDoubleField(ptr, PyComplexObject, "imag"), value.imag)
            mapper.DecRef(ptr)


    @WithMapper    
    def testPyComplex_AsCComplex(self, mapper, _):
        values = ((1.5, (1.5, 0.0, None)),
                  (3 + 4j, (3.0, 4.0, None)),
                  (27, (27.0, 0.0, None)),
                  (None, (-1.0, 0.0, TypeError)),
                  ('I am not a number! I am a free man!', (-1.0, 0, TypeError)))
        
        for (value, info) in values:
            Py_complex_ = mapper.PyComplex_AsCComplex(mapper.Store(value))
            real_, imag_, error = info
            self.assertEquals(Py_complex_.real, real_)
            self.assertEquals(Py_complex_.imag, imag_)
            self.assertMapperHasError(mapper, error)

 
    @WithMapper
    def testPyComplex_FromDoubles(self, mapper, _):
        self.assertEquals(mapper.Retrieve(mapper.PyComplex_FromDoubles(1, 2)), 1 + 2j)
        
        

class PyNumber_Test(TestCase):
    
    @WithMapper
    def assertUnaryOp(self, cpyName, ipyFunc, mapper, _):
        values = [-1, 4, 2, -3.5, (1, 2), [3, 4], set([-1]), 'hullo', object(), object]
        for value in values:
            error = None
            try:
                result = ipyFunc(value)
            except Exception, e:
                error = e.__class__
            valuePtr = mapper.Store(value)
            mapper.LastException = None
            resultPtr = getattr(mapper, cpyName)(valuePtr)
            
            if error:
                self.assertEquals(resultPtr, IntPtr.Zero)
                self.assertMapperHasError(mapper, error)
            else:
                self.assertEquals(mapper.Retrieve(resultPtr), result)
                mapper.DecRef(resultPtr)
            
            mapper.DecRef(valuePtr)
    
    
    @WithMapper
    def assertBinaryOp(self, cpyName, ipyFunc, mapper, _):
        values = [-1, 4, 2, -3.5, (1, 2), [3, 4], set([-1]), 'hullo', object(), object]
        count = len(values)
        for i in range(count):
            for j in range(count):
                error = None
                try:
                    result = ipyFunc(values[i], values[j])
                except Exception, e:
                    error = e.__class__
                iptr = mapper.Store(values[i])
                jptr = mapper.Store(values[j])
                mapper.LastException = None
                resultPtr = getattr(mapper, cpyName)(iptr, jptr)
                
                if error:
                    self.assertEquals(resultPtr, IntPtr.Zero)
                    self.assertMapperHasError(mapper, error)
                else:
                    self.assertEquals(mapper.Retrieve(resultPtr), result)
                    mapper.DecRef(resultPtr)
                
                mapper.DecRef(iptr)
                mapper.DecRef(jptr)
    
    
    def testPyNumber_Absolute(self):
        self.assertUnaryOp("PyNumber_Absolute", abs)
    
    def testPyNumber_Index(self):
        self.assertUnaryOp("PyNumber_Index", operator.index)
    
    def testPyNumber_Add(self):
        self.assertBinaryOp("PyNumber_Add", operator.add)
    
    def testPyNumber_Subtract(self):
        self.assertBinaryOp("PyNumber_Subtract", operator.sub)
    
    def testPyNumber_Multiply(self):
        self.assertBinaryOp("PyNumber_Multiply", operator.mul)
    
    def testPyNumber_Divide(self):
        self.assertBinaryOp("PyNumber_Divide", operator.div)
    
    def testPyNumber_TrueDivide(self):
        self.assertBinaryOp("PyNumber_TrueDivide", operator.truediv)
    
    def testPyNumber_FloorDivide(self):
        self.assertBinaryOp("PyNumber_FloorDivide", operator.floordiv)
    
    def testPyNumber_Remainder(self):
        self.assertBinaryOp("PyNumber_Remainder", operator.mod)
    
    def testPyNumber_Lshift(self):
        self.assertBinaryOp("PyNumber_Lshift", operator.lshift)
    
    def testPyNumber_Rshift(self):
        self.assertBinaryOp("PyNumber_Rshift", operator.rshift)
    
    def testPyNumber_And(self):
        self.assertBinaryOp("PyNumber_And", operator.and_)
    
    def testPyNumber_Or(self):
        self.assertBinaryOp("PyNumber_Or", operator.or_)
    
    def testPyNumber_Xor(self):
        self.assertBinaryOp("PyNumber_Xor", operator.xor)
    
    
    @WithMapper
    def testPyNumber_Check(self, mapper, _):
        class NumberLike(object):
            def __abs__(self):  
                return 99
        
        for number in (-1, 32.3, NumberLike(), 4+5j):
            ptr = mapper.Store(number)
            self.assertEquals(mapper.PyNumber_Check(ptr), 1)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
            
        for notnumber in ("foo", NumberLike, [1, 2, 3]):
            ptr = mapper.Store(notnumber)
            self.assertEquals(mapper.PyNumber_Check(ptr), 0)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
        
    
    @WithMapper
    def testPyNumber_Long(self, mapper, _):
        values = [0, 12345, 123456789012345, 123.45, '123']
        values += map(float, values)
        for value in values:
            ptr = mapper.Store(value)
            _long = mapper.Retrieve(mapper.PyNumber_Long(ptr))
            self.assertEquals(_long, long(value), "converted wrong")
            self.assertMapperHasError(mapper, None)
            mapper.DecRef(ptr)
        
        badvalues = ['foo', object, object(), '123.4']
        for value in badvalues:
            ptr = mapper.Store(value)
            mapper.LastException = None
            self.assertEquals(mapper.PyNumber_Long(ptr), IntPtr.Zero)
            
            error = None
            try:
                long(value)
            except Exception, e:
                error = type(e)
            self.assertMapperHasError(mapper, error)
            mapper.DecRef(ptr)
        
        # work around ipy bug
        self.assertEquals(mapper.PyNumber_Long(mapper.Store('')), IntPtr.Zero)
        self.assertMapperHasError(mapper, ValueError)
        
        self.assertEquals(mapper.PyNumber_Long(mapper.Store('   ')), IntPtr.Zero)
        self.assertMapperHasError(mapper, ValueError)
        
        
    
    @WithMapper
    def testPyNumber_Float(self, mapper, _):
        values = [0, 12345, 123456789012345, 123.45, "123.45"]
        values += map(float, values)
        for value in values:
            ptr = mapper.Store(value)
            _float = mapper.Retrieve(mapper.PyNumber_Float(ptr))
            self.assertEquals(_float, float(value), "converted wrong")
            self.assertMapperHasError(mapper, None)
            mapper.DecRef(ptr)
        
        badvalues = ['foo', object, object()]
        for value in badvalues:
            ptr = mapper.Store(value)
            mapper.LastException = None
            self.assertEquals(mapper.PyNumber_Float(ptr), IntPtr.Zero)
            
            error = None
            try:
                float(value)
            except Exception, e:
                error = type(e)
            self.assertMapperHasError(mapper, error)
            mapper.DecRef(ptr)
    
    
    @WithMapper
    def testPyNumber_Int(self, mapper, _):        
        values = [0, 12345, 123456789012345, 123.45, "123"]
        values += map(float, values)
        for value in values:
            ptr = mapper.Store(value)
            _int = mapper.Retrieve(mapper.PyNumber_Int(ptr))
            self.assertEquals(type(_int) in (int, long), True, "returned inappropriate type")
            self.assertEquals(_int, int(value), "converted wrong")
            self.assertMapperHasError(mapper, None)
            mapper.DecRef(ptr)
        
        badvalues = ['foo', object, object(), "123.45"]
        for value in badvalues:
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyNumber_Int(ptr), IntPtr.Zero)
            
            error = None
            try:
                int(value)
            except Exception, e:
                error = type(e)
            self.assertMapperHasError(mapper, error)
            mapper.DecRef(ptr)
        
    

suite = makesuite(
    PyBool_Test,
    PyInt_Test,
    PyLong_Test,
    PyFloat_Test,
    PyComplex_Test,
    PyNumber_Test,
)

if __name__ == '__main__':
    run(suite)
