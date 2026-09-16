import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()

def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)

# 1. add helper proc before MOM_nurbs_move
old = CR.join([b'#=============================================================', b'proc MOM_nurbs_move { } {']) + CR
new = CR.join([
    b'#=============================================================',
    b'proc PB_CMD_output_comment { text } {',
    b'#=============================================================',
    b'# Output a comment/literal without a sequence number.',
    b'   set seq_state [MOM_set_seq_off]',
    b'   MOM_output_literal $text',
    b'   if { [string match "on" $seq_state] } { MOM_set_seq_on }',
    b'}',
    b'',
    b'',
    b'#=============================================================',
    b'proc MOM_nurbs_move { } {',
]) + CR
b = rep(b, old, new, 'helper')

# 2. line-by-line: comment literals -> helper
lines = b.split(CR)
n = 0
for i, line in enumerate(lines):
    if line.lstrip().startswith(b'MOM_output_literal ";'):
        lines[i] = line.replace(b'MOM_output_literal "', b'PB_CMD_output_comment "', 1)
        n += 1
b = CR.join(lines)
print('replaced comment literals:', n)

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
open(p, 'wb').write(b)
print('written', len(b))
print('ALL DONE')
