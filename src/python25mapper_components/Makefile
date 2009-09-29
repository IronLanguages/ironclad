all : ../Python25Mapper_exceptions.Generated.cs ../CodeSnippets_ihooks.Generated.cs ../CodeSnippets_kindaDictProxy.Generated.cs ../CodeSnippets_kindaSeqIter.Generated.cs

../Python25Mapper_exceptions.Generated.cs : exceptions store_dispatch operator numbers_convert_c2py numbers_convert_py2c fill_types ../../tools/generatepython25mapper.py
	ipy ../../tools/generatepython25mapper.py

../CodeSnippets_ihooks.Generated.cs: CodeSnippets_ihooks.cs.src import_code.py ../../tools/insertfiles.py
	python ../../tools/insertfiles.py CodeSnippets_ihooks.cs.src import_code.py > ../CodeSnippets_ihooks.Generated.cs

../CodeSnippets_kindaDictProxy.Generated.cs: CodeSnippets_kindaDictProxy.cs.src kindadictproxy.py ../../tools/insertfiles.py
	python ../../tools/insertfiles.py CodeSnippets_kindaDictProxy.cs.src kindadictproxy.py > ../CodeSnippets_kindaDictProxy.Generated.cs

../CodeSnippets_kindaSeqIter.Generated.cs: CodeSnippets_kindaSeqIter.cs.src kindaseqiter.py ../../tools/insertfiles.py
	python ../../tools/insertfiles.py CodeSnippets_kindaSeqIter.cs.src kindaseqiter.py > ../CodeSnippets_kindaSeqIter.Generated.cs