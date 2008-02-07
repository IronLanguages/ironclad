
all : jumpy stub testdata
	ipy runtests.py

jumpy :
	cd src && $(MAKE)

stub : 
	ipy tools/buildstub.py C:/WINDOWS/system32/python25.dll build overrides

testdata : 
	cd tests/data/src && $(MAKE)
