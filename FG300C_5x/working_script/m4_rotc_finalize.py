# -*- coding: utf-8 -*-
# Final cleanup of the C-axis direction fix:
# 1) Remove the temporary DBG diagnostic from DPP_GE_COOR_ROT.
# 2) .pui: 5th axis direction -> MAGNITUDE_DETERMINES_DIRECTION (value + UI enum).
# 3) README: replace the wrong rot_dir_5th history entry with the correct one.
import os
import re

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def blocku(text):
    return CR.join(l.encode('utf-8') for l in text.strip('\n').split('\n')) + CR


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        return f.read()


# ---------------------------------------------------------------- .tcl
tcl = load('LOMO_FG300C.tcl')
BR_OPEN = tcl.count(b'{')
BR_CLOSE = tcl.count(b'}')

# 1) remove the DBG diagnostic block (from its comment to the return statement)
pat = rb'   # ---- DBG \(temporary\): dump rotary solution per operation ----.*?   return \$coord_rot'
new_tcl, n = re.subn(pat, rb'   return $coord_rot', tcl, count=1, flags=re.DOTALL)
assert n == 1, 'tcl DBG removal: found %d' % n
tcl = new_tcl
print('   ok  tcl: DBG diagnostic removed')

assert tcl.count(LF) == tcl.count(CR), 'tcl: mixed line endings'
assert max(tcl) < 128, 'tcl: non-ASCII byte'
assert b'DBG_COOR_ROT' not in tcl, 'tcl: DBG_COOR_ROT still present'
print('   tcl brace delta { %+d  } %+d' % (tcl.count(b'{') - BR_OPEN, tcl.count(b'}') - BR_CLOSE))
assert (tcl.count(b'{') - BR_OPEN) == (tcl.count(b'}') - BR_CLOSE), 'tcl: unbalanced braces'
with open(os.path.join(BASE, 'LOMO_FG300C.tcl'), 'wb') as f:
    f.write(tcl)
print('   written LOMO_FG300C.tcl %d bytes' % len(tcl))

# ---------------------------------------------------------------- .pui
pui = load('LOMO_FG300C.pui')
pui, n1 = re.subn(rb'"SIGN_DETERMINES_DIRECTION"', rb'"MAGNITUDE_DETERMINES_DIRECTION"', pui, count=1)
assert n1 == 1, 'pui value: found %d' % n1
pui, n2 = re.subn(rb'"Sign_Determines_Direction"', rb'"Magnitude_Determines_Direction"', pui, count=1)
assert n2 == 1, 'pui enum: found %d' % n2
print('   ok  pui: 5th axis direction -> MAGNITUDE')

assert pui.count(LF) == pui.count(CR), 'pui: mixed line endings'
assert max(pui) < 128, 'pui: non-ASCII byte'
with open(os.path.join(BASE, 'LOMO_FG300C.pui'), 'wb') as f:
    f.write(pui)
print('   written LOMO_FG300C.pui %d bytes' % len(pui))

# ---------------------------------------------------------------- README
readme = load('README.md')
old = blocku('''- 2026-09-14: исправлена инверсия знака Z подхода для 3+2 операций со стороны
  +/-X (M4_rotate): решение стола C приходило со сдвигом 180°, подход выводился
  Z-200 вместо Z200. В DPP_GE_COOR_ROT_AUTO3D изменён знак поворота C при
  расчёте повёрнутой позиции (rot_dir_5th); CYCLE800-углы не затронуты.''')
new = blocku('''- 2026-09-15: исправлена инверсия знака Z подхода для 3+2 операций со стороны
  +/-X (M4_rotate / M4 floor_facing): ось C (поворотный стол) была настроена
  SIGN_DETERMINES_DIRECTION, из-за чего обратная кинематика давала зеркальную
  ветку решения (сдвиг 180° в C) для оси инструмента +X. Установлено
  MAGNITUDE_DETERMINES_DIRECTION (mom_kin_5th_axis_direction).''')
n = readme.count(old)
assert n == 1, 'readme history: found %d' % n
readme = readme.replace(old, new)
print('   ok  README: history entry corrected')

assert readme.count(LF) == readme.count(CR), 'readme: mixed line endings'
with open(os.path.join(BASE, 'README.md'), 'wb') as f:
    f.write(readme)
r = readme.decode('utf-8')
assert 'MAGNITUDE_DETERMINES_DIRECTION' in r
assert 'rot_dir_5th' not in r, 'readme still mentions rot_dir_5th'
print('   written README.md %d bytes' % len(readme))

print('ALL DONE')
