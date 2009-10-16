include ../Makefile.config

ifeq ($(OS),windows)
	CFLAGS += -specs=use-msvcr90.spec
endif

COMPILE_IRONCLAD_FLAGS = -DPy_BUILD_CORE -DIRONCLAD -I Include

CPY_OBJS = \
    Modules/_csv.c.o \
    Modules/gcmodule.c.o \
    Modules/mmapmodule.c.o \
    Modules/posixmodule.c.o \
    Objects/abstract.c.o \
    Objects/bufferobject.c.o \
    Objects/cobject.c.o \
    Objects/fileobject.c.o \
    Objects/listobject.c.o \
    Objects/longobject.c.o \
    Objects/methodobject.c.o \
    Objects/object.c.o \
    Objects/stringobject.c.o \
    Objects/structseq.c.o \
    Objects/tupleobject.c.o \
    Objects/unicodeobject.c.o \
    Parser/intrcheck.c.o \
    Parser/tokenizer.c.o \
    Python/ceval.c.o \
    Python/errors.c.o \
    Python/getargs.c.o \
    Python/modsupport.c.o \
    Python/mysnprintf.c.o \
    Python/mystrtoul.c.o \
    Python/pystate.c.o \
    Python/pystrtod.c.o \
    Python/sigcheck.c.o \



all: ../build/ironclad/python26.dll ../build/ironclad/ic_msvcr90.dll

../build/ironclad/python26.dll: stub.asm.o stub.c.o $(CPY_OBJS) depend-msvcr90.res
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/python26.dll stub.asm.o stub.c.o $(CPY_OBJS) depend-msvcr90.res

stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm

stub.c.o: generated Include/*.h
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o stub.c.o -c stubmain.c -I Include

generated: *.c _ordered_data _mgd_functions _ignore_symbols _extra_data
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .

Modules/%.c.o: Modules/%.c
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o $@ -c $^

Objects/%.c.o: Objects/%.c
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o $@ -c $^

Parser/%.c.o: Parser/%.c
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o $@ -c $^

Python/%.c.o: Python/%.c
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o $@ -c $^


../build/ironclad/ic_msvcr90.dll: ic_msvcr90.c.o depend-msvcr90.res
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/ic_msvcr90.dll ic_msvcr90.c.o depend-msvcr90.res

ic_msvcr90.c.o : ic_msvcr90.c
	gcc $(CFLAGS) -o ic_msvcr90.c.o -c ic_msvcr90.c


depend-msvcr90.res: depend-msvcr90.rc depend-msvcr90.manifest
	windres --input depend-msvcr90.rc --output depend-msvcr90.res --output-format=coff


clean:
	$(RM) ..\build\ironclad\python26.dll
	$(RM) ..\build\ironclad\ic_msvcr90.dll
	$(RM) depend-msvcr90.res
	$(RM) *.o stub.generated.*
	$(RM) Modules\*.o
	$(RM) Objects\*.o
	$(RM) Parser\*.o
	$(RM) Python\*.o

