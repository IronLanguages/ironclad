""" A 'temporary' replacement for nose."""

from itertools import chain, takewhile
import os
import sys
import types
from unittest import TestCase, TestResult

class Schnoz(object):
    def __init__(self, name, lib_path, data_dir):
        self.dirname = []
        self.name = name
        self.path = lib_path
        self.blacklist_path = os.path.join(data_dir, '%s_test_blacklist' % name)
        self.continuation_path = os.path.join(data_dir, '%s_continuation' % name)
        self.test_blacklist = []
        self.read_into_blacklist(self.test_blacklist, self.blacklist_path)


    def import_test_module(self, direc, mod_name):
        full_name = '%s.%s.tests.%s' % (self.name, direc, mod_name)
        package = __import__(full_name)
        return reduce(getattr, [direc, 'tests', mod_name], package)


    def read_into_blacklist(self, blacklist, filename):
        if not os.path.isfile(filename):
            return
        f = file(filename)
        try:
            for line in f:
                line = line.split('#')[0].strip()
                if not line:
                    continue
                blacklist.append(line)
        finally:
            f.close()


    def run_single_test(self, test_path, runner=None):
        package_name, mod_name, class_name, test_name = test_path
        module = import_test_module(package_name, mod_name)
        klass = getattr(module, class_name)
        test_path = (package_name, mod_name, class_name, test_name)
        if not runner(klass(test_name), test_path):
            ironclad.shutdown()
            sys.exit(1)


    def blacklist_on_fail(self, test_case, test_path):
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
            self.save_continuation_point(test_path)


    def run_test_case(self, test_case, test_path):
        print '.'.join(test_path), '...   ',
        self.save_continuation_point(test_path)
        try:
            result = TestResult()
            test_case.run(result)
            if result.errors:
                print result.errors[0][1]
                return False
            elif result.failures:
                print result.failures[0][1]
                return False
            else:
                print 'OK'
                return True
        except Exception, e:
            print str(e)
            return False
    

    def ensure_package(self, package_name):
        tests_path = os.path.join(self.path, package_name, 'tests')
        init_path = os.path.join(tests_path, '__init__.py')
        open(init_path, 'w').close()


    def get_modules(self, package_name):
        tests_path = os.path.join(self.path, package_name, 'tests')
        for filename in sorted(os.listdir(tests_path)):
            if not filename.endswith('.py') or not filename.startswith('test'):
                continue
            mod_name = filename[:-3]
            if '.'.join((package_name, mod_name)) in self.test_blacklist:
                continue
            module = self.import_test_module(package_name, mod_name)
            yield mod_name, module


    def get_classes(self, module, mod_path):
        for class_name, test_class in sorted(module.__dict__.items()):
            if not isinstance(test_class, (type, types.ClassType)) or not issubclass(test_class, TestCase):
                continue
            if '.'.join(mod_path + (class_name,)) in self.test_blacklist:
                continue
            yield class_name, test_class


    def get_test_names(self, test_class, class_path):
        tests = []
        for cls in (test_class,) + test_class.__bases__: 
            for test_name in dir(cls):
                if not test_name.startswith('test_') or '.'.join(class_path +(test_name,)) in self.test_blacklist:
                    continue    
                tests.append(test_name)
        return sorted(tests)


    def get_all_tests(self):
        return self.get_matching_tests(())

    def get_matching_tests(self, path):
        package_names, mod_names, class_names, input_test_names = (tuple([comp] for comp in path) + ([], [], [], []))[0:4]
        for package_name in package_names or self.dirs:
            self.ensure_package(package_name)
            
            mod_pairs = [(name, import_test_module(package_name, name)) for name in mod_names]
            mod_pairs = mod_pairs or self.get_modules(package_name)
    
            for mod_name, module in mod_pairs:
                class_pairs = [(name, getattr(module, name)) for name in class_names]
                class_pairs = class_pairs or self.get_classes(module, (package_name, mod_name))
                    
                for class_name, test_class in class_pairs:
                    test_names = input_test_names or self.get_test_names(test_class, (package_name, mod_name, class_name))
    
                    for test_name in test_names:
                        test_path = (package_name, mod_name, class_name, test_name)
                        
                        pair = test_path, test_class(test_name)
                        yield pair


    def run_all_tests(self, runner, previous_test=None):
        all_tests = self.get_all_tests()
        if previous_test:
            for _ in takewhile(lambda (p, _): p != previous_test, all_tests):
                pass
        run_count = 0
        pass_count = 0
        for test_path, test_case in all_tests:
            run_count += 1
            if runner(test_case, test_path):
                pass_count += 1
        print "run complete; %d/%d passes" % (pass_count, run_count)


    def run_paths(self, paths, runner, previous_test=None):
        success = True
        for path in paths:
            all_tests = get_matching_tests(path)
            if previous_test:
                for _ in takewhile(lambda (p, _): p != previous_test, all_tests):
                    pass
    
            for test_path, test in all_tests:
                result = runner(test, test_path)
                success = success and result
        if not success:
            ironclad.shutdown()
            sys.exit(1)

        
    def add_to_blacklist(self, test_path, msg=""):
        f = file(self.blacklist_path, 'a')
        try:
            if msg:
                msg = " # " + msg
            f.write(".".join(test_path) + msg + "\n")
        finally:
            f.close()
    
    
    def save_continuation_point(self, test_path):
        f = file(self.continuation_path, 'w')
        try:
            if test_path:
                f.write('.'.join(test_path))
        finally:
            f.close()
            
    
    def get_continuation_point(self):
        if not os.path.isfile(self.continuation_path):
            return None
        f = file(self.continuation_path)
        try:
            name = f.read().strip()
            if name:
                return tuple(name.split('.'))
            return None
        finally:
            f.close()
    
    def main(self, dirs):
        self.dirs = dirs
        args = sys.argv[1:]
        runner = self.run_test_case
        previous_test = None
        if '--blacklist-add' in args:
            args.remove('--blacklist-add')
            runner = self.blacklist_on_fail
        if '--continue' in args:
            args.remove('--continue')
            previous_test = get_continuation_point()
            print "Continuation point", previous_test
        
        if not args:
            self.run_all_tests(runner, previous_test=previous_test)
        else:
            paths = (path_string.split('.') for path_string in args)
            run_paths(paths, runner, previous_test=previous_test)
    
