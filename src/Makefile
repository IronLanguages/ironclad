include ../Makefile.config

../build/ironclad/ironclad.dll : generatePython25Mapper Dispatcher.Generated.cs ../ironpython/*.dll *.cs
	$(CSC) /out:../build/ironclad/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronPython.Modules.dll /r:../ironpython/Microsoft.Scripting.dll /r:../ironpython/Microsoft.Scripting.Core.dll /nologo *.cs 

generatePython25Mapper :
	cd python25mapper_components && $(MAKE)

Dispatcher.Generated.cs : ../tools/* ../stub/_ignores
	cd .. && ipy tools/generatedispatcher.py  src

clean :
	$(RM) *.Generated.cs
	$(RM) ..\build\ironclad\ironclad.dll