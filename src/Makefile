../build/ironclad.dll : generatePythonMapper *.cs ../ironpython/IronPython.dll ../ironpython/IronMath.dll 
	csc /out:../build/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronMath.dll /nologo *.cs 

generatePythonMapper : 
	cd pythonmapper_components && $(MAKE)