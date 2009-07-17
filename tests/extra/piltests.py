from glob import glob
import os
import shutil
from textwrap import dedent

from tests.utils.functionaltestcase import FunctionalTestCase
from tests.utils.runtest import automakesuite, run

FORMATS = 'gif', 'png', 'bmp', 'jpg'
SAMPLE_IMAGES = map(os.path.join("tests", "data", "test.").__add__, FORMATS)

# It might be possible to speed up these consistency tests by keeping around
# two interpreter processes and injecting commands into them (this should work)

def readBinary(filename):
    try:
        f = file(filename, 'rb')
        return f.read()
    finally:
        f.close()


IPY = 'ipy.exe'
PYTHON = 'python.exe'


class PILTest(FunctionalTestCase):

    TEMPLATE = dedent("""\
        import sys
        sys.path.insert(0, %r)
        import ironclad
        ironclad.patch_native_filenos()
        %%s
        """) % os.path.abspath("build")

    def setUp(self):
        FunctionalTestCase.setUp(self)
        for filename in SAMPLE_IMAGES:
            shutil.copy(filename, self.testDir)


    def assertSaveLoad(self, format):
        self.assertRuns(dedent("""
            import Image
            input = Image.open('test.%(fmt)s')
            input.save('output.%(fmt)s')
            output = Image.open('output.%(fmt)s')
            assert list(input.getdata()) == list(output.getdata()), 'saved image not identical to opened image'
            """ % {'fmt': format}))


    def assertConsistency(self, code):
        ironExitCode, ironOutput, ironError = self.runCode(code, IPY)
        pyExitCode, pyOutput, pyError = self.runCode(code, PYTHON)

        ironLines = ironOutput.splitlines()
        pyLines = pyOutput.splitlines()
        self.assertEquals(len(ironLines), len(pyLines), ">>>%s<<<\n>>>%s<<<" % (ironOutput, pyOutput))
        for ironLine, pyLine in zip(ironLines, pyLines):
            self.assertEquals(ironLine, pyLine, "%s != %s" %(ironLine, pyLine))


    def assertOperation(self, code, format):
        roots = 'output. ironOutput. pyOutput.'.split()
        tempOut, ironOut, pyOut = [os.path.join(self.testDir, name + format) for name in roots]
        self.runCode(code % dict(format=format), IPY)
        shutil.move(tempOut, ironOut)
        self.runCode(code % {'format':format}, PYTHON)
        shutil.move(tempOut, pyOut)
        self.assertEquals(readBinary(ironOut), readBinary(pyOut))


    def assertInformation(self, format):
        code = dedent("""
            import Image
            im = Image.open('test.%s')
            print 'FILENAME:', im.filename
            print 'SIZE:', im.size
            print 'FORMAT:', im.format
            print 'INFO:', sorted(im.info.items())
            print 'MODE:', im.mode
            print 'GETPIXEL:', im.getpixel((20, 30))
            print 
            """ % format)
        self.assertConsistency(code)


    def testSaveLoad(self):
        self.assertSaveLoad('gif')
        self.assertSaveLoad('png')
        self.assertSaveLoad('bmp')


    def testImageInformation(self):
        self.assertInformation('gif')
        self.assertInformation('bmp')
        self.assertInformation('png')


    def assertImageOp(self, op):
        code = dedent("""
            import Image
            Image.open('test.%%(format)s').%s.save('output.%%(format)s')""" % op)
        self.assertOperation(code, format="png")
        

    def testRotate(self):
        self.assertImageOp('rotate(37)')

        
    def testTransforms(self):
        self.assertImageOp('transform((50, 60), Image.EXTENT, (20, 30, 40, 50))')
        self.assertImageOp('transform((50, 60), Image.AFFINE, (1, 2, 2, -1, 20, 30))')
        self.assertImageOp('transform((100, 120), Image.QUAD, (10, 20, 5, 50, 50, 60, 40, 20))')


    def testOtherOps(self):
        self.assertImageOp('resize((400, 500), Image.NEAREST)')
        self.assertImageOp('resize((400, 500), Image.ANTIALIAS)')
        self.assertImageOp('transpose(Image.ROTATE_90)')
        self.assertImageOp('transpose(Image.FLIP_LEFT_RIGHT)')
        self.assertImageOp('transpose(Image.FLIP_TOP_BOTTOM)')
        self.assertImageOp('transpose(Image.ROTATE_180)')
        self.assertImageOp('transpose(Image.ROTATE_270)')
        # self.assertImageOp('crop((20, 30, 40, 50))')


    def testSplit(self):
        code = dedent("""
            import Image
            for i, im in enumerate(Image.open('test.bmp').split()):
                im.save('%s%%d.bmp' %% i)
        """)
        self.runCode(code % 'ironoutput', IPY)
        self.runCode(code % "pyoutput", PYTHON)
        for i, (actual, expected) in enumerate(zip(sorted(glob('ironoutput*')), sorted(glob('pyoutput*')))):
            self.assertEquals(readBinary(actual), readBinary(expected), i)



suite = automakesuite(locals())
if __name__ == "__main__":
    run(suite, 2)
