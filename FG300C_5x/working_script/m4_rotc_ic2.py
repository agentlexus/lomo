import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)
old = CR.join([
    b'# at constant Z.  We replace that whole XY run-around with a single rotary C move:',
    b'#     G1 G91 C-360.1 F200',
    b'# then a following G90 when the flat circle-pass ends.',
]) + CR
new = CR.join([
    b'# at constant Z.  We replace that whole XY run-around with a single rotary C move:',
    b'#     G1 C=IC(360.1) F200',
    b'# (no G90 needed - C=IC keeps the absolute G90 mode).',
]) + CR
b = rep(b, old, new, 'lin-comment')
assert b.count(b'\n') == b.count(b'\r')
assert max(b) < 128
open(p, 'wb').write(b)
print('comment updated', len(b))
