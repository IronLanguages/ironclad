namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string FIX_CPyMarshal_RuntimeType_CODE = @"
CPyMarshal = CPyMarshal() # eww
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
