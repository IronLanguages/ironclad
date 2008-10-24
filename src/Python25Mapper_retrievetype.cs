using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private void
        GenerateClass(IntPtr typePtr)
        {
            ClassBuilder cb = new ClassBuilder(typePtr);
            object ob_type = this.UpdateMethodTableField(cb.methodTable, typePtr, "ob_type");
            object tp_base = this.UpdateMethodTableField(cb.methodTable, typePtr, "tp_base");

            PythonTuple tp_bases = null;
            IntPtr tp_basesPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_bases");
            if (tp_basesPtr != IntPtr.Zero)
            {
                tp_bases = (PythonTuple)this.Retrieve(tp_basesPtr);
                foreach (object _base in tp_bases)
                {
                    this.UpdateMethodTableObj(cb.methodTable, _base);
                }
            }
            if (tp_bases == null)
            {
                tp_bases = new PythonTuple(new object[] { tp_base });
            }

            this.scratchModule.SetVariable("_ironclad_metaclass", ob_type);
            this.scratchModule.SetVariable("_ironclad_bases", tp_bases);
            this.ExecInModule(cb.code.ToString(), this.scratchModule);

            object klass = this.scratchModule.GetVariable<object>(cb.__name__);
            object _dispatcher = PythonCalls.Call(this.dispatcherClass, new object[] { this, cb.methodTable });
            Builtin.setattr(this.scratchContext, klass, "_dispatcher", _dispatcher);
            object typeDict = Builtin.getattr(this.scratchContext, klass, "__dict__");
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_dict", this.Store(typeDict));

            object klass_actualiser = this.scratchModule.GetVariable<object>(cb.__name__ + "_actualiser");
            this.actualiseHelpers[typePtr] = klass_actualiser;
            
            this.map.Associate(typePtr, klass);
            this.IncRef(typePtr);
        }

        private object
        UpdateMethodTableField(PythonDictionary methodTable, IntPtr typePtr, string field)
        {
            IntPtr potentialMethodSourcePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), field);
            return this.UpdateMethodTablePtr(methodTable, potentialMethodSourcePtr);
        }

        private object
        UpdateMethodTablePtr(PythonDictionary methodTable, IntPtr potentialMethodSourcePtr)
        {
            object potentialMethodSource = this.Retrieve(potentialMethodSourcePtr);
            return this.UpdateMethodTableObj(methodTable, potentialMethodSource);
        }

        private object
        UpdateMethodTableObj(PythonDictionary methodTable, object potentialMethodSource)
        {
            if (Builtin.hasattr(this.scratchContext, potentialMethodSource, "_dispatcher"))
            {
                PythonDictionary methodSource = (PythonDictionary)Builtin.getattr(
                    this.scratchContext, Builtin.getattr(
                        this.scratchContext, potentialMethodSource, "_dispatcher"), "table");
                methodTable.update(this.scratchContext, methodSource);
            }
            this.Store(potentialMethodSource);
            return potentialMethodSource;
        }
    }
}
