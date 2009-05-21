include ../../../Makefile.config

all : ../setvalue.pyd ../exportsymbols.dll ../fakepython25.dll


../setvalue.pyd : setvalue.o
	gcc $(CFLAGS) -shared -o ../setvalue.pyd setvalue.o

setvalue.o : setvalue.c
	gcc $(CFLAGS) -o setvalue.o -c setvalue.c


../exportsymbols.dll : exportsymbols.o
	gcc $(CFLAGS) -shared -o ../exportsymbols.dll exportsymbols.o

exportsymbols.o : exportsymbols.c
	gcc $(CFLAGS) -o exportsymbols.o -c exportsymbols.c


../fakepython25.dll : fakepython25.o
	gcc $(CFLAGS) -shared -o ../fakepython25.dll fakepython25.o

fakepython25.o : fakepython25.c
	gcc $(CFLAGS) -o fakepython25.o -c fakepython25.c


clean :
	$(RM) *.o
	$(RM) ..\setvalue.pyd
	$(RM) ..\exportsymbols.dll
	$(RM) ..\fakepython25.dll