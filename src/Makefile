../build/ironclad.dll : generatePython25Api generatePython25Mapper *.cs ../ironpython/IronPython.dll ../ironpython/IronPython.Modules.dll ../ironpython/Microsoft.Scripting.dll ../ironpython/Microsoft.Scripting.Core.dll
	csc /out:../build/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronPython.Modules.dll /r:../ironpython/Microsoft.Scripting.dll /r:../ironpython/Microsoft.Scripting.Core.dll /nologo *.cs 

generatePython25Api : 
	cd python25api_components && $(MAKE)

generatePython25Mapper:
	cd python25mapper_components && $(MAKE)