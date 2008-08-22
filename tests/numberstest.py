
import operator

from tests.utils.runtest import makesuite, run

from tests.utils.memory import CreateTypes
from tests.utils.testcase import TestCase

from System import Int64, IntPtr, UInt32, UInt64
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyIntObject, PyFloatObject


class PyBool_Test(TestCase):
    
    def testTrueFalse(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
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
        
        mapper.Dispose()
        deallocTypes()


    def testPyBool_FromLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        truePtr = mapper.PyBool_FromLong(23151)
        self.assertEquals(truePtr, mapper._Py_TrueStruct)
        self.assertEquals(mapper.RefCount(truePtr), 2)
        
        falsePtr = mapper.PyBool_FromLong(0)
        self.assertEquals(falsePtr, mapper._Py_ZeroStruct)
        self.assertEquals(mapper.RefCount(falsePtr), 2)
        
        mapper.Dispose()
        deallocTypes()


class PyInt_Test(TestCase):

    def testStoreInt(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyIntObject, "ob_type"), mapper.PyInt_Type)
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyIntObject, "ob_ival"), value)
            mapper.DecRef(ptr)
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyInt_FromLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyIntObject, "ob_type"), mapper.PyInt_Type)
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyIntObject, "ob_ival"), value)
            mapper.DecRef(ptr)
                
        mapper.Dispose()
        deallocTypes()
    
    def testPyInt_FromSsize_t(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromSsize_t(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyIntObject, "ob_type"), mapper.PyInt_Type)
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyIntObject, "ob_ival"), value)
            mapper.DecRef(ptr)
                
        mapper.Dispose()
        deallocTypes()


    def testPyInt_AsLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.PyInt_FromLong(value)
            self.assertEquals(mapper.PyInt_AsLong(ptr), value, "failed to map back")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyInt_Type, "bad type")
                
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyInt_AsLong_StrangeType(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class NotInt(object):
            def __int__(self):
                return 12345
        
        ptr = mapper.Store(NotInt())
        self.assertEquals(mapper.PyInt_AsLong(ptr), 12345, "failed to map back")
                
        mapper.Dispose()
        deallocTypes()
        
    

class PyLong_Test(TestCase):

    def testStoreLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (5555555555, -5555555555, long(0)):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
            mapper.DecRef(ptr)
                
        mapper.Dispose()
        deallocTypes()
    
    def testPyLong_FromLongLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in map(Int64, (5555555555, -5555555555, 0)):
            ptr = mapper.PyLong_FromLongLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
                
        mapper.Dispose()
        deallocTypes()
    
    def testPyLong_FromUnsignedLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in map(UInt32, (4000000000, 0)):
            ptr = mapper.PyLong_FromUnsignedLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
                
        mapper.Dispose()
        deallocTypes()
    
    def testPyLong_FromUnsignedLongLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in map(UInt64, (18000000000000000000, 0)):
            ptr = mapper.PyLong_FromUnsignedLongLong(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyObject, "ob_type"), mapper.PyLong_Type, "bad type")
                
        mapper.Dispose()
        deallocTypes()


    def testPyLong_AsLongLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0, 9223372036854775807, -9223372036854775808):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyLong_AsLongLong(ptr), value)
        
        for value in (9223372036854775808, -9223372036854775809):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyLong_AsLongLong(ptr), 0)
            
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(OverflowError, KindaConvertError)
                
        mapper.Dispose()
        deallocTypes()


    def testPyLong_AsLong(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0, 2147483647, -2147483648):
            ptr = mapper.Store(long(value))
            self.assertEquals(mapper.PyLong_AsLong(ptr), value)
        
        for value in (2147483648, -2147483649):
            ptr = mapper.Store(long(value))
            self.assertEquals(mapper.PyLong_AsLong(ptr), 0)
            
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(OverflowError, KindaConvertError)
                
        mapper.Dispose()
        deallocTypes()


class PyFloat_Test(TestCase):

    def testStoreFloat(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyFloatObject, "ob_refcnt"), 1)
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyFloatObject, "ob_type"), mapper.PyFloat_Type)
            self.assertEquals(CPyMarshal.ReadDoubleField(ptr, PyFloatObject, "ob_fval"), value)
            mapper.DecRef(ptr)
                
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyFloat_FromDouble(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.PyFloat_FromDouble(value)
            self.assertEquals(mapper.Retrieve(ptr), value, "stored/retrieved wrong")
            self.assertEquals(CPyMarshal.ReadIntField(ptr, PyFloatObject, "ob_refcnt"), 1)
            self.assertEquals(CPyMarshal.ReadPtrField(ptr, PyFloatObject, "ob_type"), mapper.PyFloat_Type)
            self.assertEquals(CPyMarshal.ReadDoubleField(ptr, PyFloatObject, "ob_fval"), value)
            mapper.DecRef(ptr)
                
        mapper.Dispose()
        deallocTypes()


    def testPyFloat_AsDouble(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for value in (0.0, 3.3e33, -3.3e-33):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyFloat_AsDouble(ptr), value, "stored/retrieved wrong")
            mapper.DecRef(ptr)
        
        for value in ("cheese", object, object()):
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyFloat_AsDouble(ptr), -1, "did not return expected 'error' value")
            
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
            
            mapper.DecRef(ptr)
            
        mapper.Dispose()
        deallocTypes()
        


class PyNumber_Test(TestCase):
    
    def assertUnaryOp(self, cpyName, ipyFunc):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        values = [-1, 4, -3.5, (1, 2), [3, 4], set([-1]), 'hullo', object(), object]
        for value in values:
            error = None
            try:
                result = ipyFunc(value)
            except Exception, e:
                error = e.__class__
            valuePtr = mapper.Store(value)
            resultPtr = getattr(mapper, cpyName)(valuePtr)
            
            if error:
                self.assertEquals(resultPtr, IntPtr.Zero)
                def KindaConvertError():
                    raise mapper.LastException
                self.assertRaises(error, KindaConvertError)
            else:
                self.assertEquals(mapper.Retrieve(resultPtr), result)
                mapper.DecRef(resultPtr)
            
            mapper.DecRef(valuePtr)
                
        mapper.Dispose()
        deallocTypes()
    
    def assertBinaryOp(self, cpyName, ipyFunc):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        values = [-1, 4, -3.5, (1, 2), [3, 4], set([-1]), 'hullo', object(), object]
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
                resultPtr = getattr(mapper, cpyName)(iptr, jptr)
                
                if error:
                    self.assertEquals(resultPtr, IntPtr.Zero)
                    def KindaConvertError():
                        raise mapper.LastException
                    self.assertRaises(error, KindaConvertError)
                else:
                    self.assertEquals(mapper.Retrieve(resultPtr), result)
                    mapper.DecRef(resultPtr)
                
                mapper.DecRef(iptr)
                mapper.DecRef(jptr)
                
        mapper.Dispose()
        deallocTypes()
    
    def testPyNumber_Absolute(self):
        self.assertUnaryOp("PyNumber_Absolute", abs)
    
    def testPyNumber_Add(self):
        self.assertBinaryOp("PyNumber_Add", lambda a, b: a + b)
    
    def testPyNumber_Subtract(self):
        self.assertBinaryOp("PyNumber_Subtract", lambda a, b: a - b)
    
    def testPyNumber_Multiply(self):
        self.assertBinaryOp("PyNumber_Multiply", lambda a, b: a * b)
    
    def testPyNumber_Divide(self):
        self.assertBinaryOp("PyNumber_Divide", operator.div)
    
    def testPyNumber_TrueDivide(self):
        self.assertBinaryOp("PyNumber_TrueDivide", operator.truediv)
    
    def testPyNumber_FloorDivide(self):
        self.assertBinaryOp("PyNumber_FloorDivide", operator.floordiv)
    
    
    def testPyNumber_Long(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        values = [0, 12345, 123456789012345, 123.45]
        values += map(float, values)
        for value in values:
            ptr = mapper.Store(value)
            _long = mapper.Retrieve(mapper.PyNumber_Long(ptr))
            self.assertEquals(_long, long(value), "converted wrong")
            mapper.DecRef(ptr)
        
        badvalues = ['foo', object, object()]
        for value in badvalues:
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyNumber_Long(ptr), IntPtr.Zero)
            
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
            
            mapper.DecRef(ptr)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyNumber_Float(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        values = [0, 12345, 123456789012345, 123.45]
        values += map(float, values)
        for value in values:
            ptr = mapper.Store(value)
            _float = mapper.Retrieve(mapper.PyNumber_Float(ptr))
            self.assertEquals(_float, float(value), "converted wrong")
            mapper.DecRef(ptr)
        
        badvalues = ['foo', object, object()]
        for value in badvalues:
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyNumber_Float(ptr), IntPtr.Zero)
            
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
            
            mapper.DecRef(ptr)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyNumber_Int(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        values = [0, 12345, 123456789012345, 123.45]
        values += map(float, values)
        for value in values:
            ptr = mapper.Store(value)
            _int = mapper.Retrieve(mapper.PyNumber_Int(ptr))
            self.assertEquals(_int, int(value), "converted wrong")
            mapper.DecRef(ptr)
        
        badvalues = ['foo', object, object()]
        for value in badvalues:
            ptr = mapper.Store(value)
            self.assertEquals(mapper.PyNumber_Int(ptr), IntPtr.Zero)
            
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
            
            mapper.DecRef(ptr)
        
        mapper.Dispose()
        deallocTypes()
        
    

suite = makesuite(
    PyBool_Test,
    PyInt_Test,
    PyLong_Test,
    PyFloat_Test,
    PyNumber_Test,
)

if __name__ == '__main__':
    run(suite)