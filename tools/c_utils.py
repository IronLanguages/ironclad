

def type_from_c_type(c_type):
    return {
        'Py_ssize_t': 'size',
    }.get(c_type, c_type)


def name_spec_from_c(c):
    c = c.replace('const', '')
    c_start, c_end = map(str.strip, c.split(';')[0].split('(', 1))
    if c_start.find('*') == -1:
        rettype, name = c_start.split(' ')
        rettype = type_from_c_type(rettype)
    else:
        name = c_start.rsplit('*', 1)[1].strip()
        rettype = 'ptr'
    c_args = map(str.strip, c.split(','))
    args = []
    for c_arg in c_args:
        if c_arg.find('*') == -1:
            args.append(type_from_c_type(c_arg.rsplit(' ', 1)[0]))
        elif c_arg.find('char') != -1:
            args.append('str')
        else:
            args.append('ptr')
    
    return (name, '_'.join((rettype, ''.join(args))))