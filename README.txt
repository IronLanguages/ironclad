Ironclad currently only works on 32-bit Windows; support for other platforms is
expected in later releases.

To use ironclad, make sure that the 'build' directory (or wherever you have put
the ironclad package) is on your sys.path, and 'import ironclad' from IronPython
2.06. Once it has been imported, you should be able to import and (perhaps) use
any compiled CPython extensions accessible from your sys.path.

If you have any problems, please ask for help at
http://groups.google.com/group/c-extensions-for-ironpython

Notably, it should be possible to import and use most of NumPy 1.3 and SciPy 0.7; 
it's not as fast as it is on CPython (and some parts are unbelievably, hideously 
slow) but the benefits are generally still noticeable when working with 
sufficiently large datasets.

Slightly more detailed information, including build and development notes, is 
available in the 'doc' directory.
