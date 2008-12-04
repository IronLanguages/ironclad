include ../Makefile.config

../build/ironclad.dll : generatePython25Api generatePython25Mapper ../ironpython/*.dll *.cs
	$(CSC) /out:../build/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronPython.Modules.dll /r:../ironpython/Microsoft.Scripting.dll /r:../ironpython/Microsoft.Scripting.Core.dll /nologo *.cs 

generatePython25Api : 
	cd python25api_components && $(MAKE)

generatePython25Mapper :
	cd python25mapper_components && $(MAKE)

clean :
	del *.Generated.cs
	del ..\build\ironclad.dll