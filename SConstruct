# Script to build Ironclad out-of-source
#
# It can build several (or all) configuration/framework/platform combinations in one invocation.
# The final build output is placed in directory 'out/«configuration»/«framework»'.
# Intermediate build artifacts are placed in 'build/«configuration»/«framework»'.
# To see info on all supported build variables, options,
# and where the artifacts for the current build(s) are placed use:
# scons -h

import os

if os.name == 'nt':
    supported_frameworks = ['net462', 'net6.0']
else:
    supported_frameworks = ['net6.0']

vars = Variables(None, ARGUMENTS)
vars.Add(ListVariable('configuration', help='build configuration', default='release', names=['release', 'debug']))
vars.Add(ListVariable('framework', help='.NET platform to target', default=supported_frameworks[0], names=supported_frameworks))
vars.Add(BoolVariable('use_msvc1600', help='Set to use MSVC v16.0 in place of Clang', default=False))

env = Environment(variables=vars)
unknown = vars.UnknownVariables()
if unknown:
    print("Unknown variables: %s" % " ".join(unknown.keys()))
    print("For help, run: scons -h")
    Exit(1)
Help(vars.GenerateHelpText(env))
USE_MSVC1600 = env['use_msvc1600']

OUT_DIR_ROOT = 'out'            # for build output (final) artifacts
BUILD_DIR_ROOT = 'build'        # for intermediate build artifacts


for MODE in env['configuration'].data:
    for FMWK in env['framework'].data:
        TARGET_PATH = os.path.join(MODE, FMWK)
        BUILD_DIR = os.path.join(BUILD_DIR_ROOT, TARGET_PATH)
        OUT_DIR = os.path.join(OUT_DIR_ROOT, TARGET_PATH)
        Help(f"\nOut dir: {OUT_DIR}\n")
        Help(f"Build dir: {BUILD_DIR}\n")
        SConscript('main.scons', variant_dir=BUILD_DIR, duplicate=True, exports='MODE FMWK USE_MSVC1600 OUT_DIR')