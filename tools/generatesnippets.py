
import os, sys

from data.snippets.cs.codesnippets import *

from tools.utils.io import read, write


#==========================================================================

def read_dir(src):
    def read_snippet(name):
        return {
            'name': name[:-3], 
            'code': read(src, name).replace('"', '""'),
        }
    snippets = []
    for name in os.listdir(src):
        if name.endswith('.py'):
            snippets.append(CODESNIPPET_TEMPLATE % read_snippet(name))
    return CODESNIPPETS_FILE_TEMPLATE % '\n\n'.join(snippets)


#==========================================================================

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    code = read_dir(src)
    
    write(dst, 'CodeSnippets.Generated.cs', code, badge=True)
