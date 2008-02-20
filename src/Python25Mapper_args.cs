using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime;

namespace JumPy
{
    public partial class Python25Mapper : PythonMapper
    {
        protected virtual Dictionary<int, object> 
        GetArgValues(IntPtr args, IntPtr kwargs, IntPtr kwlist)
        {
            Tuple actualArgs = (Tuple)this.Retrieve(args);
            Dict actualKwargs = (Dict)this.Retrieve(kwargs);

            Dictionary<int, object> result = new Dictionary<int, object>();
            for (int i = 0; i < actualArgs.GetLength(); i++)
            {
                result[i] = actualArgs[i];
            }
            
            int intPtrSize = Marshal.SizeOf(typeof(IntPtr));
            int index = 0;
            IntPtr currentKw = kwlist;
            while (Marshal.ReadIntPtr(currentKw) != IntPtr.Zero)
            {
                IntPtr addressToRead = CPyMarshal.ReadPtr(currentKw);
                string thisKey = Marshal.PtrToStringAnsi(addressToRead);
                if (actualKwargs.ContainsKey(thisKey))
                {
                    result[index] = actualKwargs[thisKey];
                }
                currentKw = (IntPtr)(currentKw.ToInt32() + intPtrSize);
                index++;
            }
        
            return result;
        }


        protected virtual Dictionary<int, object> 
        GetArgValues(IntPtr args)
        {
            Tuple actualArgs = (Tuple)this.Retrieve(args);
            Dictionary<int, object> result =  new Dictionary<int, object>();
            for (int i = 0; i < actualArgs.GetLength(); i++)
            {
                result[i] = actualArgs[i];
            }
            return result;
        }


        protected virtual Dictionary<int, ArgWriter> 
        GetArgWriters(string format)
        {
            Dictionary<int, ArgWriter> result = new Dictionary<int, ArgWriter>();
            string trimmedFormat = format;
            int argIndex = 0;
            int nextStartPointer = 0;
            while (trimmedFormat.Length > 0 && 
                   !trimmedFormat.StartsWith(":") &&
                   !trimmedFormat.StartsWith(";"))
            {
                if (trimmedFormat.StartsWith("|"))
                {
                    trimmedFormat = trimmedFormat.Substring(1);
                    continue;
                }
                
                if (trimmedFormat.StartsWith("i"))
                {
                    trimmedFormat = trimmedFormat.Substring(1);
                    result[argIndex] = new IntArgWriter(nextStartPointer);
                }
                else if (trimmedFormat.StartsWith("O"))
                {
                    trimmedFormat = trimmedFormat.Substring(1);
                    result[argIndex] = new ObjectArgWriter(nextStartPointer, this);
                }
                else if (trimmedFormat.StartsWith("s#"))
                {
                    trimmedFormat = trimmedFormat.Substring(2);
                    result[argIndex] = new SizedStringArgWriter(nextStartPointer, this);
                }
                else if (trimmedFormat.StartsWith("s"))
                {
                    trimmedFormat = trimmedFormat.Substring(1);
                    result[argIndex] = new CStringArgWriter(nextStartPointer, this);
                }
                else
                {
                    throw new NotImplementedException(String.Format(
                        "Unrecognised characters in format string, starting at: {0}", 
                        trimmedFormat));
                }
                nextStartPointer = result[argIndex].NextWriterStartIndex;
                argIndex++;
            }
            return result;
        }


        protected virtual int 
        SetArgValues(Dictionary<int, object> argsToWrite, 
                     Dictionary<int, ArgWriter> argWriters, 
                     IntPtr outPtr)
        {
            try
            {
                foreach (KeyValuePair<int,object> p in argsToWrite)
                {
                    argWriters[p.Key].Write(outPtr, p.Value);
                }
            }
            catch (Exception e)
            {
                this._lastException = e;
                return 0;
            }
            return 1;
        }


        public override int 
        PyArg_ParseTupleAndKeywords(IntPtr args, 
                                    IntPtr kwargs, 
                                    string format, 
                                    IntPtr kwlist, 
                                    IntPtr outPtr)
        {
            Dictionary<int, object> argsToWrite = this.GetArgValues(args, kwargs, kwlist);
            Dictionary<int, ArgWriter> argWriters = this.GetArgWriters(format);
            return this.SetArgValues(argsToWrite, argWriters, outPtr);
        }


        public override int 
        PyArg_ParseTuple(IntPtr args, 
                         string format, 
                         IntPtr outPtr)
        {
            Dictionary<int, object> argsToWrite = this.GetArgValues(args);
            Dictionary<int, ArgWriter> argWriters = this.GetArgWriters(format);
            return this.SetArgValues(argsToWrite, argWriters, outPtr);
        }
    }
}
