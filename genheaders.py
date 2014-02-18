#!/usr/bin/env python
#
# Copyright (c) 2013-2014 The Khronos Group Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and/or associated documentation files (the
# "Materials"), to deal in the Materials without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Materials, and to
# permit persons to whom the Materials are furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Materials.
#
# THE MATERIALS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# MATERIALS OR THE USE OR OTHER DEALINGS IN THE MATERIALS.

import sys, time, pdb, string, cProfile
from reg import *

# debug - start header generation in debugger
# dump - dump registry after loading
# profile - enable Python profiling
# protect - whether to use #ifndef protections
# registry <filename> - use specified XML registry instead of gl.xml
# target - string name of target header, or all targets if None
# timeit - time length of registry loading & header generation
# validate - validate return & parameter group tags against <group>
debug   = False
dump    = False
profile = False
protect = True
target  = None
timeit  = False
validate= False
# Default input / log files
errFilename = None
diagFilename = 'diag.txt'
regFilename = 'gl.xml'

if __name__ == '__main__':
    i = 1
    while (i < len(sys.argv)):
        arg = sys.argv[i]
        i = i + 1
        if (arg == '-debug'):
            write('Enabling debug (-debug)', file=sys.stderr)
            debug = True
        elif (arg == '-dump'):
            write('Enabling dump (-dump)', file=sys.stderr)
            dump = True
        elif (arg == '-noprotect'):
            write('Disabling inclusion protection in output headers', file=sys.stderr)
            protect = False
        elif (arg == '-profile'):
            write('Enabling profiling (-profile)', file=sys.stderr)
            profile = True
        elif (arg == '-registry'):
            regFilename = sys.argv[i]
            i = i+1
            write('Using registry ', regFilename, file=sys.stderr)
        elif (arg == '-time'):
            write('Enabling timing (-time)', file=sys.stderr)
            timeit = True
        elif (arg == '-validate'):
            write('Enabling group validation (-validate)', file=sys.stderr)
            validate = True
        elif (arg[0:1] == '-'):
            write('Unrecognized argument:', arg, file=sys.stderr)
            exit(1)
        else:
            target = arg
            write('Using target', target, file=sys.stderr)

# Simple timer functions
startTime = None
def startTimer():
    global startTime
    startTime = time.clock()
def endTimer(msg):
    global startTime
    endTime = time.clock()
    if (timeit):
        write(msg, endTime - startTime)
        startTime = None

# Load & parse registry
reg = Registry()

startTimer()
tree = etree.parse(regFilename)
endTimer('Time to make ElementTree =')

startTimer()
reg.loadElementTree(tree)
endTimer('Time to parse ElementTree =')

if (validate):
    reg.validateGroups()

if (dump):
    write('***************************************')
    write('Performing Registry dump to regdump.txt')
    write('***************************************')
    reg.dumpReg(filehandle = open('regdump.txt','w'))

# Turn a list of strings into a regexp string matching exactly those strings
def makeREstring(list):
    return '^(' + '|'.join(list) + ')$'

# These are "mandatory" OpenGL ES 1 extensions, to
# be included in the core GLES/gl.h header.
es1CoreList = [
    'GL_OES_read_format',
    'GL_OES_compressed_paletted_texture',
    'GL_OES_point_size_array',
    'GL_OES_point_sprite'
]

# Descriptive names for various regexp patterns used to select
# versions and extensions

allVersions     = allExtensions = '.*'
noVersions      = noExtensions = None
gl12andLaterPat = '1\.[2-9]|[234]\.[0-9]'
gles2onlyPat    = '2\.[0-9]'
gles2and3Pat    = '[23]\.[0-9]'
es1CorePat      = makeREstring(es1CoreList)
# Extensions in old glcorearb.h but not yet tagged accordingly in gl.xml
glCoreARBPat    = None
glx13andLaterPat = '1\.[3-9]'

# Copyright text prefixing all headers (list of strings).
prefixStrings = [
    '/*',
    '** Copyright (c) 2013-2014 The Khronos Group Inc.',
    '**',
    '** Permission is hereby granted, free of charge, to any person obtaining a',
    '** copy of this software and/or associated documentation files (the',
    '** "Materials"), to deal in the Materials without restriction, including',
    '** without limitation the rights to use, copy, modify, merge, publish,',
    '** distribute, sublicense, and/or sell copies of the Materials, and to',
    '** permit persons to whom the Materials are furnished to do so, subject to',
    '** the following conditions:',
    '**',
    '** The above copyright notice and this permission notice shall be included',
    '** in all copies or substantial portions of the Materials.',
    '**',
    '** THE MATERIALS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,',
    '** EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF',
    '** MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.',
    '** IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY',
    '** CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,',
    '** TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE',
    '** MATERIALS OR THE USE OR OTHER DEALINGS IN THE MATERIALS.',
    '*/',
    '/*',
    '** This header is generated from the Khronos OpenGL / OpenGL ES XML',
    '** API Registry. The current version of the Registry, generator scripts',
    '** used to make the header, and the header can be found at',
    '**   http://www.opengl.org/registry/',
    '**',
    '** Khronos $' + 'Revision$ on $' + 'Date$',
    '*/',
    ''
]

# glext.h / glcorearb.h define calling conventions inline (no GL *platform.h)
glExtPlatformStrings = [
    '#if defined(_WIN32) && !defined(APIENTRY) && !defined(__CYGWIN__) && !defined(__SCITECH_SNAP__)',
    '#ifndef WIN32_LEAN_AND_MEAN',
    '#define WIN32_LEAN_AND_MEAN 1',
    '#endif',
    '#include <windows.h>',
    '#endif',
    '',
    '#ifndef APIENTRY',
    '#define APIENTRY',
    '#endif',
    '#ifndef APIENTRYP',
    '#define APIENTRYP APIENTRY *',
    '#endif',
    '#ifndef GLAPI',
    '#define GLAPI extern',
    '#endif',
    ''
]

glCorearbPlatformStrings = glExtPlatformStrings + [
    '/* glcorearb.h is for use with OpenGL core profile implementations.',
    '** It should should be placed in the same directory as gl.h and',
    '** included as <GL/glcorearb.h>.',
    '**',
    '** glcorearb.h includes only APIs in the latest OpenGL core profile',
    '** implementation together with APIs in newer ARB extensions which ',
    '** can be supported by the core profile. It does not, and never will',
    '** include functionality removed from the core profile, such as',
    '** fixed-function vertex and fragment processing.',
    '**',
    '** Do not #include both <GL/glcorearb.h> and either of <GL/gl.h> or',
    '** <GL/glext.h> in the same source file.',
    '*/',
    ''
]

# wglext.h needs Windows include
wglPlatformStrings = [
    '#if defined(_WIN32) && !defined(APIENTRY) && !defined(__CYGWIN__) && !defined(__SCITECH_SNAP__)',
    '#define WIN32_LEAN_AND_MEAN 1',
    '#include <windows.h>',
    '#endif',
    '',
]

# GLES 1/2/3 core .h have separate *platform.h files to define calling conventions
gles1PlatformStrings = [ '#include <GLES/glplatform.h>', '' ]
gles2PlatformStrings = [ '#include <GLES2/gl2platform.h>', '' ]
gles3PlatformStrings = [ '#include <GLES3/gl3platform.h>', '' ]
eglPlatformStrings   = [ '#include <EGL/eglplatform.h>', '' ]

# GLES 1/2 extension .h have small addition to calling convention headers
gles1ExtPlatformStrings = gles2ExtPlatformStrings = [
    '#ifndef GL_APIENTRYP',
    '#define GL_APIENTRYP GL_APIENTRY*',
    '#endif',
    ''
]

# Insert generation date in a comment for headers not having *GLEXT_VERSION macros
genDateCommentString = [
    format("/* Generated on date %s */" % time.strftime("%Y%m%d")),
    ''
]

# GL_GLEXT_VERSION is defined only in glext.h
glextVersionStrings = [
    format("#define GL_GLEXT_VERSION %s" % time.strftime("%Y%m%d")),
    ''
]
# WGL_WGLEXT_VERSION is defined only in wglext.h
wglextVersionStrings = [
    format("#define WGL_WGLEXT_VERSION %s" % time.strftime("%Y%m%d")),
    ''
]
# GLX_GLXEXT_VERSION is defined only in glxext.h
glxextVersionStrings = [
    format("#define GLX_GLXEXT_VERSION %s" % time.strftime("%Y%m%d")),
    ''
]
# EGL_EGLEXT_VERSION is defined only in eglext.h
eglextVersionStrings = [
    format("#define EGL_EGLEXT_VERSION %s" % time.strftime("%Y%m%d")),
    ''
]

# Defaults for generating re-inclusion protection wrappers (or not)
protectFile = protect
protectFeature = protect
protectProto = protect

buildList = [
    # GL API 1.2+ + extensions - GL/glext.h
    CGeneratorOptions(
        filename          = 'GL/glext.h',
        apiname           = 'gl',
        profile           = 'compatibility',
        versions          = allVersions,
        emitversions      = gl12andLaterPat,
        defaultExtensions = 'gl',                   # Default extensions for GL
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + glExtPlatformStrings + glextVersionStrings,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GLAPI ',
        apientry          = 'APIENTRY ',
        apientryp         = 'APIENTRYP '),
    # GL core profile + extensions - GL/glcorearb.h
    CGeneratorOptions(
        filename          = 'GL/glcorearb.h',
        apiname           = 'gl',
        profile           = 'core',
        versions          = allVersions,
        emitversions      = allVersions,
        defaultExtensions = 'glcore',               # Default extensions for GL core profile (only)
        addExtensions     = glCoreARBPat,
        removeExtensions  = None,
        prefixText        = prefixStrings + glCorearbPlatformStrings,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GLAPI ',
        apientry          = 'APIENTRY ',
        apientryp         = 'APIENTRYP '),
    # GLES 1.x API + mandatory extensions - GLES/gl.h (no function pointers)
    CGeneratorOptions(
        filename          = 'GLES/gl.h',
        apiname           = 'gles1',
        profile           = 'common',
        versions          = allVersions,
        emitversions      = allVersions,
        defaultExtensions = None,                   # No default extensions
        addExtensions     = es1CorePat,             # Add mandatory ES1 extensions in GLES1/gl.h
        removeExtensions  = None,
        prefixText        = prefixStrings + gles1PlatformStrings + genDateCommentString,
        genFuncPointers   = False,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = False,                  # Core ES API functions are in the static link libraries
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GL_API ',
        apientry          = 'GL_APIENTRY ',
        apientryp         = 'GL_APIENTRYP '),
    # GLES 1.x extensions - GLES/glext.h
    CGeneratorOptions(
        filename          = 'GLES/glext.h',
        apiname           = 'gles1',
        profile           = 'common',
        versions          = allVersions,
        emitversions      = noVersions,
        defaultExtensions = 'gles1',                # Default extensions for GLES 1
        addExtensions     = None,
        removeExtensions  = es1CorePat,             # Remove mandatory ES1 extensions in GLES1/glext.h
        prefixText        = prefixStrings + gles1ExtPlatformStrings + genDateCommentString,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GL_API ',
        apientry          = 'GL_APIENTRY ',
        apientryp         = 'GL_APIENTRYP '),
    # GLES 2.0 API - GLES2/gl2.h (no function pointers)
    CGeneratorOptions(
        filename          = 'GLES2/gl2.h',
        apiname           = 'gles2',
        profile           = 'common',
        versions          = gles2onlyPat,
        emitversions      = allVersions,
        defaultExtensions = None,                   # No default extensions
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + gles2PlatformStrings + genDateCommentString,
        genFuncPointers   = False,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = False,                  # Core ES API functions are in the static link libraries
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GL_APICALL ',
        apientry          = 'GL_APIENTRY ',
        apientryp         = 'GL_APIENTRYP '),
    # GLES 2.0 extensions - GLES2/gl2ext.h
    CGeneratorOptions(
        filename          = 'GLES2/gl2ext.h',
        apiname           = 'gles2',
        profile           = 'common',
        versions          = gles2onlyPat,
        emitversions      = None,
        defaultExtensions = 'gles2',                # Default extensions for GLES 2
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + gles2ExtPlatformStrings + genDateCommentString,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GL_APICALL ',
        apientry          = 'GL_APIENTRY ',
        apientryp         = 'GL_APIENTRYP '),
    # GLES 3.0 API - GLES3/gl3.h (no function pointers)
    CGeneratorOptions(
        filename          = 'GLES3/gl3.h',
        apiname           = 'gles2',
        profile           = 'common',
        versions          = gles2and3Pat,
        emitversions      = allVersions,
        defaultExtensions = None,                   # No default extensions
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + gles3PlatformStrings + genDateCommentString,
        genFuncPointers   = False,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = False,                  # Core ES API functions are in the static link libraries
        protectProtoStr   = 'GL_GLEXT_PROTOTYPES',
        apicall           = 'GL_APICALL ',
        apientry          = 'GL_APIENTRY ',
        apientryp         = 'GL_APIENTRYP '),
    # EGL API - EGL/egl.h (no function pointers, yet @@@)
    CGeneratorOptions(
        filename          = 'EGL/egl.h',
        apiname           = 'egl',
        profile           = None,
        versions          = allVersions,
        emitversions      = allVersions,
        defaultExtensions = None,                   # No default extensions
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + eglPlatformStrings + genDateCommentString,
        genFuncPointers   = False,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = False,
        protectProtoStr   = 'EGL_EGLEXT_PROTOTYPES',
        apicall           = 'EGLAPI ',
        apientry          = 'EGLAPIENTRY ',
        apientryp         = 'EGLAPIENTRYP '),
    # EGL extensions - EGL/eglext.h (no function pointers, yet @@@)
    CGeneratorOptions(
        filename          = 'EGL/eglext.h',
        apiname           = 'egl',
        profile           = None,
        versions          = allVersions,
        emitversions      = None,
        defaultExtensions = 'egl',                  # Default extensions for EGL
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + eglPlatformStrings + eglextVersionStrings,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'EGL_EGLEXT_PROTOTYPES',
        apicall           = 'EGLAPI ',
        apientry          = 'EGLAPIENTRY ',
        apientryp         = 'EGLAPIENTRYP '),
    # GLX 1.* API - GL/glx.h
    CGeneratorOptions(
        filename          = 'GL/glx.h',
        apiname           = 'glx',
        profile           = None,
        versions          = allVersions,
        emitversions      = allVersions,
        defaultExtensions = None,                   # No default extensions
        addExtensions     = None,
        removeExtensions  = None,
        # add glXPlatformStrings?
        prefixText        = prefixStrings + genDateCommentString,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'GLX_GLXEXT_PROTOTYPES',
        apicall           = '',
        apientry          = '',
        apientryp         = ' *'),
    # GLX 1.3+ API + extensions - GL/glxext.h (no function pointers, yet @@@)
    CGeneratorOptions(
        filename          = 'GL/glxext.h',
        apiname           = 'glx',
        profile           = None,
        versions          = allVersions,
        emitversions      = glx13andLaterPat,
        defaultExtensions = 'glx',                  # Default extensions for GLX
        addExtensions     = None,
        removeExtensions  = None,
        # add glXPlatformStrings?
        prefixText        = prefixStrings + glxextVersionStrings,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'GLX_GLXEXT_PROTOTYPES',
        apicall           = '',
        apientry          = '',
        apientryp         = ' *'),
    # WGL API + extensions - GL/wgl.h (no function pointers, yet @@@)
    CGeneratorOptions(
        filename          = 'GL/wgl.h',
        apiname           = 'wgl',
        profile           = None,
        versions          = allVersions,
        emitversions      = allVersions,
        defaultExtensions = 'wgl',                  # Default extensions for WGL
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + wglPlatformStrings + genDateCommentString,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'WGL_WGLEXT_PROTOTYPES',
        apicall           = '',
        apientry          = 'WINAPI ',
        apientryp         = 'WINAPI * '),
    # WGL extensions - GL/wglext.h (no function pointers, yet @@@)
    CGeneratorOptions(
        filename          = 'GL/wglext.h',
        apiname           = 'wgl',
        profile           = None,
        versions          = allVersions,
        emitversions      = None,
        defaultExtensions = 'wgl',                  # Default extensions for WGL
        addExtensions     = None,
        removeExtensions  = None,
        prefixText        = prefixStrings + wglPlatformStrings + wglextVersionStrings,
        genFuncPointers   = True,
        protectFile       = protectFile,
        protectFeature    = protectFeature,
        protectProto      = protectProto,
        protectProtoStr   = 'WGL_WGLEXT_PROTOTYPES',
        apicall           = '',
        apientry          = 'WINAPI ',
        apientryp         = 'WINAPI * '),
    # End of list
    None
]

# create error/warning & diagnostic files
if (errFilename):
    errWarn = open(errFilename,'w')
else:
    errWarn = sys.stderr
diag = open(diagFilename, 'w')

def genHeaders():
    # Loop over targets, building each
    generated = 0
    for genOpts in buildList:
        if (genOpts == None):
            break
        if (target and target != genOpts.filename):
            # write('*** Skipping', genOpts.filename)
            continue
        write('*** Building', genOpts.filename)
        generated = generated + 1
        startTimer()
        gen = COutputGenerator(errFile=errWarn,
                               warnFile=errWarn,
                               diagFile=diag)
        reg.setGenerator(gen)
        reg.apiGen(genOpts)
        write('** Generated', genOpts.filename)
        endTimer('Time to generate ' + genOpts.filename + ' =')
    if (target and generated == 0):
        write('Failed to generate target:', target)

if (debug):
    pdb.run('genHeaders()')
elif (profile):
    import cProfile, pstats
    cProfile.run('genHeaders()', 'profile.txt')
    p = pstats.Stats('profile.txt')
    p.strip_dirs().sort_stats('time').print_stats(50)
else:
    genHeaders()
