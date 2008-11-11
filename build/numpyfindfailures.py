from System.Diagnostics import Process

def run_blacklister_robustly():
    p = Process()
    p.StartInfo.FileName = 'ipy'
    p.StartInfo.Arguments = 'numpytests.py --blacklist-add'
    p.Start()
    if not p.WaitForExit(120000):
	p.Kill()
	return False
    return p.ExitCode == 0

while not run_blacklister_robustly():
    pass
    
    
    

