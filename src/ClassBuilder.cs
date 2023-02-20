using System;
using System.Text;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    internal class ClassBuilder
    {
        public StringBuilder code = new StringBuilder();
        public PythonDictionary methodTable = new PythonDictionary();

        public IntPtr ptr = IntPtr.Zero;
        public string tablePrefix = null;
        public string __name__ = null;
        public string __module__ = null;
        public string tp_name = null;

        private readonly string[] EASY_TYPE_FIELDS = new string[] { 
            nameof(PyTypeObject.tp_init), nameof(PyTypeObject.tp_call), nameof(PyTypeObject.tp_repr),
            nameof(PyTypeObject.tp_str), nameof(PyTypeObject.tp_compare), nameof(PyTypeObject.tp_hash), 
            nameof(PyTypeObject.tp_getattr), nameof(PyTypeObject.tp_iter), nameof(PyTypeObject.tp_iternext),
        };
        private readonly string[] MP_FIELDS = new string[] { 
            nameof(PyMappingMethods.mp_subscript), nameof(PyMappingMethods.mp_ass_subscript), nameof(PyMappingMethods.mp_length),
        };
        private readonly string[] SQ_FIELDS = new string[] { 
            nameof(PySequenceMethods.sq_item), nameof(PySequenceMethods.sq_concat), nameof(PySequenceMethods.sq_ass_item),
            nameof(PySequenceMethods.sq_length), nameof(PySequenceMethods.sq_slice), nameof(PySequenceMethods.sq_ass_slice),
            nameof(PySequenceMethods.sq_contains),
        };
        private readonly string[] NB_FIELDS = new string[] { 
            nameof(PyNumberMethods.nb_add), nameof(PyNumberMethods.nb_subtract), nameof(PyNumberMethods.nb_multiply),
            nameof(PyNumberMethods.nb_divide), nameof(PyNumberMethods.nb_true_divide), nameof(PyNumberMethods.nb_floor_divide),
            nameof(PyNumberMethods.nb_remainder), nameof(PyNumberMethods.nb_divmod), nameof(PyNumberMethods.nb_lshift),
            nameof(PyNumberMethods.nb_rshift), nameof(PyNumberMethods.nb_and), nameof(PyNumberMethods.nb_xor),
            nameof(PyNumberMethods.nb_or), nameof(PyNumberMethods.nb_inplace_add), nameof(PyNumberMethods.nb_inplace_subtract),
            nameof(PyNumberMethods.nb_inplace_multiply), nameof(PyNumberMethods.nb_inplace_divide), nameof(PyNumberMethods.nb_inplace_true_divide),
            nameof(PyNumberMethods.nb_inplace_floor_divide), nameof(PyNumberMethods.nb_inplace_remainder), nameof(PyNumberMethods.nb_inplace_lshift),
            nameof(PyNumberMethods.nb_inplace_rshift), nameof(PyNumberMethods.nb_inplace_and), nameof(PyNumberMethods.nb_inplace_xor),
            nameof(PyNumberMethods.nb_inplace_or), nameof(PyNumberMethods.nb_negative), nameof(PyNumberMethods.nb_positive),
            nameof(PyNumberMethods.nb_absolute), nameof(PyNumberMethods.nb_invert), nameof(PyNumberMethods.nb_int),
            nameof(PyNumberMethods.nb_long), nameof(PyNumberMethods.nb_float), nameof(PyNumberMethods.nb_oct),
            nameof(PyNumberMethods.nb_hex), nameof(PyNumberMethods.nb_index), nameof(PyNumberMethods.nb_nonzero),
            nameof(PyNumberMethods.nb_power), nameof(PyNumberMethods.nb_inplace_power),
        };

        public ClassBuilder(IntPtr typePtr)
        {
            this.ptr = typePtr;
            this.Build();
        }

        private void
        Build()
        {
            this.InitialiseScope();
            
            this.GenerateMembers();
            this.GenerateProperties();
            this.GenerateMagicMethods(); // } This order of calls effectively treats all methods as having the
            this.GenerateMethods();      // } COEXIST flag set; swap would be equivalent to it never being set.
            this.GenerateClass();
            
            this.code.Append(CodeSnippets.CLASS_STUB_CODE);
        }

        private void
        InitialiseScope()
        {
            this.tp_name = CPyMarshal.ReadCStringField(this.ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_name));
            CallableBuilder.ExtractNameModule(this.tp_name, ref this.__name__, ref this.__module__);
            this.tablePrefix = this.__name__ + ".";
            this.code.Append("_ironclad_class_attrs = dict()");
        }

        private void
        GenerateClass()
        {
            string __doc__ = CPyMarshal.ReadCStringField(this.ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_doc)).Replace("\\", "\\\\");
            this.code.Append(String.Format(CodeSnippets.CLASS_TEMPLATE, this.__name__, this.__module__, __doc__));
            this.ConnectTypeField("tp_new", typeof(dgt_ptr_ptrptrptr));
        }

        private void
        GenerateProperties()
        {
            IntPtr getsetPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_getset));
            if (getsetPtr == IntPtr.Zero)
            {
                return;
            }
            
            while (CPyMarshal.ReadInt(getsetPtr) != 0)
            {
                this.GenerateProperty(getsetPtr);
                getsetPtr = CPyMarshal.Offset(getsetPtr, Marshal.SizeOf<PyGetSetDef>());
            }
        }

        private void
        GenerateMembers()
        {
            IntPtr memberPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_members));
            if (memberPtr == IntPtr.Zero)
            {
                return;
            }
            
            while (CPyMarshal.ReadInt(memberPtr) != 0)
            {
                this.GenerateMember(memberPtr);
                memberPtr = CPyMarshal.Offset(memberPtr, Marshal.SizeOf<PyMemberDef>());
            }
        }

        private void
        GenerateMethods()
        {
            IntPtr methodsPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_methods));
            CallableBuilder.GenerateMethods(this.code, methodsPtr, this.methodTable, this.tablePrefix);
        }

        private void
        GenerateMagicMethods()
        {
            this.GenerateProtocolMagicMethods(this.ptr, typeof(PyTypeObject), EASY_TYPE_FIELDS);
            this.GenerateNamedProtocolMagicMethods(nameof(PyTypeObject.tp_as_sequence), typeof(PySequenceMethods), SQ_FIELDS);
            this.GenerateNamedProtocolMagicMethods(nameof(PyTypeObject.tp_as_mapping), typeof(PyMappingMethods), MP_FIELDS);
            this.GenerateNamedProtocolMagicMethods(nameof(PyTypeObject.tp_as_number), typeof(PyNumberMethods), NB_FIELDS);
            this.GenerateRichcmpMethods();
            this.UglyComplexHack();
        }

        private void
        GenerateProperty(IntPtr getsetPtr)
        {
            string getname = "None";
            string setname = "None";
            this.code.Append(CodeSnippets.CLEAR_GETTER_SETTER_CODE);
            PyGetSetDef getset = (PyGetSetDef)Marshal.PtrToStructure(getsetPtr, typeof(PyGetSetDef));
        
            if (getset.get != IntPtr.Zero)
            {
                getname = String.Format("__get_{0}", getset.name);
                this.code.Append(String.Format(CodeSnippets.GETTER_METHOD_TEMPLATE, getname, this.tablePrefix, getset.closure));

                dgt_ptr_ptrptr dgt = (dgt_ptr_ptrptr)
                    Marshal.GetDelegateForFunctionPointer(
                        getset.get, typeof(dgt_ptr_ptrptr));
                this.methodTable[this.tablePrefix + getname] = dgt;
            }

            if (getset.set != IntPtr.Zero)
            {
                setname = String.Format("__set_{0}", getset.name);
                this.code.Append(String.Format(CodeSnippets.SETTER_METHOD_TEMPLATE, setname, this.tablePrefix, getset.closure));

                dgt_int_ptrptrptr dgt = (dgt_int_ptrptrptr)
                    Marshal.GetDelegateForFunctionPointer(
                        getset.set, typeof(dgt_int_ptrptrptr));
                this.methodTable[this.tablePrefix + setname] = dgt;
            }

            this.code.Append(String.Format(CodeSnippets.PROPERTY_CODE, getset.name, getset.doc));
        }

        private static bool
        TryGetMemberMethodInfix(MemberT type, ref string suffix)
        {
            switch (type)
            {
                case MemberT.INT:
                    suffix = "int";
                    return true;
                case MemberT.UINT:
                    suffix = "uint";
                    return true;
                case MemberT.LONG:
                    suffix = "long";
                    return true;
                case MemberT.ULONG:
                    suffix = "ulong";
                    return true;
                case MemberT.DOUBLE:
                    suffix = "double";
                    return true;
                case MemberT.CHAR:
                    suffix = "char";
                    return true;
                case MemberT.UBYTE:
                    suffix = "ubyte";
                    return true;
                case MemberT.STRING:
                    suffix = "string";
                    return true;
                case MemberT.OBJECT:
                    suffix = "object";
                    return true;
                default:
                    return false;
            }
        }

        private void
        GenerateMember(IntPtr memberPtr)
        {
            PyMemberDef member = (PyMemberDef)Marshal.PtrToStructure(
                memberPtr, typeof(PyMemberDef));

            this.code.Append(CodeSnippets.CLEAR_GETTER_SETTER_CODE);

            string infix = null;
            if (TryGetMemberMethodInfix((MemberT)member.type, ref infix))
            {
                string getname = String.Format("__get_{0}", member.name);
                this.code.Append(String.Format(CodeSnippets.MEMBER_GETTER_TEMPLATE, getname, member.offset, infix));

                string setname = "None";
                if ((member.flags & 1) == 0 && (MemberT)member.type != MemberT.STRING)
                {
                    setname = String.Format("__set_{0}", member.name);
                    this.code.Append(String.Format(CodeSnippets.MEMBER_SETTER_TEMPLATE, setname, member.offset, infix));
                }
                this.code.Append(String.Format(CodeSnippets.PROPERTY_CODE, member.name, member.doc));
            }
            else
            {
                Console.WriteLine("detected unsupported member type {0}; ignoring", (Py_TPFLAGS)member.type);
            }
        }

        private void
        GenerateNamedProtocolMagicMethods(string protocolName, Type protocolType, string[] fields)
        {
            IntPtr pPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), protocolName);
            this.GenerateProtocolMagicMethods(pPtr, protocolType, fields);
        }

        private void
        GenerateProtocolMagicMethods(IntPtr protocolPtr, Type protocol, string[] fields)
        {
            if (protocolPtr == IntPtr.Zero)
            {
                return;
            }
            
            foreach (string field in fields)
            {
                if (CPyMarshal.ReadPtrField(protocolPtr, protocol, field) != IntPtr.Zero)
                {
                    string name;
                    string template;
                    Type dgtType;
                    bool needGetSwappedInfo;
                    MagicMethods.GetInfo(field, out name, out template, out dgtType, out needGetSwappedInfo);
                    this.methodTable[this.tablePrefix + name] = CPyMarshal.ReadFunctionPtrField(protocolPtr, protocol, field, dgtType);
                    this.code.Append(String.Format(template, name, "", this.tablePrefix));

                    if (needGetSwappedInfo)
                    {
                        MagicMethods.GetSwappedInfo(field, out name, out template, out dgtType);
                        this.methodTable[this.tablePrefix + name] = CPyMarshal.ReadFunctionPtrField(protocolPtr, protocol, field, dgtType); ;
                        this.code.Append(String.Format(template, name, "", this.tablePrefix));
                    }
                }
            }
        }

        private void
        GenerateRichcmpMethods()
        {
            if (CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_richcompare)) != IntPtr.Zero)
            {
                this.code.Append(String.Format(CodeSnippets.RICHCMP_METHOD_TEMPLATE, tablePrefix));
                this.ConnectTypeField("tp_richcompare", typeof(dgt_ptr_ptrptrint));
            }
        }
        
        
        private void
        UglyComplexHack()
        {
            if (this.methodTable.has_key(this.tablePrefix + "__get_real") &&
                this.methodTable.has_key(this.tablePrefix + "__get_imag"))
            {
                this.code.Append(CodeSnippets.COMPLEX_HACK_CODE);
            }
        }


        private void
        ConnectTypeField(string fieldName, Type dgtType)
        {
            if (CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), fieldName) != IntPtr.Zero)
            {
                Delegate dgt = CPyMarshal.ReadFunctionPtrField(this.ptr, typeof(PyTypeObject), fieldName, dgtType);
                this.methodTable[this.tablePrefix + fieldName] = dgt;
            }
        }
    }
}
