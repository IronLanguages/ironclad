from subprocess import PIPE, Popen
import sys
from textwrap import wrap

_, objectFile, symbolsFile = sys.argv

def read(filename):
    stream = file(filename)
    result = stream.read()
    stream.close()
    return result
    
try:
    output = Popen(["objdump", "-t", objectFile], stdout=PIPE).communicate()[0]
except WindowsError:
    print "Could not find objdump: Not checking stub.c.o"
    sys.exit(0)
allSymbols = set(line.split()[-1][1:] for line in output.splitlines() if line)
expectedSymbols = set(map(str.strip, read(symbolsFile).splitlines()))
missingSymbols = expectedSymbols - allSymbols

warningMsg = """\
Some symbols which aren't going to be implemented in C# are not implemented in C. This will cause LoadLibrary to fail... but not all the time"""

if missingSymbols != set([]):
    print
    print >>sys.stderr, warningMsg
    print 
    print "The following symbols are missing:"
    for symbol in sorted(missingSymbols):
	print "    ", symbol
    sys.exit(1)





