include ../Makefile.config

ifeq ($(OS),windows)
	CFLAGS += -specs=use-msvcr90.spec
endif

all: ../build/ironclad/python26.dll ../build/ironclad/ic_msvcr90.dll

../build/ironclad/python26.dll: stub.asm.o stub.c.o depend-msvcr90.manifest
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/python26.dll stub.asm.o stub.c.o
	mt -manifest depend-msvcr90.manifest -outputresource:..\build\ironclad\python26.dll;2 -nologo

stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm

stub.c.o: generated Include/*.h Modules/*.c Objects/*.c Parser/*.c Python/*.c
	gcc $(CFLAGS) -o stub.c.o -c stubmain.c -I Include

generated: *.c _ordered_data _mgd_functions _ignore_symbols _extra_data
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .


../build/ironclad/ic_msvcr90.dll: ic_msvcr90.c.o
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/ic_msvcr90.dll ic_msvcr90.c.o
	mt -manifest depend-msvcr90.manifest -outputresource:..\build\ironclad\ic_msvcr90.dll;2 -nologo

ic_msvcr90.c.o : ic_msvcr90.c
	gcc $(CFLAGS) -o ic_msvcr90.c.o -c ic_msvcr90.c


clean:
	$(RM) *.o stub.generated.*
	$(RM) ..\build\ironclad\python26.dll
	$(RM) ..\build\ironclad\ic_msvcr90.dll
