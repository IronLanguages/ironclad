include ../../../Makefile.config

all : ../setvalue.pyd ../exportsymbols.dll ../fakepython25.dll ../implicit-load-msvcr90.dll


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


../implicit-load-msvcr90.dll : empty.o
	gcc $(CFLAGS) -shared -o ../implicit-load-msvcr90.dll empty.o
	mt -manifest ..\..\..\stub\depend-msvcr90.manifest -outputresource:..\implicit-load-msvcr90.dll;2 -nologo

empty.o : empty.c
	gcc $(CFLAGS) -o empty.o -c empty.c
	


clean :
	$(RM) *.o
	$(RM) ..\setvalue.pyd
	$(RM) ..\exportsymbols.dll
	$(RM) ..\fakepython25.dll
	$(RM) ..\implicit-load-msvcr90.dll