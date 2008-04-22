../build/ironclad.dll : generatePythonMapper generatePython25Mapper *.cs ../ironpython/IronPython.dll ../ironpython/IronPython.Modules.dll ../ironpython/Microsoft.Scripting.dll
	csc /out:../build/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronPython.Modules.dll /r:../ironpython/Microsoft.Scripting.dll /nologo *.cs 

generatePythonMapper : 
	cd pythonmapper_components && $(MAKE)

generatePython25Mapper:
	cd python25mapper_components && $(MAKE)