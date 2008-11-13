from System.Diagnostics import Process
from numpytests import get_continuation_point, add_to_blacklist, save_continuation_point

def run_blacklister_robustly():
    p = Process()
    p.StartInfo.FileName = 'ipy'
    p.StartInfo.Arguments = 'numpytests.py --blacklist-add --continue'
    p.Start()
    if not p.WaitForExit(120000):
	add_to_blacklist(get_continuation_point(), msg='Took too long (probably)')
	save_continuation_point(None)
	p.Kill()
	p.WaitForExit()
	return False
    return p.ExitCode == 0

while not run_blacklister_robustly():
    pass
    
    
    

