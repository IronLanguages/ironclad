
all : ironclad stub testdata
	ipy runtests.py

ironclad :
	cd src && $(MAKE)

stub : 
	ipy tools/buildstub.py C:/WINDOWS/system32/python25.dll build overrides

testdata : 
	cd tests/data/src && $(MAKE)
