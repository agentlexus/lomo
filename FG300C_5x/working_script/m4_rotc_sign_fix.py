# -*- coding: utf-8 -*-
# Fix the flipped approach Z sign for the +/-X side 3+2 operations (M4_rotate).
# The rotary-table C solution for those orientations is 180 deg off, so the
# rotated POSITION maps the approach +X -> -Y -> -Z (Z becomes -200). Flip the
# C rotation direction used for the rotated position (rot_dir_5th) so it maps
# +X -> +Y -> +Z (+200). The rotation MATRIX uses the raw angle, so CYCLE800
# spatial angles are not affected. C=0 / C=180 are sign-invariant, so the
# +/-Y operations stay intact.
import os

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'
data = {}


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        data[name] = f.read()
    return data[name]


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def rep(name, tag, old, new):
    raw = data[name]
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d' % (tag, n)
    data[name] = raw.replace(old, new)
    print('   ok  %s' % tag)


# ------------------------------------------------------------------ .tcl
tcl = load('LOMO_FG300C.tcl')
BR_OPEN = tcl.count(b'{')
BR_CLOSE = tcl.count(b'}')

rep('LOMO_FG300C.tcl', 'tcl/flip C rotation direction for rotated position',
    block('''   set rot_dir_5th -1
   if { [string match "reverse" $::mom_kin_5th_axis_rotation] } {
      set rot_dir_5th 1
   }'''),
    block('''   # C-axis (5th): the rotary-table C solution for the +/-X side approaches
   # comes out 180 deg off, mapping the approach +X -> -Y -> -Z and flipping
   # the approach Z sign (Z-200). Use the opposite C direction here so the
   # rotated POSITION maps +X -> +Y -> +Z (+200). The rotation MATRIX below
   # uses the raw angle, so CYCLE800 spatial angles are not affected.
   set rot_dir_5th 1
   if { [string match "reverse" $::mom_kin_5th_axis_rotation] } {
      set rot_dir_5th -1
   }'''))

# ---------------------------------------------------------------- write + check
raw = data['LOMO_FG300C.tcl']
assert raw.count(LF) == raw.count(CR), 'mixed line endings'
with open(os.path.join(BASE, 'LOMO_FG300C.tcl'), 'wb') as f:
    f.write(raw)
print('   written LOMO_FG300C.tcl %d bytes' % len(raw))

t = data['LOMO_FG300C.tcl']
assert max(t) < 128, 'tcl: non-ASCII byte written'
print('   tcl brace delta { %+d  } %+d' % (t.count(b'{') - BR_OPEN, t.count(b'}') - BR_CLOSE))
assert (t.count(b'{') - BR_OPEN) == (t.count(b'}') - BR_CLOSE), 'unbalanced braces'
for pat in (b'set rot_dir_5th 1', b'set rot_dir_5th -1', b'set rot_dir_4th -1', b'set rot_dir_4th 1'):
    print('   count %-28s %d' % (pat.decode(), t.count(pat)))
print('ALL DONE')
