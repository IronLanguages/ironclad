
import os
import os.path
import ironclad
import numpy
from numpy.testing import TestCase
from unittest import TestResult

numpy_path = r"C:\Python25\Lib\site-packages\numpy"
dirs = ['core']

blackList = ['test_mul', 'test_defchararray', 'test_memmap', 'TestPickling']


for direc in dirs: 
    tests_path = os.path.join(numpy_path, direc, 'tests')
    init_path = os.path.join(tests_path, '__init__.py')
    open(init_path, 'w').close()
    
    for filename in os.listdir(tests_path):
        if not filename.endswith('.py') or not filename.startswith('test'):
            continue
        mod_name = filename[:-3]
        full_name = 'numpy.%s.tests.%s' % (direc, mod_name)
        
        if mod_name in blackList:
            continue
        
        package = __import__(full_name)
        
        module = reduce(lambda a, name: getattr(a, name), [direc, 'tests', mod_name], package)
        
        for class_name, test_class in module.__dict__.items():
            if class_name in blackList:
                continue
            if not isinstance(test_class, type) or not issubclass(test_class, TestCase):
               continue
            for test_name, _ in sorted(test_class.__dict__.items()):
                
                if not test_name.startswith('test_') or test_name in blackList:
                    continue
                print "%s %s.%s.%s" % (direc, mod_name, class_name, test_name),
                try:
                    result = TestResult()
                    test_class(test_name).run(result)
                    if result.errors: print result.errors[0][1]
                    elif result.failures: print result.failures[0][1]
                    else: print 'OK'
                except Exception, e:
                    print str(e)

ironclad.shutdown()    
        
        
 
    
        
        
    