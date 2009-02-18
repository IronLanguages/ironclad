Ironclad currently only works on 32-bit Windows; support for other platforms is
expected in later releases.

To use ironclad, make sure that the 'build' directory (or wherever you have put
the ironclad package) is on your sys.path, and 'import ironclad' from IronPython
2.0. Once it has been imported, you should be able to import and (perhaps) use
any compiled CPython extensions accessible from your sys.path.

PLEASE NOTE: some extensions may require MSVCR71.dll or MSVCP71.dll; due to the 
somewhat murky legalities involved, we do not distribute these files. However, 
you almost certainly have a copy of each on your system somewhere, and you 
probably already have them on your PATH. If not, copying them into the same 
directory as the .pyd that needs them should make everything work. (According 
to MSDN, those files should be distributed with anything that needs to use them;
however, due to their ready availability, many developers are unaware of this 
requirement).

If you have any problems, please ask for help at
http://groups.google.com/group/c-extensions-for-ironpython

Notably, it should be possible to import and use most of NumPy 1.2 and an unknown 
proportion of SciPy 0.7; it's not as fast as it is on CPython (and some parts are 
unbelievably, hideously slow) but the benefits are generally still noticeable 
when working with sufficiently large datasets.

Similarly, parts of matplotlib now work: the 'ps' backend should work out of the
box, and the 'pdf' and 'svg' backends appear to work if you install zlib for 
IronPython. 

Slightly more detailed information is available in the 'doc' directory.