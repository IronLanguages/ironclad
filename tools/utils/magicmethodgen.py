

def template(functype, inargs, template):
    args = ', '.join(['_%d' % i for i in xrange(len(inargs))])
    return template % {
        'arglist': args,
        'callargs': args,
        'functype': functype,
    }


def swapped_template(functype, inargs, template):
    args = ['_%d' % i for i in xrange(len(inargs))]
    return template % {
        'arglist': ', '.join(args),
        'callargs': ', '.join(args[::-1]),
        'functype': functype,
    }