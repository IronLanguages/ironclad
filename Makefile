
all : bin
	ipy runtests.py

bin : ironclad stubdll testdata

ironclad :
	cd src && $(MAKE)

stubdll : 
	cd stub && $(MAKE)

testdata : 
	cd tests/data/src && $(MAKE)

clean :
	cd src && $(MAKE) clean
	cd stub && $(MAKE) clean
	cd tests/data/src && $(MAKE) clean
