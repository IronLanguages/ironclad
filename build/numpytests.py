
from itertools import takewhile
import os
import os.path
import sys
import ironclad
import numpy
from numpy.testing import TestCase
from unittest import TestResult

def read_into_blacklist(blacklist, filename):
    f = file(filename)
    try:
        for line in f:
            line = line.split('#')[0].strip()
            blacklist.append(line)
    finally:
        f.close()

numpy_path = r"C:\Python25\Lib\site-packages\numpy"
dirs = ['core', 'lib', 'linalg', 'ma', 'oldnumeric', 'random']

mod_blacklist = [
    'core.test_defchararray', 
    'core.test_memmap',
    'core.test_records',
]
class_blacklist = [
    'core.test_multiarray.TestStringCompare', # don't care about strings yet
    'core.test_multiarray.TestPickling', # don't care about pickling yet
    'core.test_multiarray.TestRecord', # record arrays
    'core.test_regression.TestRegression', # has too many errors to worry about now.
]
test_blacklist = [
    'core.test_defmatrix.TestCtor.test_basic', # uses getframe
    'core.test_defmatrix.TestCtor.test_bmat_nondefault_str', # uses getframe
    'core.test_multiarray.TestAttributes.test_fill', # seems to intermittently kill the test run
    'core.test_multiarray.TestFromToFile.test_file', # meant to be disabled on windows
    'core.test_multiarray.TestTake.test_record_array', # record arrays
    'core.test_multiarray.TestMethods.test_sort_order', # record arrays involved
    'core.test_multiarray.TestPutmask.test_record_array', # record arrays involved
    'core.test_multiarray.TestClip.test_record_array', # record arrays again
    'core.test_multiarray.TestResize.test_check_reference', # reference counting different in ironclad

    # might want to extract other test cases:
    'core.test_multiarray.TestMethods.test_sort', # fails on the creation of character arrays which we aren't worrying about 
    'core.test_multiarray.TestMethods.test_argsort', # fails on the creation of character arrays which we aren't worrying about

    # Fail due to differences in str(complex) between python and ipy - not worth fixing now (similar test in functionality test)
    'core.test_print.TestPrint.test_longdouble',
    'core.test_print.TestPrint.test_complex_double', 
    'core.test_print.TestPrint.test_complex_float', 
    'core.test_print.TestPrint.test_complex_longdouble',

    'core.test_scalarmath.TestRepr.test_float_repr', # takes a long time to run (may just be a large test)
    'core.test_scalarmath.TestTypes.test_type_add', # takes a long time to run (may just be a large test)
]
read_into_blacklist(test_blacklist, 'numpy_test_blacklist')


def import_test_module(direc, mod_name):
    full_name = 'numpy.%s.tests.%s' % (direc, mod_name)
    package = __import__(full_name)
    return reduce(getattr, [direc, 'tests', mod_name], package)


def run_single_test(package_name, mod_name, class_name, test_name, runner=None):
    module = import_test_module(package_name, mod_name)
    klass = getattr(module, class_name)
    test_path = (package_name, mod_name, class_name, test_name)
    runner(klass(test_name), test_path)


def blacklist_on_fail(test_case, test_path):
    print '.'.join(test_path)
    catastrophe = False
    try:
        result = TestResult()
        test_case.run(result)
    except:
        catastrophe = True
    if catastrophe or result.errors or result.failures:
        add_to_blacklist(test_path)
        print ".".join(test_path), " failed - adding to blacklist and stopping"
        ironclad.shutdown()
        sys.exit(1)
    else:
        save_continuation_point(test_path)



def run_test_case(test_case, test_path):
    try:
        print '.'.join(test_path), '...   ',
        save_continuation_point(test_path)
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


def get_modules(package_name):
    tests_path = os.path.join(numpy_path, package_name, 'tests')
    for filename in sorted(os.listdir(tests_path)):
        if not filename.endswith('.py') or not filename.startswith('test'):
            continue
        mod_name = filename[:-3]
        if '.'.join((package_name, mod_name)) in mod_blacklist:
            continue
        module = import_test_module(package_name, mod_name)
        yield mod_name, module


def get_classes(module, mod_path):
    for class_name, test_class in sorted(module.__dict__.items()):
        if not isinstance(test_class, type) or not issubclass(test_class, TestCase):
           continue
        if '.'.join(mod_path + (class_name,)) in class_blacklist:
            continue
        yield class_name, test_class


def get_test_names(test_class, class_path):
    tests = []
    for test_name, _ in sorted(test_class.__dict__.items()):
        if not test_name.startswith('test_') or '.'.join(class_path +(test_name,)) in test_blacklist:
            continue    
        tests.append(test_name)
    return tests


def get_all_tests(dirs, previous_test=None):
    for package_name in dirs: 
        ensure_package(package_name)
        for mod_name, module in get_modules(package_name):
            for class_name, test_class in get_classes(module, (package_name, mod_name)):
                for test_name in get_test_names(test_class, (package_name, mod_name, class_name)):
                    test_path = (package_name, mod_name, class_name, test_name)
                    yield test_path, test_class(test_name)


def run_all_tests(dirs, runner, previous_test=None):
    all_tests = get_all_tests(dirs)
    if previous_test:
        for _ in takewhile(lambda (p, _): p != previous_test, all_tests): pass
    for test_path, test_case in all_tests:
        runner(test_case, test_path)
    print "All tests run ?!"


def add_to_blacklist(test_path, msg=""):
    f = file('numpy_test_blacklist', 'a')
    try:
        if msg:
            msg = " # " + msg
        f.write(".".join(test_path) + msg + "\n")
    finally:
        f.close()


def save_continuation_point(test_path):
    f = file('numpy_continuation', 'w')
    try:
        if test_path:
            f.write('.'.join(test_path))
    finally:
        f.close()
        

def get_continuation_point():
    if not os.path.isfile('numpy_continuation'):
        return None
    f = file('numpy_continuation')
    try:
        name = f.read().strip()
        if name:
            return tuple(name.split('.'))
        return None
    finally:
        f.close()


def main():
    args = sys.argv[1:]
    runner = run_test_case
    previous_test = None
    if '--blacklist-add' in args:
        args.remove('--blacklist-add')
        runner = blacklist_on_fail
    if '--continue' in args:
        args.remove('--continue')
        previous_test = get_continuation_point()
        print "Continuation point", previous_test
    
    if not args:
        run_all_tests(dirs, runner, previous_test=previous_test)
    else:
        for test_path in args:
            package_name, mod_name, class_name, test_name = test_path.split('.')
            run_single_test(package_name, mod_name, class_name, test_name, runner=runner)
    

if __name__ == "__main__":
    main()

ironclad.shutdown()    

