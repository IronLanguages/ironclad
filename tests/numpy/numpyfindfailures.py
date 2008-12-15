from System.Diagnostics import Process
from numpytests import get_all_tests, add_to_blacklist

for test_path, _ in  get_all_tests(['core', 'lib']):
    p = Process()
    print "Running", ".".join(test_path)
    p.StartInfo.FileName = 'ipy'
    p.StartInfo.Arguments = 'numpytests.py %s' % '.'.join(test_path)
    p.StartInfo.CreateNoWindow = True
    p.StartInfo.UseShellExecute = False
    p.Start()
    if not p.WaitForExit(300000):
        add_to_blacklist(test_path)
        p.Kill()
        p.WaitForExit()
    if p.ExitCode != 0:
        add_to_blacklist(test_path)


    



    
    
    

