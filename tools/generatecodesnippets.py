
from tools.utils.io import ALL_FILES, run_generator
from tools.utils.codesnippetsgen import CodeSnippetsGenerator


#==========================================================================

INPUTS = ALL_FILES

OUTPUTS = (
    ('CodeSnippets.Generated.cs',   'CODESNIPPETS'),
)

if __name__ == '__main__':
    run_generator(CodeSnippetsGenerator, INPUTS, OUTPUTS)


#==========================================================================
