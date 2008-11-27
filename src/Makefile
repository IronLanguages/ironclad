include ../Makefile.config

../build/ironclad.dll : generatePython25Api generatePython25Mapper CodeSnippets_ihooks.Generated.cs CodeSnippets_dispatcher.Generated.cs *.cs ../ironpython/IronPython.dll ../ironpython/IronPython.Modules.dll ../ironpython/Microsoft.Scripting.dll ../ironpython/Microsoft.Scripting.Core.dll
	$(CSC) /out:../build/ironclad.dll /t:library /r:../ironpython/IronPython.dll /r:../ironpython/IronPython.Modules.dll /r:../ironpython/Microsoft.Scripting.dll /r:../ironpython/Microsoft.Scripting.Core.dll /nologo *.cs 

generatePython25Api : 
	cd python25api_components && $(MAKE)

generatePython25Mapper:
	cd python25mapper_components && $(MAKE)

CodeSnippets_dispatcher.Generated.cs: CodeSnippets_dispatcher.cs.src dispatcher.py
	python ../tools/insertfiles.py CodeSnippets_dispatcher.cs.src dispatcher.py > CodeSnippets_dispatcher.Generated.cs

CodeSnippets_ihooks.Generated.cs: CodeSnippets_ihooks.cs.src import_code.py
	python ../tools/insertfiles.py CodeSnippets_ihooks.cs.src import_code.py > CodeSnippets_ihooks.Generated.cs