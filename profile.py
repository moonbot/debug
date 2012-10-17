#!/usr/bin/env python
# encoding: utf-8
"""
debug:profile

Created by Brennan Chapman on 2012-10-04.
Copyright (c) 2012 Moonbot Studios. All rights reserved.

Set of profiling tools to assist in optimizing python scripts
"""
import cProfile
import logging
import os, sys, time
import pstats
import subprocess
import gprof2dot

LOG = logging.getLogger(__name__)

default_dotExecPath = {
    'windows':'C:\\Program Files (x86)\\Graphviz 2.28\\bin\\dot.exe',
    'mac':"/usr/local/bin/dot",
}

def quoteForPOSIX(string):
    '''quote a string so it can be used as an argument in a  posix shell

       According to: http://www.unix.org/single_unix_specification/
          2.2.1 Escape Character (Backslash)

          A backslash that is not quoted shall preserve the literal value
          of the following character, with the exception of a <newline>.

          2.2.2 Single-Quotes

          Enclosing characters in single-quotes ( '' ) shall preserve
          the literal value of each character within the single-quotes.
          A single-quote cannot occur within single-quotes.

    '''
    return "\\'".join("'" + p + "'" for p in string.split("'"))

def getTempFile(name):
    ''' Return a temp file path with the supplied extension '''
    tmp = None
    if os.environ.has_key('TMP'):
        tmp = os.environ['TMP']
    elif os.environ.has_key('TMPDIR'):
        tmp = os.environ['TMPDIR']
    else:
        tmp = os.path.expanduser('~')
    tmpFile = os.path.join(tmp, name)
    return tmpFile

def createDotMap(cmd, outputImage=None, outputProfile=None, dotExec=None, openImage=False, showStack=False, **kwargs):
    '''
    Profile the execution of a command and create a dot map using gprof2dot
    Command should be exactly what the normal code would be in string form
        Ex:
            doSomething(with, this)
            =
            crateDotMap("doSomething(with, this)", "test.png")
    You can pass TMP fo
    '''
    # Setup Paths
    outputImagePath = _cleanPath(outputImage)
    if dotExec is None:
        print "loading dotExec"
        dotExec = _getDotExecPath()
    if dotExec is None or not os.path.exists(dotExec):
        LOG.error("Graphviz not found. Please supply the path to dot executable")
        if dotExec:
            LOG.error("Path: {0}".format(dotExec))
        return
    if outputProfile:
        outputProfilePath = _cleanPath(outputProfile)
    else:
        outputProfilePath = "{0}.profile".format(os.path.splitext(outputImagePath)[0])
    
    # Create the profile
    kwargs = {
        'outputFile':outputProfilePath,
        'cmd':cmd,
        'frameDepth':1,
    }
    totalTime = createProfile(**kwargs)

    # Create the gprof configuration
    gProfOutputPath = "{0}.gprofdot".format(os.path.splitext(outputImagePath)[0])
    if showStack:
        import traceback
        label = "\"{0}\"".format("\n".join(traceback.format_stack()))
    else:
        label = "{0} | Total Time: {1}".format(cmd, totalTime)
    _createGProfConfig(gProfOutputPath, outputProfilePath, cmd, label)

    # Create the dot graph
    _createDotMap(dotExec, outputImagePath, gProfOutputPath)

    if openImage:
        time.sleep(.1) # Wait for the image to be closed
        platform = _getPlatform()
        try:
            if platform == "windows":
                os.startfile(outputImagePath)
            elif platform == "mac":
                cmd = "open \"{0}\"".format(outputImagePath)
                op = subprocess.Popen(cmd, shell=True)
                op.wait()
        except:
            LOG.error("Unable to open file: {0}".format(outputImagePath))

    # Cleanup
    # try:
    #     os.remove(gProfOutputPath)
    #     LOG.debug("Removed: {0}".format(gProfOutputPath))
    #     os.remove(outputProfilePath)
    #     LOG.debug("Removed: {0}".format(outputProfilePath))
    # except Exception, e:
    #     LOG.warning("Warning unable to remove profile. {0}".format(e))

def createProfile(cmd, outputFile, global_dict=None, local_dict=None, frameDepth=0):
    ''' Profile the execution of a command and save it to a file '''
    if local_dict is None and global_dict is None:
        call_frame = sys._getframe(frameDepth).f_back
        local_dict = call_frame.f_locals
        global_dict = call_frame.f_globals
    outputFile = _cleanPath(outputFile)
    startTime = time.time()
    cProfile.runctx(cmd, global_dict, local_dict, outputFile)
    return time.time() - startTime

def test_createDotMap():
    import socket
    createDotMap("socket.gethostname()", openImage=True)

def _getPlatform():
    ''' Get the os of the current system in a standard format '''
    if ((sys.platform.lower() == "win32") or (sys.platform.lower() == "win64")):
        return "windows"
    elif (sys.platform.lower() == "darwin"):
        return "mac"
    else:
        return "linux"

def _getDotExecPath():
    ''' Locate the dot executable path '''
    platform = _getPlatform()
    if default_dotExecPath.has_key(platform):
        return default_dotExecPath[platform]
    return None

def _cleanPath(path):
    if path is None:
        nameTmp = "profileGraph_{0}.png".format(time.time())
        path = getTempFile(nameTmp)
    path = os.path.abspath(path)
    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path

def _createGProfConfig(outputPath, outputProfile, cmd, label):
    ''' Create the dot graph configuration file from gprof2dot '''
    gprofCmd = ["",
        "-f", "pstats", outputProfile,
        "-o", outputPath,
        "-l", label,
    ]
    sys.argv = gprofCmd
    gProf = gprof2dot.Main()
    gProf.main()
    gProf.output.close()
    print os.path.exists(outputPath)
    f = open(outputPath, 'r')
    data = f.readlines()
    print data
    f.close()

def _createDotMap(dotExec, outputImagePath, gProfOutputPath):
    ''' Use graphviz to create the dot graph '''
    cmd = "\"{0}\" -v -Tpng \"{2}\" -o \"{1}\"".format(dotExec, outputImagePath, gProfOutputPath)
    kwargs = {}
    if _getPlatform() == 'mac':
        kwargs['shell'] = True
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    LOG.debug("Dot Command: {0}".format(cmd))
    p.wait()
    LOG.debug("Dot Command Results: {0}".format(p.communicate()))
    LOG.info("Dot Graph available at: {0}".format(outputImagePath))
    LOG.debug("dot return code: {0}".format(p.returncode))
    return p.returncode