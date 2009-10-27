
import os, sys

from tools.utils import read, write

from data.snippets.cs.codesnippets import *


def read_dir(src):
    def slurp(name):
        return {
            'name': name[:-3], 
            'code': read(src, name).replace('"', '""'),
        }
    snippets = []
    for name in os.listdir(src):
        if name.endswith('.py'):
            snippets.append(CODESNIPPET_TEMPLATE % slurp(name))
    return CODESNIPPETS_FILE_TEMPLATE % '\n\n'.join(snippets)


src, dst = sys.argv[1:]
write(dst, 'CodeSnippets.Generated.cs', read_dir(src), badge=True)
