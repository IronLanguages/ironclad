from System import GC

def gcwait():
    GC.Collect()
    GC.WaitForPendingFinalizers()