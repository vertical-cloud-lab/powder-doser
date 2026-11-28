"""Minimal S-expression reader/writer for KiCad files (FC-1 generators)."""
import re

class Q(str):
    """A quoted string atom."""
    pass

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)

def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError('parse error at %d: %r' % (pos, text[pos:pos + 40]))
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            lst = stack.pop()
            stack[-1].append(lst)
        elif m.group(3) is not None:
            s = m.group(3).replace('\\"', '"').replace('\\\\', '\\')
            stack[-1].append(Q(s))
        elif m.group(4) is not None:
            stack[-1].append(m.group(4))
    return stack[0][0] if len(stack[0]) == 1 else stack[0]

def q(s):
    return Q(s)

def _atom(a):
    if isinstance(a, Q):
        return '"' + a.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(a, float):
        s = ('%.4f' % a).rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    return str(a)

def dumps(x, indent=0):
    if not isinstance(x, list):
        return _atom(x)
    # short lists on one line
    if all(not isinstance(e, list) for e in x) or (len(x) <= 4 and sum(isinstance(e, list) for e in x) <= 1 and len(str(x)) < 80):
        return '(' + ' '.join(dumps(e, 0) for e in x) + ')'
    pad = '\t' * (indent + 1)
    head = []
    i = 0
    while i < len(x) and not isinstance(x[i], list):
        head.append(_atom(x[i]))
        i += 1
    out = '(' + ' '.join(head)
    for e in x[i:]:
        out += '\n' + pad + dumps(e, indent + 1)
    out += '\n' + '\t' * indent + ')'
    return out

def find(lst, key):
    for e in lst:
        if isinstance(e, list) and e and e[0] == key:
            return e
    return None

def findall(lst, key):
    return [e for e in lst if isinstance(e, list) and e and e[0] == key]
