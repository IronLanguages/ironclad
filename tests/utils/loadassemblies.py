import clr
import sys

clr.AddReferenceToFileAndPath("build/ironclad/ironclad.dll")
clr.AddReferenceToFileAndPath("tests/data/testutils.dll")

sys.path.insert(0, "ironpython")
clr.AddReferenceToFile("Microsoft.Scripting.dll")
clr.AddReferenceToFile("Microsoft.Scripting.Core.dll")
clr.AddReferenceToFile("IronPython.dll")
clr.AddReferenceToFile("IronPython.Modules.dll")
