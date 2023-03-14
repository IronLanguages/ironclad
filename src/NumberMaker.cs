using System;

using System.Numerics;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;


namespace Ironclad
{
    public class NumberMaker
    {
        public static BigInteger
        MakeBigInteger(CodeContext ctx, object obj)
        {
            var index = PythonOps.Index(obj);
            switch (index)
            {
                case int i:
                    return i;
                case BigInteger bi:
                    return bi;
                default:
                    throw new InvalidOperationException();
            }
        }
        
        public static BigInteger
        MakeUnsignedBigInteger(CodeContext ctx, object obj)
        {
            BigInteger result = MakeBigInteger(ctx, obj);
            
            if (result < 0)
            {
                throw PythonOps.TypeError("cannot make {0} unsigned", result);
            }
            
            return result;
        }
        
        
        public static double
        MakeFloat(CodeContext ctx, object obj)
        {
            try
            {
                return Converter.ConvertToDouble(obj);
            }
            catch
            {
                // one of the following fallbacks *might* work
            }
            
            if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                Builtin.hasattr(ctx, obj, "__int__"))
            {
                object probablyInt = PythonCalls.Call(TypeCache.Int32, new object[] {obj});
                return MakeFloat(ctx, probablyInt);
            }
            
            if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                Builtin.hasattr(ctx, obj, "__index__"))
            {
                object probablyLong = PythonCalls.Call(TypeCache.BigInteger, new object[] {obj});
                return MakeFloat(ctx, probablyLong);
            }
            
            throw PythonOps.TypeError("could not make number sufficiently floatesque");
        }
    }
}
