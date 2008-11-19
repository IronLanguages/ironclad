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

        private readonly string[] EASY_TYPE_FIELDS = new string[] { "tp_call", "tp_repr", "tp_str", "tp_compare", "tp_hash" };
        private readonly string[] MP_FIELDS = new string[] { "mp_subscript", "mp_ass_subscript", "mp_length" };
        private readonly string[] SQ_FIELDS = new string[] { "sq_item", "sq_ass_item", "sq_length", "sq_slice", "sq_ass_slice" };
        private readonly string[] NB_FIELDS = new string[] { 
            "nb_add", "nb_subtract", "nb_multiply", "nb_divide", "nb_true_divide", 
              "nb_floor_divide", "nb_remainder", "nb_divmod", 
            "nb_lshift", "nb_rshift", "nb_and", "nb_xor", "nb_or", 
              "nb_inplace_add", "nb_inplace_subtract", "nb_inplace_multiply", "nb_inplace_divide", 
              "nb_inplace_true_divide", "nb_inplace_floor_divide", "nb_inplace_remainder", 
              "nb_inplace_lshift", "nb_inplace_rshift", "nb_inplace_and", "nb_inplace_xor", "nb_inplace_or", 
            "nb_negative", "nb_positive", "nb_absolute", "nb_invert", "nb_int", "nb_long", "nb_float", 
              "nb_oct", "nb_hex", "nb_index", 
            "nb_nonzero",
            "nb_power", "nb_inplace_power",};

        public ClassBuilder(IntPtr typePtr)
        {
            this.ptr = typePtr;
            this.Build();
        }

        private void
        Build()
        {
            this.BeginClass();
            this.GenerateMembers();
            this.GenerateProperties();
            this.GenerateMethods();
            this.GenerateMagicMethods();
            this.GenerateActualiser();
        }

        private void
        BeginClass()
        {
            this.tp_name = CPyMarshal.ReadCStringField(this.ptr, typeof(PyTypeObject), "tp_name");
            CallableBuilder.ExtractNameModule(this.tp_name, ref this.__name__, ref this.__module__);
            string __doc__ = CPyMarshal.ReadCStringField(this.ptr, typeof(PyTypeObject), "tp_doc").Replace("\\", "\\\\");
            this.code.Append(String.Format(CodeSnippets.CLASS_CODE, this.__name__, this.__module__, __doc__));

            this.tablePrefix = this.__name__ + ".";
            this.ConnectTypeField("tp_new", typeof(Python25Api.PyType_GenericNew_Delegate));
            this.ConnectTypeField("tp_init", typeof(CPython_initproc_Delegate));
        }

        private void
        GenerateProperties()
        {
            IntPtr getsetPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), "tp_getset");
            if (getsetPtr == IntPtr.Zero)
            {
                return;
            }
            while (CPyMarshal.ReadInt(getsetPtr) != 0)
            {
                this.GenerateProperty(getsetPtr);
                getsetPtr = CPyMarshal.Offset(getsetPtr, Marshal.SizeOf(typeof(PyGetSetDef)));
            }
        }

        private void
        GenerateMembers()
        {
            IntPtr memberPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), "tp_members");
            if (memberPtr == IntPtr.Zero)
            {
                return;
            }
            while (CPyMarshal.ReadInt(memberPtr) != 0)
            {
                this.GenerateMember(memberPtr);
                memberPtr = CPyMarshal.Offset(memberPtr, Marshal.SizeOf(typeof(PyMemberDef)));
            }
        }

        private void
        GenerateMethods()
        {
            IntPtr methodsPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), "tp_methods");
            CallableBuilder.GenerateMethods(this.code, methodsPtr, this.methodTable, this.tablePrefix);
        }

        private void
        GenerateMagicMethods()
        {
            this.GenerateProtocolMagicMethods(this.ptr, typeof(PyTypeObject), EASY_TYPE_FIELDS);
            this.GenerateNamedProtocolMagicMethods("tp_as_number", typeof(PyNumberMethods), NB_FIELDS);
            this.GenerateNamedProtocolMagicMethods("tp_as_mapping", typeof(PyMappingMethods), MP_FIELDS);
            this.GenerateNamedProtocolMagicMethods("tp_as_sequence", typeof(PySequenceMethods), SQ_FIELDS);
            this.HandleMappingSequenceCollision();
            this.GenerateRichcmpMethods();
            this.GenerateIterMethods();
            this.UglyComplexHack();
        }
        
        private void
        GenerateActualiser()
        {
            this.code.Append(CodeSnippets.ACTUALISER_CODE);
        }

        private void
        GenerateProperty(IntPtr getsetPtr)
        {
            string getname = "None";
            string setname = "None";
            PyGetSetDef getset = (PyGetSetDef)Marshal.PtrToStructure(getsetPtr, typeof(PyGetSetDef));

            if (getset.get != IntPtr.Zero)
            {
                getname = String.Format("__get_{0}", getset.name);
                this.code.Append(String.Format(CodeSnippets.GETTER_METHOD_CODE, getname, this.tablePrefix, getset.closure));

                CPython_getter_Delegate dgt = (CPython_getter_Delegate)
                    Marshal.GetDelegateForFunctionPointer(
                        getset.get, typeof(CPython_getter_Delegate));
                this.methodTable[this.tablePrefix + getname] = dgt;
            }

            if (getset.set != IntPtr.Zero)
            {
                setname = String.Format("__set_{0}", getset.name);
                this.code.Append(String.Format(CodeSnippets.SETTER_METHOD_CODE, setname, this.tablePrefix, getset.closure));

                CPython_setter_Delegate dgt = (CPython_setter_Delegate)
                    Marshal.GetDelegateForFunctionPointer(
                        getset.set, typeof(CPython_setter_Delegate));
                this.methodTable[this.tablePrefix + setname] = dgt;
            }

            this.code.Append(String.Format(CodeSnippets.PROPERTY_CODE, getset.name, getname, setname, getset.doc));
        }

        private static bool
        TryGetMemberMethodSuffix(MemberT type, ref string suffix)
        {
            switch (type)
            {
                case MemberT.INT:
                    suffix = "int";
                    return true;
                case MemberT.CHAR:
                    suffix = "char";
                    return true;
                case MemberT.UBYTE:
                    suffix = "ubyte";
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

            string suffix = null;
            if (TryGetMemberMethodSuffix(member.type, ref suffix))
            {
                string getname = String.Format("__get_{0}", member.name);
                this.code.Append(String.Format(CodeSnippets.MEMBER_GETTER_CODE, getname, member.offset, suffix));

                string setname = "None";
                if ((member.flags & 1) == 0)
                {
                    setname = String.Format("__set_{0}", member.name);
                    this.code.Append(String.Format(CodeSnippets.MEMBER_SETTER_CODE, setname, member.offset, suffix));
                }
                this.code.Append(String.Format(CodeSnippets.PROPERTY_CODE, member.name, getname, setname, member.doc));
            }
            else
            {
                Console.WriteLine("detected unsupported member type {0}; ignoring", member.type);
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
        GenerateIterMethods()
        {
            Py_TPFLAGS tp_flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(this.ptr, typeof(PyTypeObject), "tp_flags");
            if ((tp_flags & Py_TPFLAGS.HAVE_ITER) == 0)
            {
                return;
            }
            if (CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), "tp_iter") != IntPtr.Zero)
            {
                this.code.Append(String.Format(CodeSnippets.ITER_METHOD_CODE, tablePrefix));
                this.ConnectTypeField("tp_iter", typeof(CPythonSelfFunction_Delegate));
            }
            if (CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), "tp_iternext") != IntPtr.Zero)
            {
                this.code.Append(String.Format(CodeSnippets.ITERNEXT_METHOD_CODE, tablePrefix));
                this.ConnectTypeField("tp_iternext", typeof(CPythonSelfFunction_Delegate));
            }
        }

        private void
        GenerateRichcmpMethods()
        {
            if (CPyMarshal.ReadPtrField(this.ptr, typeof(PyTypeObject), "tp_richcompare") != IntPtr.Zero)
            {
                this.code.Append(String.Format(CodeSnippets.RICHCMP_METHOD_CODE, tablePrefix));
                this.ConnectTypeField("tp_richcompare", typeof(CPython_richcmpfunc_Delegate));
            }
        }

        private void
        HandleMappingSequenceCollision()
        {
            if (this.methodTable.has_key(this.tablePrefix + "_getitem_sq_item") ||
                this.methodTable.has_key(this.tablePrefix + "_getitem_mp_subscript"))
            {
                this.code.Append(CodeSnippets.GETITEM_CODE);
            }

            if (this.methodTable.has_key(this.tablePrefix + "_setitem_sq_ass_item") ||
                this.methodTable.has_key(this.tablePrefix + "_setitem_mp_ass_subscript"))
            {
                this.code.Append(CodeSnippets.SETITEM_CODE);
            }

            if (this.methodTable.has_key(this.tablePrefix + "_len_sq_length") ||
                this.methodTable.has_key(this.tablePrefix + "_len_mp_length"))
            {
                this.code.Append(CodeSnippets.LEN_CODE);
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