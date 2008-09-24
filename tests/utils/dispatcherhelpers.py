from System import IntPtr

class EvilHackDict(dict):
    def __hash__(self):
        return 1

NULL = object()
NULL_PTR = IntPtr.Zero
OBJ = object()
OBJ_PTR = IntPtr(123)

NAME = '<test_name>'
RESULT = object()
RESULT_PTR = IntPtr(999)
RESULT_INT = 123
RESULT_SSIZE = 99999

TYPE_PTR = IntPtr(111)
INSTANCE_PTR = IntPtr(222)
ARGS = (1, 2, 3)
ARGS_PTR = IntPtr(333)
KWARGS = EvilHackDict({"1": 2, "3": 4})
KWARGS_PTR = IntPtr(444)
ARG = object()
ARG_PTR = IntPtr(555)
ARG2 = object()
ARG2_PTR = IntPtr(666)
ARG3 = object()
ARG3_PTR = IntPtr(777)

CLOSURE = IntPtr(888)
SSIZE = 123456
SSIZE2 = 789012

SIZE = 32
OFFSET = 16

PTRMAP = {
    OBJ: OBJ_PTR,
    ARGS: ARGS_PTR,
    KWARGS: KWARGS_PTR,
    ARG: ARG_PTR,
    ARG2: ARG2_PTR,
    ARG3: ARG3_PTR,
    RESULT: RESULT_PTR
}
PTRMAP.update(dict(((v,k) for (k,v) in PTRMAP.items())))