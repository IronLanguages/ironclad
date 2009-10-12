Ironclad needs an updated import library for msvcr90 -- the one distributed
with MinGW doesn't work. Assuming you have the correct version of msvcr90
installed, 'make patch' in this directory will move it aside and replace it 
with one generated from your installed version; make unpatch will restore
the original.

Don't make patch if you're patched; don't make unpatch if you're unpatched.