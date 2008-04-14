
import unittest
from tests.utils.memory import CreateTypes
from tests.utils.runtest import makesuite, run

from IronPython.Hosting import PythonEngine
from Ironclad import Python25Mapper


class Python25Mapper_Types_Test(unittest.TestCase):
    
    def testTypeMappings(self):
        types = {
            "PyBaseObject_Type": object,
            "PyString_Type": str,
            "PyList_Type": list,
            "PyTuple_Type": tuple,
            "PyFile_Type": file,
        }
        
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        
        try:
            for (k, v) in types.items():
                self.assertEquals(mapper.Retrieve(getattr(mapper, k)), v, "failed to map " + k)
        finally:
            deallocTypes()
    
    
    def testPyType_IsSubtype(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)
        deallocTypes = CreateTypes(mapper)
        
        try:
            self.assertTrue(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyBaseObject_Type), "wrong")
            self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyList_Type), "wrong")
            
            self.assertFalse(mapper.PyType_IsSubtype(mapper.PyBaseObject_Type, mapper.PyList_Type), "wrong")
            self.assertTrue(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyBaseObject_Type), "wrong")
            
            self.assertFalse(mapper.PyType_IsSubtype(mapper.PyString_Type, mapper.PyList_Type), "wrong")
            self.assertFalse(mapper.PyType_IsSubtype(mapper.PyList_Type, mapper.PyString_Type), "wrong")
            
        finally:
            deallocTypes()
        
        


suite = makesuite(
    Python25Mapper_Types_Test,
)

if __name__ == '__main__':
    run(suite)