
import os
import os.path
import ironclad
import numpy
from numpy.testing import TestCase
from unittest import TestResult

numpy_path = r"C:\Python25\Lib\site-packages\numpy"
dirs = ['core']

mod_blacklist = ['test_defchararray', 'test_memmap']
class_blacklist = [
    'test_multiarray.TestStringCompare', # don't care about strings yet
    'test_multiarray.TestPickling', # don't care about pickling yet
    'test_multiarray.TestClip', # seems to cause problems
    'test_multiarray.TestRecord', # record arrays
]
test_blacklist = [
    'test_multiarray.TestTake.test_wrap', # hangs
    'test_multiarray.TestTake.test_record_array', # record arrays
    'test_defmatrix.TestCtor.test_basic', # uses getframe
    'test_defmatrix.TestCtor.test_bmat_nondefault_str', # uses getframe
    'test_multiarray.TestMethods.test_sort_order', # record arrays involved
    'test_multiarray.TestPutmask.test_record_array', # record arrays involved
]


for direc in dirs: 
    tests_path = os.path.join(numpy_path, direc, 'tests')
    init_path = os.path.join(tests_path, '__init__.py')
    open(init_path, 'w').close()
    
    for filename in os.listdir(tests_path):
        if not filename.endswith('.py') or not filename.startswith('test'):
            continue
        mod_name = filename[:-3]
        full_name = 'numpy.%s.tests.%s' % (direc, mod_name)
        
        if mod_name in mod_blacklist:
            continue
        
        package = __import__(full_name)
        module = reduce(lambda a, name: getattr(a, name), [direc, 'tests', mod_name], package)
        
        for class_name, test_class in module.__dict__.items():
            if not isinstance(test_class, type) or not issubclass(test_class, TestCase):
               continue
            if '.'.join([mod_name, class_name]) in class_blacklist:
                continue
               
            for test_name, _ in sorted(test_class.__dict__.items()):
                if not test_name.startswith('test_') or '.'.join([mod_name, class_name, test_name]) in test_blacklist:
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
        
        
 
    
        
        
    