# -*- coding: utf-8 -*-
# Hypothesis test: set the C axis (5th) direction to MAGNITUDE_DETERMINES_DIRECTION.
# The +/-X tool-axis operations get a mirrored C solution (180 deg off) because
# the C rotary table is configured SIGN_DETERMINES_DIRECTION. For a 0-360 rotary
# table the direction is determined by magnitude, not sign.
import os
import re

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'

with open(os.path.join(BASE, 'LOMO_FG300C.tcl'), 'rb') as f:
    raw = f.read()

pattern = rb'(set mom_kin_5th_axis_direction\s+)"SIGN_DETERMINES_DIRECTION"'
new_raw, n = re.subn(pattern, rb'\1"MAGNITUDE_DETERMINES_DIRECTION"', raw, count=1)
assert n == 1, 'found %d matches' % n

assert new_raw.count(LF) == new_raw.count(CR), 'mixed line endings'
assert max(new_raw) < 128, 'non-ASCII byte'
with open(os.path.join(BASE, 'LOMO_FG300C.tcl'), 'wb') as f:
    f.write(new_raw)
print('   ok  mom_kin_5th_axis_direction -> MAGNITUDE_DETERMINES_DIRECTION')
print('   written %d bytes' % len(new_raw))
print('ALL DONE')
