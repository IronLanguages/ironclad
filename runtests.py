import os
import clr
import unittest

clr.AddReferenceToFile("build/jumpy.dll")
clr.AddReference("IronPython.dll")
clr.AddReference("IronMath.dll")

suite = unittest.TestSuite()
for f in os.listdir("tests"):
    if f.endswith("test.py"):
        name = f[:-3]
        try:
            m = __import__("tests.%s" % name)
            suite.addTest(getattr(m, name).suite)
        except:
            pass

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)