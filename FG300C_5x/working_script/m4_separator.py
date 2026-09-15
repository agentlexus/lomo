# -*- coding: utf-8 -*-
# Add a blank separator line between operations: after ";(End of Path)" output
# a single-space line, so the next operation starts with a blank line above
# ";(start of Path)" (matches the reference etalon).
import os

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


with open(os.path.join(BASE, 'LOMO_FG300C.tcl'), 'rb') as f:
    raw = f.read()

old = block('''   MOM_output_literal ";(End of Path)"

   # Remember whether the next operation has a tool change: the 3+2 retract''')
new = block('''   MOM_output_literal ";(End of Path)"
   MOM_output_literal " "

   # Remember whether the next operation has a tool change: the 3+2 retract''')

n = raw.count(old)
assert n == 1, 'anchor found %d' % n
raw = raw.replace(old, new)
print('   ok  separator line added after ;(End of Path)')

assert raw.count(LF) == raw.count(CR), 'mixed line endings'
assert max(raw) < 128, 'non-ASCII byte'
with open(os.path.join(BASE, 'LOMO_FG300C.tcl'), 'wb') as f:
    f.write(raw)
print('   written LOMO_FG300C.tcl %d bytes' % len(raw))
print('ALL DONE')
