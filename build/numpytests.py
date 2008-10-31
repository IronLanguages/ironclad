
import os
import os.path
import sys
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


def import_test_module(direc, mod_name):
    full_name = 'numpy.%s.tests.%s' % (direc, mod_name)
    package = __import__(full_name)
    return reduce(getattr, [direc, 'tests', mod_name], package)


def run_single_test(package_name, mod_name, class_name, test_name):
    module = import_test_module(package_name, mod_name)
    klass = getattr(module, class_name)
    run_test_case(klass(test_name))


def run_test_case(test_case):
    try:
        result = TestResult()
        test_case.run(result)
        if result.errors: print result.errors[0][1]
        elif result.failures: print result.failures[0][1]
        else: print 'OK'
    except Exception, e:
        print str(e)


def ensure_package(package_name):
    tests_path = os.path.join(numpy_path, package_name, 'tests')
    init_path = os.path.join(tests_path, '__init__.py')
    open(init_path, 'w').close()    


def get_modules_dict(package_name):
    tests_path = os.path.join(numpy_path, package_name, 'tests')
    modules = {}
    for filename in os.listdir(tests_path):
        if not filename.endswith('.py') or not filename.startswith('test'):
            continue
        mod_name = filename[:-3]
        if mod_name in mod_blacklist:
            continue
        module = import_test_module(package_name, mod_name)
        modules[mod_name] = module
    return modules
    

def get_classes_dict(mod_name, module):
    classes = {}
    for class_name, test_class in module.__dict__.items():
        if not isinstance(test_class, type) or not issubclass(test_class, TestCase):
           continue
        if '.'.join([mod_name, class_name]) in class_blacklist:
            continue
        classes[class_name] = test_class
    return classes


def get_test_names(mod_name, class_name, test_class):
    tests = []
    for test_name, _ in sorted(test_class.__dict__.items()):
        if not test_name.startswith('test_') or '.'.join([mod_name, class_name, test_name]) in test_blacklist:
            continue    
        tests.append(test_name)
    return tests


def run_all_tests(dirs):
    for package_name in dirs: 
        ensure_package(package_name)
        for mod_name, module in get_modules_dict(package_name).items():
            for class_name, test_class in get_classes_dict(mod_name, module).items():
                for test_name in get_test_names(mod_name, class_name, test_class):
                    print "%s %s.%s.%s" % (package_name, mod_name, class_name, test_name),
                    run_test_case(test_class(test_name))


args = sys.argv[1:]
if not args:
    run_all_tests(dirs)
else:
    for test_path in args:
        package_name, mod_name, class_name, test_name = test_path.split('.')
        run_single_test(package_name, mod_name, class_name, test_name)

ironclad.shutdown()    

