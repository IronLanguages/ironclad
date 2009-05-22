""" A 'temporary' replacement for nose."""

from itertools import chain, takewhile
import os
import sys
import types
from unittest import TestCase, TestSuite, TextTestRunner

class Schnoz(object):
    def __init__(self, name, lib_path, data_dir):
        self.dirname = []
        self.name = name
        self.path = lib_path
        blacklist_path = os.path.join(data_dir, '%s_test_blacklist' % name)
        self.read_blacklist(blacklist_path)


    def read_blacklist(self, filename):
        self.test_blacklist = []
        if not os.path.isfile(filename):
            return
        f = file(filename)
        try:
            for line in f:
                line = line.split('#')[0].strip()
                if not line:
                    continue
                self.test_blacklist.append(line)
        finally:
            f.close()
    

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


    def import_test_module(self, direc, mod_name):
        full_name = '%s.%s.tests.%s' % (self.name, direc, mod_name)
        package = __import__(full_name)
        return reduce(getattr, [direc, 'tests', mod_name], package)


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
        

    def get_matching_tests(self, path):
        package_names, mod_names, class_names, input_test_names = (tuple([comp] for comp in path) + ([], [], [], []))[0:4]
        for package_name in package_names:
            self.ensure_package(package_name)
            
            mod_pairs = [(name, self.import_test_module(package_name, name)) for name in mod_names]
            mod_pairs = mod_pairs or self.get_modules(package_name)
    
            for mod_name, module in mod_pairs:
                class_pairs = [(name, getattr(module, name)) for name in class_names]
                class_pairs = class_pairs or self.get_classes(module, (package_name, mod_name))
                    
                for class_name, test_class in class_pairs:
                    test_names = input_test_names or self.get_test_names(test_class, (package_name, mod_name, class_name))
    
                    for test_name in test_names:
                        yield test_class(test_name)
                        

    def main(self, paths=None, verbosity=1):
        args = sys.argv[1:] or paths or ()
        paths = (path_string.split('.') for path_string in args)
        
        suite = TestSuite()
        for path in paths:
            for test in self.get_matching_tests(path):
                suite.addTest(test)
        TextTestRunner(verbosity=verbosity).run(suite)
