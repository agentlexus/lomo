# -*- coding: utf-8 -*-
# Append a history entry for the M4_rotate Z-sign fix.
import os

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'


def blocku(text):
    return CR.join(l.encode('utf-8') for l in text.strip('\n').split('\n')) + CR


with open(os.path.join(BASE, 'README.md'), 'rb') as f:
    raw = f.read()

old = blocku('## Примечание')
new = blocku('''- 2026-09-14: исправлена инверсия знака Z подхода для 3+2 операций со стороны
  +/-X (M4_rotate): решение стола C приходило со сдвигом 180°, подход выводился
  Z-200 вместо Z200. В DPP_GE_COOR_ROT_AUTO3D изменён знак поворота C при
  расчёте повёрнутой позиции (rot_dir_5th); CYCLE800-углы не затронуты.

## Примечание''')

assert raw.count(old) == 1, 'anchor count %d' % raw.count(old)
raw = raw.replace(old, new)
assert raw.count(LF) == raw.count(CR), 'mixed line endings'
with open(os.path.join(BASE, 'README.md'), 'wb') as f:
    f.write(raw)
r = raw.decode('utf-8')
assert 'rot_dir_5th' in r
print('written README.md %d bytes' % len(raw))
print('ALL DONE')
