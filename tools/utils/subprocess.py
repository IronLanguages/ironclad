
from System.Diagnostics import Process, ProcessStartInfo
    

#==========================================================================

def popen(executable, arguments):
    global process # XXX: keep it alive
    processStartInfo = ProcessStartInfo(executable, arguments)
    processStartInfo.UseShellExecute = False
    processStartInfo.CreateNoWindow = True
    processStartInfo.RedirectStandardOutput = True
    process = Process.Start(processStartInfo)
    return file(process.StandardOutput.BaseStream, "r")
    

#==========================================================================
    
