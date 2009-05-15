include ../../../Makefile.config

all : ../setvalue.pyd ../exportsymbols.dll

../setvalue.pyd : setvalue.o
	gcc $(CFLAGS) -shared -o ../setvalue.pyd setvalue.o

setvalue.o : setvalue.c
	gcc $(CFLAGS) -o setvalue.o -c setvalue.c

../exportsymbols.dll : exportsymbols.o
	gcc $(CFLAGS) -shared -o ../exportsymbols.dll exportsymbols.o

exportsymbols.o : exportsymbols.c
	gcc $(CFLAGS) -o exportsymbols.o -c exportsymbols.c

clean :
	$(RM) *.o
	$(RM) ..\setvalue.pyd
	$(RM) ..\exportsymbols.dll