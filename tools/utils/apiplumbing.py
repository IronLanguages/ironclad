

class ApiPlumbingContext(object):

    def __init__(self):
        self.dgt_specs = set()
        self.dispatcher_methods = {}


#==========================================================================

class ApiPlumbingGenerator(object):

    RUN_INPUTS = ''

    @classmethod
    def output_name(cls):
        return cls.__name__[:-len('Generator')]

    def __init__(self, context):
        self.context = context

    def run(self, inputs):
        keys = self.RUN_INPUTS.split()
        args = [inputs[key] for key in keys]
        return self._run(*args)


#==========================================================================
# late imports for classes which depend on ApiPlumbingGenerator existing

from tools.utils.delegatesgen import DelegatesGenerator
from tools.utils.dispatchergen import DispatcherGenerator
from tools.utils.magicmethodsgen import MagicMethodsGenerator
from tools.utils.pythonapigen import PythonApiGenerator
from tools.utils.pythonstructsgen import PythonStructsGenerator

_acceptable_generator_order = (
    PythonStructsGenerator, # no deps
    PythonApiGenerator,     # no deps
    DispatcherGenerator,    # no deps
    MagicMethodsGenerator,  # requires Dispatcher
    DelegatesGenerator,     # requires Dispatcher, PythonApi
)

def generate_apiplumbing(inputs):
    context = ApiPlumbingContext()
    def _generate_file(generator_type):
        return generator_type.output_name(), generator_type(context).run(inputs)
    return map(_generate_file, _acceptable_generator_order)

