using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;

using Ironclad.Structs;


namespace Ironclad
{

    public partial class PythonMapper
    {
        public override void
        Register__Py_NoneStruct(IntPtr address)
        {
            PyObject none = new PyObject();
            none.ob_refcnt = 1;
            none.ob_type = this.PyNone_Type;
            Marshal.StructureToPtr(none, address, false);
            // no need to Associate: None/null is special-cased
        }

        public override void
        Register__Py_ZeroStruct(IntPtr address)
        {
            PyIntObject False = new PyIntObject();
            False.ob_refcnt = 1;
            False.ob_type = this.PyBool_Type;
            False.ob_ival = 0;
            Marshal.StructureToPtr(False, address, false);
            this.map.Associate(address, Builtin.False);
        }

        public override void
        Register__Py_TrueStruct(IntPtr address)
        {
            PyIntObject True = new PyIntObject();
            True.ob_refcnt = 1;
            True.ob_type = this.PyBool_Type;
            True.ob_ival = 1;
            Marshal.StructureToPtr(True, address, false);
            this.map.Associate(address, Builtin.True);
        }

        public override void
        Register__Py_EllipsisObject(IntPtr address)
        {
            PyObject ellipsis = new PyObject();
            ellipsis.ob_refcnt = 1;
            ellipsis.ob_type = this.PyEllipsis_Type;
            Marshal.StructureToPtr(ellipsis, address, false);
            this.map.Associate(address, Builtin.Ellipsis);
        }

        public override void
        Register__Py_NotImplementedStruct(IntPtr address)
        {
            PyObject notimpl = new PyObject();
            notimpl.ob_refcnt = 1;
            notimpl.ob_type = this.PyNotImplemented_Type;
            Marshal.StructureToPtr(notimpl, address, false);
            this.map.Associate(address, PythonOps.NotImplemented);
        }

        public override void
        Register_Py_OptimizeFlag(IntPtr address)
        {
            CPyMarshal.WriteInt(address, 2);
        }

        public override void
        Register__PyThreadState_Current(IntPtr address)
        {
            CPyMarshal.WritePtr(address, IntPtr.Zero);
        }

        public override void
        Register_PyEllipsis_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            // (but surely there's a better way to get the Ellipsis object...)
            CPyMarshal.Zero(address, Marshal.SizeOf<PyTypeObject>());
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.ob_refcnt), 1);
            CPyMarshal.WriteCStringField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_name), "ellipsis");
            object ellipsisType = PythonCalls.Call(Builtin.type, new object[] { PythonOps.Ellipsis });
            this.map.Associate(address, ellipsisType);
        }

        public override void
        Register_PyNotImplemented_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            // (but surely there's a better way to get the NotImplemented object...)
            CPyMarshal.Zero(address, Marshal.SizeOf<PyTypeObject>());
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.ob_refcnt), 1);
            CPyMarshal.WriteCStringField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_name), "NotImplementedType");
            object notImplementedType = PythonCalls.Call(Builtin.type, new object[] { PythonOps.NotImplemented });
            this.map.Associate(address, notImplementedType);
        }

        public override void
        Register_PyBool_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            CPyMarshal.Zero(address, Marshal.SizeOf<PyTypeObject>());
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_base), this.PyInt_Type);
            CPyMarshal.WriteCStringField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_name), "bool");
            this.map.Associate(address, TypeCache.Boolean);
        }

        public override void
        Register_PyBytes_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            CPyMarshal.Zero(address, Marshal.SizeOf<PyTypeObject>());
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_basicsize), (nint)Marshal.SizeOf<PyBytesObject>() - 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_itemsize), 1);
            CPyMarshal.WriteCStringField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_name), "str");
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_str), this.GetFuncPtr(nameof(IC_PyBytes_Str)));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_repr), this.GetFuncPtr(nameof(PyObject_Repr)));

            int sqSize = Marshal.SizeOf<PySequenceMethods>();
            IntPtr sqPtr = this.allocator.Alloc(sqSize);
            CPyMarshal.Zero(sqPtr, sqSize);
            CPyMarshal.WritePtrField(sqPtr, typeof(PySequenceMethods), nameof(PySequenceMethods.sq_concat), this.GetFuncPtr(nameof(IC_PyBytes_Concat_Core)));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_sequence), sqPtr);

            int bfSize = Marshal.SizeOf<PyBufferProcs>();
            IntPtr bfPtr = this.allocator.Alloc(bfSize);
            CPyMarshal.Zero(bfPtr, bfSize);
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), nameof(PyBufferProcs.bf_getreadbuffer), this.GetFuncPtr(nameof(IC_bytes_getreadbuffer)));
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), nameof(PyBufferProcs.bf_getwritebuffer), this.GetFuncPtr(nameof(IC_bytes_getwritebuffer)));
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), nameof(PyBufferProcs.bf_getsegcount), this.GetFuncPtr(nameof(IC_bytes_getsegcount)));
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), nameof(PyBufferProcs.bf_getcharbuffer), this.GetFuncPtr(nameof(IC_bytes_getreadbuffer)));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_buffer), bfPtr);

            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags), (Int32)Py_TPFLAGS.HAVE_GETCHARBUFFER);

            this.map.Associate(address, TypeCache.String);
        }

        private void
        AddNumberMethodsWithoutIndex(IntPtr typePtr)
        {
            int nmSize = Marshal.SizeOf<PyNumberMethods>();
            IntPtr nmPtr = this.allocator.Alloc(nmSize);
            CPyMarshal.Zero(nmPtr, nmSize);

            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), nameof(PyNumberMethods.nb_int), this.GetFuncPtr(nameof(PyNumber_Int)));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), nameof(PyNumberMethods.nb_long), this.GetFuncPtr(nameof(PyNumber_Long)));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), nameof(PyNumberMethods.nb_float), this.GetFuncPtr(nameof(PyNumber_Float)));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), nameof(PyNumberMethods.nb_multiply), this.GetFuncPtr(nameof(PyNumber_Multiply)));

            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_number), nmPtr);
        }

        private void
        AddNumberMethodsWithIndex(IntPtr typePtr)
        {
            this.AddNumberMethodsWithoutIndex(typePtr);
            IntPtr nmPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_as_number));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), nameof(PyNumberMethods.nb_index), this.GetFuncPtr(nameof(PyNumber_Index)));

            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags));
            flags |= Py_TPFLAGS.HAVE_INDEX;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags), (Int32)flags);
        }
    }
}
