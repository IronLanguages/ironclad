
import unittest
import tests.utils.loadassemblies

from tests.utils.gc import gcwait


class TestCase(unittest.TestCase):
    
    def tearDown(self):
        gcwait()
        unittest.TestCase.tearDown(self)
        
        
    def assertMapperHasError(self, mapper, error):
        if error:
            self.assertNotEquals(mapper.LastException, None, "no error set on mapper")
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(error, KindaConvertError)
            mapper.LastException = None
        else:
            self.assertEquals(mapper.LastException, None)