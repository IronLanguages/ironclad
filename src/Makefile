../build/ironclad.dll : generatePythonMapper generatePython25Mapper *.cs ../ironpython/IronPython.dll ../ironpython/IronMath.dll 
	csc /out:../build/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronMath.dll /nologo *.cs 

generatePythonMapper : 
	cd pythonmapper_components && $(MAKE)

generatePython25Mapper:
	cd python25mapper_components && $(MAKE)