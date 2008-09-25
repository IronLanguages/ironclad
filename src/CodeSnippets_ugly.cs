namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string FIX_CPyMarshal_RuntimeType_CODE = @"
CPyMarshal = CPyMarshal() # eww
";

        public const string FIX_math_log_log10_CODE = @"
import math
math._log = math.log
math.log = lambda x: math._log(float(x))
math._log10 = math.log10
math.log10 = lambda x: math._log10(float(x))
";

        public const string FAKE_numpy_testing_CODE = @"
class Tester():
    def test(self, *args, **kwargs):
        print msg
    def bench(self, *args, **kwargs):
        print msg
ScipyTest = NumpyTest = Tester
";
    }
}
