// IRONCLAD: only tiny fragments copied

/*

Unicode implementation based on original code by Fredrik Lundh,
modified by Marc-Andre Lemburg <mal@lemburg.com> according to the
Unicode Integration Proposal (see file Misc/unicode.txt).

Major speed upgrades to the method implementations at the Reykjavik
NeedForSpeed sprint, by Fredrik Lundh and Andrew Dalke.

Copyright (c) Corporation for National Research Initiatives.

--------------------------------------------------------------------
The original string type implementation is:

    Copyright (c) 1999 by Secret Labs AB
    Copyright (c) 1999 by Fredrik Lundh

By obtaining, using, and/or copying this software and/or its
associated documentation, you agree that you have read, understood,
and will comply with the following terms and conditions:

Permission to use, copy, modify, and distribute this software and its
associated documentation for any purpose and without fee is hereby
granted, provided that the above copyright notice appears in all
copies, and that both that copyright notice and this permission notice
appear in supporting documentation, and that the name of Secret Labs
AB or the author not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR
ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
--------------------------------------------------------------------

*/

#define PY_SSIZE_T_CLEAN

#ifdef __cplusplus
extern "C" {
#endif
static char unicode_default_encoding[100];

const char *PyUnicode_GetDefaultEncoding(void)
{
    return unicode_default_encoding;
}

int PyUnicode_SetDefaultEncoding(const char *encoding)
{
    PyObject *v;

    /* Make sure the encoding is valid. As side effect, this also
       loads the encoding into the codec registry cache. */
    v = _PyCodec_Lookup(encoding);
    if (v == NULL)
	goto onError;
    Py_DECREF(v);
    strncpy(unicode_default_encoding,
	    encoding,
	    sizeof(unicode_default_encoding));
    return 0;

 onError:
    return -1;
}

#ifdef __cplusplus
}
#endif

