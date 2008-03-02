
all : ironclad stubdll testdata
	ipy runtests.py

ironclad :
	cd src && $(MAKE)

stubdll : 
	cd stub && $(MAKE)

testdata : 
	cd tests/data/src && $(MAKE)
