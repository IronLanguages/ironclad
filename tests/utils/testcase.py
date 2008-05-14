
import unittest
import tests.utils.loadassemblies

from tests.utils.gc import gcwait


class TestCase(unittest.TestCase):
    
    def tearDown(self):
        gcwait()
        unittest.TestCase.tearDown(self)

