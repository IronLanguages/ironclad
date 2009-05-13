include ../Makefile.config

../build/ironclad/ironclad.dll : generatePython25Mapper Dispatcher.Generated.cs *.cs
	$(CSC) /out:../build/ironclad/ironclad.dll /t:library /r:$(IPY_DIR)/IronPython.dll /r:$(IPY_DIR)/IronPython.Modules.dll /r:$(IPY_DIR)/Microsoft.Scripting.dll /r:$(IPY_DIR)/Microsoft.Scripting.Core.dll /nologo *.cs 

generatePython25Mapper :
	cd python25mapper_components && $(MAKE)

Dispatcher.Generated.cs : ../tools/* ../stub/_ignore_symbols
	cd .. && ipy tools/generatedispatcher.py  src

clean :
	$(RM) *.Generated.cs
	$(RM) ..\build\ironclad\ironclad.dll