
OVERVIEW

Ironclad's purpose is to allow IronPython to transparently import and use
compiled CPython extensions.

Ironclad is an IronPython package with a pleasingly simple interface: just
'import ironclad' to activate support for extensions built against Python 2.6.

Currently, this only works on 32-bit Windows, but I am actively working to 
abstract away platform dependencies.


IMPORTANT

If you plan to work heavily with files, or want to use the (builtin) mmap
module, I suggest you call ironclad.patch_native_filenos() after importing
ironclad. This patches IronPython's built-in file handling as best it can;
the effect should be that everything transparently Just Works. If you need
finer-grained control, use ironclad.open or ironclad.file to create native 
CPython files -- which will have correct values for fileno -- and use the 
functions in the (builtin) posix module to do things with filenos.


STATUS

* BioPython probably largely works or nearly works, but I haven't kept up on 
  compatibility there, so I don't actually know: the tests don't play very 
  nicely at the moment, but last time I checked a surprising amount of
  functionality was accessible.

* bz2, as shipped with Python 2.6, will import; homegrown tests reliably
  pass (the official test suite appears to be annoyingly platform-specific).

* csv, as shipped with Python 2.6, will import; the official test suite 
  contains 76 tests, of which 7 error and 1 fails. Some of the problems look
  pretty inconsequential, but there are a few real problems in specific cases.

* h5py 1.2.1 will import if ipy is run with -X:Frames, and most individual tests
  will run without problems.
  
  Sadly, threading issues (which cause pretty regular deadlocks) mean I cannot 
  recommend its use in production code; if you want to use it, try building a 
  thread-safe HDF5, and then build h5py against that HDF5. If you can do that, 
  try rebuilding h5py with PHIL deactivated; if that then works, please contact 
  h5py at alfven dot org and inform him that his suppositions are correct, and 
  that it would be awesome if he were to follow the same strategy for future 
  releases of h5py.

* matplotlib doesn't work, because the C extension modules have the wrong 
  manifests. You should be able to work around this by building your own ipy
  with a manifest containing the <dependency> in stub/depend-msvcr90.manifest.

* numpy 1.3.0 will import if ipy is run with -X:Frames. Of the 
  1704 tests we run, 143 error and 16 fail. Notable issues follow:
  
  * There is no Unicode support whatsoever: ~90 of the errors are caused
    by attempts to call PyObject_Unicode.
  * ~20 tests error out on tearDown when they try to unlink temp files
    that aren't actually closed yet (because ipy doesn't use refcounting).
  * Some things fail or error in entirely trivial and uninteresting ways
    (e or E in float printing, for example).
  * Several errors and failures still represent real problems.

* numpy 1.4.0RC1 will import if ipy is run with -X:Frames. Of the 
  2160 tests we run, 182 error and 50 fail. Haven't investigated issues in 
  any detail.

* PIL doesn't work, because ipy 2.6 can't parse Image.py. When that's fixed, most
  of it will probably work (although it's hard to tell because it doesn't come 
  with tests).

* scipy 0.7.1 will happily import if ipy is run with -X:FullFrames. Of the
  2484 tests we run, 127 error and 19 fail. Notable issues follow:
  
  * Several tests are blacklisted because they're tediously slow.
  * One test file is blacklisted because it (can) fail hard enough to take
    the process down.
  * There's some weirdness whereby scipy.factorial magically comes to exist
    when the whole suite is run, but certain packages can't be tested on 
    their own because they can't import it.
  * Most of the errors and failures still represent real problems.

* Lots of other things probably work; if you're interested in something not listed
  here, please try it out and let me know how it goes.


BUILDING

See doc/build.txt


HACKING

See doc/details.txt


CONTACT

Ironclad lives at http://code.google.com/p/ironclad/

Ask questions at http://groups.google.com/group/c-extensions-for-ironpython

Report bugs at http://code.google.com/p/ironclad/issues/list
