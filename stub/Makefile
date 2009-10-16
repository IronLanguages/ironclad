include ../Makefile.config

ifeq ($(OS),windows)
	CFLAGS += -specs=use-msvcr90.spec
endif

COMPILE_IRONCLAD_FLAGS = -DPy_BUILD_CORE -DIRONCLAD


all: ../build/ironclad/python26.dll ../build/ironclad/ic_msvcr90.dll

../build/ironclad/python26.dll: stub.asm.o stub.c.o cpython.c.o depend-msvcr90.res
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/python26.dll stub.asm.o stub.c.o cpython.c.o depend-msvcr90.res

stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm

cpython.c.o: cpython.c Include/*.h Modules/*.c Objects/*.c Parser/*.c Python/*.c
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o cpython.c.o -c cpython.c -I Include

stub.c.o: generated Include/*.h Modules/*.c Objects/*.c Parser/*.c Python/*.c
	gcc $(CFLAGS) $(COMPILE_IRONCLAD_FLAGS) -o stub.c.o -c stubmain.c -I Include

generated: *.c _ordered_data _mgd_functions _ignore_symbols _extra_data
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .


../build/ironclad/ic_msvcr90.dll: ic_msvcr90.c.o depend-msvcr90.res
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/ic_msvcr90.dll ic_msvcr90.c.o depend-msvcr90.res

ic_msvcr90.c.o : ic_msvcr90.c
	gcc $(CFLAGS) -o ic_msvcr90.c.o -c ic_msvcr90.c


depend-msvcr90.res: depend-msvcr90.rc depend-msvcr90.manifest
	windres --input depend-msvcr90.rc --output depend-msvcr90.res --output-format=coff


clean:
	$(RM) depend-msvcr90.res
	$(RM) *.o stub.generated.*
	$(RM) ..\build\ironclad\python26.dll
	$(RM) ..\build\ironclad\ic_msvcr90.dll

