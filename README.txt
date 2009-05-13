Ironclad currently only works on 32-bit Windows; support for other platforms is
expected in later releases.

To use ironclad, make sure that the 'build' directory (or wherever you have put
the ironclad package) is on your sys.path, and 'import ironclad' from IronPython
2.0. Once it has been imported, you should be able to import and (perhaps) use
any compiled CPython extensions accessible from your sys.path.

If you have any problems, please ask for help at
http://groups.google.com/group/c-extensions-for-ironpython

Notably, it should be possible to import and use most of NumPy 1.2 and an unknown 
proportion of SciPy 0.7; it's not as fast as it is on CPython (and some parts are 
unbelievably, hideously slow) but the benefits are generally still noticeable 
when working with sufficiently large datasets.

Similarly, parts of matplotlib now work: the 'ps' backend should work out of the
box, and the 'pdf' and 'svg' backends appear to work if you install zlib for 
IronPython.

TROUBLESHOOTING NOTE:

  If you encounter errors involving 'msvcp71.dll', it means that the MS C++ runtime
  is not on your PATH. To fix it, acquire a copy from somewhere, and drop it into
  '/build/ironclad/support'. Matplotlib uses this library and does not include its
  own copy, and other packages may do the same.

Slightly more detailed information, including development notes, is available in
the 'doc' directory.
