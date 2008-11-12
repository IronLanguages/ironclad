from System.Diagnostics import Process
from numpytests import get_continuation_point, add_to_blacklist

def run_blacklister_robustly():
    p = Process()
    p.StartInfo.FileName = 'ipy'
    p.StartInfo.Arguments = 'numpytests.py --blacklist-add --continue'
    p.Start()
    if not p.WaitForExit(120000):
	add_to_blacklist('Took too long (probably)')
	p.Kill()
	return False
    return p.ExitCode == 0

while not run_blacklister_robustly():
    pass
    
    
    

