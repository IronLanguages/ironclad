

from System.Diagnostics import Process, ProcessStartInfo

def popen(executable, arguments):
    global process # XXX: keep it alive
    processStartInfo = ProcessStartInfo(executable, arguments)
    processStartInfo.UseShellExecute = False
    processStartInfo.CreateNoWindow = True
    processStartInfo.RedirectStandardOutput = True
    process = Process.Start(processStartInfo)
    return file(process.StandardOutput.BaseStream, "r")


def starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)


def glom_templates(joiner, *args):
    output = []
    for (template, infos) in args:
        for info in infos:
            output.append(template % info)
    return joiner.join(output)


def multi_update(dict_, names, values):
    for (k, v) in zip(names, values):
        dict_[k] = v  


def read_interesting_lines(name):
    f = open(name)
    try:
        return filter(None, [l.split('#')[0].strip() for l in f.readlines()])
    finally:
        f.close()

