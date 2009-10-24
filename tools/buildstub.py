
import os
import sys

from stubmaker import StubMaker


def write(dir_, name, contents):
    f = open(os.path.join(dir_, name), "w")
    try:
        f.write(contents)
    finally:
        f.close()


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(1)

    sourceDll = sys.argv[1]
    outputDir = sys.argv[2]
    outputIncludeDir = os.path.join(outputDir, 'Include')
    
    overrideDir = None
    if len(sys.argv) == 4:
        overrideDir = sys.argv[3]

    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    if not os.path.exists(outputIncludeDir):
        os.mkdir(outputIncludeDir)

    sm = StubMaker(sourceDll, overrideDir)
    write(outputDir, "stubinit.generated.c", sm.generate_c())
    write(outputDir, "jumps.generated.asm", sm.generate_asm())
    write(outputIncludeDir, "_mgd_function_prototypes.generated.h", sm.generate_header())


if __name__ == "__main__":
    main()
