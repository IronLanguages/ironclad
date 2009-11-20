using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        private object
        GenerateClass(IntPtr typePtr)
        {
            ClassBuilder cb = new ClassBuilder(typePtr);
            PythonTuple tp_bases = this.ExtractBases(typePtr);
            foreach (object _base in tp_bases)
            {
                this.UpdateMethodTableObj(cb.methodTable, _base);
            }

            IntPtr ob_typePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyObject), "ob_type");
            this.IncRef(ob_typePtr);
            object ob_type = this.Retrieve(ob_typePtr);

            this.scratchModule.Get__dict__()["_ironclad_metaclass"] = ob_type;
            this.scratchModule.Get__dict__()["_ironclad_bases"] = tp_bases;
            this.ExecInModule(cb.code.ToString(), this.scratchModule);
            object klass = this.scratchModule.Get__dict__()["_ironclad_class"];
            object klass_stub = this.scratchModule.Get__dict__()["_ironclad_class_stub"];

            this.classStubs[typePtr] = klass_stub;
            Builtin.setattr(this.scratchContext, klass, "_dispatcher", new Dispatcher(this, cb.methodTable));
            object typeDict = Builtin.getattr(this.scratchContext, klass, "__dict__");
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_dict", this.Store(typeDict));
            return klass;
        }
        
        private PythonTuple
        ExtractBases(IntPtr typePtr)
        {
            PythonTuple tp_bases = null;
            IntPtr tp_basesPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_bases");
            if (tp_basesPtr != IntPtr.Zero)
            {
                tp_bases = (PythonTuple)this.Retrieve(tp_basesPtr);
            }
            if (tp_bases == null)
            {
                IntPtr tp_basePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_base");
                tp_bases = new PythonTuple(new object[] { this.Retrieve(tp_basePtr) });
            }
            return tp_bases;
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
