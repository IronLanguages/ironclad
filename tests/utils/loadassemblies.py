import clr
clr.AddReferenceToFileAndPath("build/ironclad/ironclad.dll")

# If we ever completely unload msvcr90.dll, we get weird explosions next time we try to
# load it. This is surely my fault, and it would be nice to make it work 'properly', but
# for now this hack suffices; it shouldn't be an issue in real use because you shouldn't
# be repeatedly creating Mappers.

# On platforms where this is not necessary, please implement LoadLibrary such that it 
# doesn't explode when this file is not found.

from Ironclad import Unmanaged
Unmanaged.LoadLibrary("tests\data\implicit-load-msvcr90.dll")