all : ../Python25Mapper_exceptions.Generated.cs ../CodeSnippets_dispatcher.Generated.cs ../CodeSnippets_ihooks.Generated.cs ../CodeSnippets_kindaDictProxy.Generated.cs

../Python25Mapper_exceptions.Generated.cs : exceptions builtin_exceptions store_dispatch operator numbers_convert_c2py numbers_convert_py2c fill_types ../../tools/generatepython25mapper.py
	ipy ../../tools/generatepython25mapper.py

../CodeSnippets_dispatcher.Generated.cs: CodeSnippets_dispatcher.cs.src dispatcher.py ../../tools/insertfiles.py
	python ../../tools/insertfiles.py CodeSnippets_dispatcher.cs.src dispatcher.py > ../CodeSnippets_dispatcher.Generated.cs

../CodeSnippets_ihooks.Generated.cs: CodeSnippets_ihooks.cs.src import_code.py ../../tools/insertfiles.py
	python ../../tools/insertfiles.py CodeSnippets_ihooks.cs.src import_code.py > ../CodeSnippets_ihooks.Generated.cs

../CodeSnippets_kindaDictProxy.Generated.cs: CodeSnippets_kindaDictProxy.cs.src kindadictproxy.py ../../tools/insertfiles.py
	python ../../tools/insertfiles.py CodeSnippets_kindaDictProxy.cs.src kindadictproxy.py > ../CodeSnippets_kindaDictProxy.Generated.cs