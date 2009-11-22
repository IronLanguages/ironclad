
from tools.utils.codegen import CodeGenerator
from tools.utils.delegatesgen import DelegatesGenerator
from tools.utils.dispatchergen import DispatcherGenerator
from tools.utils.magicmethodsgen import MagicMethodsGenerator
from tools.utils.pythonapigen import PythonApiGenerator
from tools.utils.pythonstructsgen import PythonStructsGenerator

#==========================================================================

def _merge_dicts(d1, d2):
    return dict(d1, **d2)


#==========================================================================

class _ApiPlumbingContext(object):

    def __init__(self):
        self.dgt_specs = set()
        self.dispatcher_methods = {}


#==========================================================================

class ApiPlumbingGenerator(CodeGenerator):

    SUBGEN_ORDER = (
        PythonStructsGenerator, # no deps
        PythonApiGenerator,     # no deps
        DispatcherGenerator,    # no deps
        MagicMethodsGenerator,  # requires Dispatcher
        DelegatesGenerator,     # requires Dispatcher, PythonApi
    )
    
    INPUTS = ' '.join([G.INPUTS for G in SUBGEN_ORDER])

    def __init__(self, context=None):
        CodeGenerator.__init__(self, context or _ApiPlumbingContext())
        self.subgens = [C(self.context) for C in self.SUBGEN_ORDER]

    def run(self, inputs):
        run = lambda g: g.run(inputs)
        return reduce(_merge_dicts, map(run, self.subgens), {})


#==========================================================================
