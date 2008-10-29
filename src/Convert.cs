using System;

using Microsoft.Scripting.Math;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;


namespace Ironclad
{
    // if you can work out how to remove the dependence on this.scratchContext,
    // then this can become the static utility class it so obviously and desperately
    // wants to be
    public partial class Python25Mapper : Python25Api
    {
        public BigInteger
        MakeBigInteger(object obj)
        {
            try
            {
                return Converter.ConvertToBigInteger(obj);
            }
            catch
            {
                // one of the following fallbacks *might* work
            }
            
            if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                Builtin.hasattr(this.scratchContext, obj, "__int__"))
            {
                object probablyInt = PythonCalls.Call(TypeCache.Int32, new object[] {obj});
                return this.MakeBigInteger(probablyInt);
            }
            if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                Builtin.hasattr(this.scratchContext, obj, "__float__"))
            {
                object probablyFloat = PythonCalls.Call(TypeCache.Double, new object[] {obj});
                return this.MakeBigInteger(probablyFloat);
            }
            throw PythonOps.TypeError("could not make number sufficiently integeresque");
        }
        
        public BigInteger
        MakeUnsignedBigInteger(object obj)
        {
            BigInteger result = this.MakeBigInteger(obj);
            if (result < 0)
            {
                throw PythonOps.TypeError("cannot make {0} unsigned", result);
            }
            return result;
        }
        
        
        public double
        MakeFloat(object obj)
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
                Builtin.hasattr(this.scratchContext, obj, "__int__"))
            {
                object probablyInt = PythonCalls.Call(TypeCache.Int32, new object[] {obj});
                return this.MakeFloat(probablyInt);
            }
            if ((!Builtin.isinstance(obj, TypeCache.PythonType)) &&
                Builtin.hasattr(this.scratchContext, obj, "__long__"))
            {
                object probablyLong = PythonCalls.Call(TypeCache.BigInteger, new object[] {obj});
                return this.MakeFloat(probablyLong);
            }
            throw PythonOps.TypeError("could not make number sufficiently floatesque");
        }
    }
}
