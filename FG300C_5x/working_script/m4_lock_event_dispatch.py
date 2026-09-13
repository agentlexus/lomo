# -*- coding: ascii -*-
# UDE "Interpolation_lock" - make the event actually dispatch, and clean up
# the legacy "interpolation_lock" event.
#   1) .tcl : the post kernel calls MOM_<event>; add the missing wrapper
#             MOM_Interpolation_lock (all working UDEs in this post have one).
#   2) .def : INCLUDE the dedicated UDE file next to the stock catalog
#             ($UGII_CAM_USER_DEF_EVENT_DIR/LOMO_FG300C.cdl).
#   3) new  : FG300C_5x/LOMO_FG300C_ude.cdl = byte copy of the deployed
#             user_def_event/LOMO_FG300C.cdl (custom events only).
#   4) drop the legacy EVENT interpolation_lock from .cdl/.pui (deprecated;
#      it was never part of the global catalog) together with the no-op
#      handler PB_CMD_MOM_interpolation_lock.
# Files are ASCII + CRLF, so every edit is byte-wise with asserts.
import os
import shutil

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
UDE_SRC = r'D:\Siemens\NX2312\MACH\resource\user_def_event\LOMO_FG300C.cdl'
CR = b'\r\n'
LF = b'\n'
BS = chr(92)
data = {}


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        data[name] = f.read()
    return data[name]


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def lc(text):
    """Append the .pui line-continuation backslash."""
    return (text + ' ' + BS).encode('ascii')


def rep(name, tag, old, new, expect=1):
    raw = data[name]
    n = raw.count(old)
    assert n == expect, 'MISS %s: found %d, expected %d' % (tag, n, expect)
    data[name] = raw.replace(old, new)
    print('   ok  %s' % tag)


def save(name):
    raw = data[name]
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    assert max(raw) < 128, '%s: non-ASCII byte written' % name
    with open(os.path.join(BASE, name), 'wb') as f:
        f.write(raw)


# ---------------------------------------------------------------- .tcl (1/2)
tcl = load('LOMO_FG300C.tcl')
BR_OPEN = tcl.count(b'{')
BR_CLOSE = tcl.count(b'}')

# the wrapper the kernel needs: ring the same bell as MOM_lock_axis / MOM_clamp
ANCHOR_NURBS = block('#=============================================================\n'
                     'proc MOM_nurbs_move { } {')
rep('LOMO_FG300C.tcl', 'tcl/wrapper MOM_Interpolation_lock',
    ANCHOR_NURBS,
    block('''
#=============================================================
proc MOM_Interpolation_lock { } {
#=============================================================
# UDE "Interpolation lock". The post dispatches a UDE to MOM_<event name>,
# so this wrapper forwards the event data to the handler
# (see PB_CMD_MOM_Interpolation_lock / PB_CMD__lock_mode).
   global mom_command_status
   global mom_lock_axis
   global mom_lock_axis_plane
   global mom_ASCALE_value
   PB_CMD_MOM_Interpolation_lock
}

''') + ANCHOR_NURBS)

# ---------------------------------------------------------------- .def
load('LOMO_FG300C.def')
rep('LOMO_FG300C.def', 'def/INCLUDE custom UDE file',
    b'$UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl',
    b'$UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl' + CR +
    b'         $UGII_CAM_USER_DEF_EVENT_DIR/LOMO_FG300C.cdl')
# ================================================================ PART2
# legacy UDE "interpolation_lock": drop the declaration (it was never part of
# the global catalog - the new UDE "Interpolation_lock" replaces it)
load('LOMO_FG300C.cdl')
rep('LOMO_FG300C.cdl', 'cdl/drop legacy EVENT interpolation_lock',
    block('''
EVENT interpolation_lock
{
   UI_LABEL "Interpolation Lock"
   CATEGORY MILL
   PARAM ude_interpolation_lock
   {
      TYPE o
      DEFVAL "Yes"
      OPTIONS "Yes","No"
      UI_LABEL "Interpolation Lock"
   }
}
''') + CR + CR,
    b'')

load('LOMO_FG300C.pui')
rep('LOMO_FG300C.pui', 'pui/drop legacy UDE row',
    block('{interpolation_lock}       {PB_CMD_MOM_interpolation_lock}  {Interpolation Lock} {UDE}'),
    b'')
rep('LOMO_FG300C.pui', 'pui/drop legacy Custom Command row',
    lc('      {"PB_CMD_MOM_interpolation_lock" "" "Custom Command"}') + CR,
    b'')
# ================================================================ PART3
# .tcl: drop the now unused no-op handler as well
rep('LOMO_FG300C.tcl', 'tcl/drop no-op PB_CMD_MOM_interpolation_lock',
    block('''
#=============================================================
proc PB_CMD_MOM_interpolation_lock { } {
#=============================================================
# DEPRECATED: legacy UDE "interpolation_lock" (PARAM ude_interpolation_lock).
# It no longer switches the lock mode on - the only trigger is the UDE
# "Interpolation_lock" (see PB_CMD_MOM_Interpolation_lock / PB_CMD__lock_mode).
# The event stays declared in .cdl/.pui so that old parts do not fail.
   global mom_ude_interpolation_lock
}
''') + CR + CR,
    b'')

# custom-UDE file for the repo: byte copy of the one already deployed in the
# NX UDE folder (deploy: MACH\resource\user_def_event\LOMO_FG300C.cdl)
with open(UDE_SRC, 'rb') as f:
    ude = f.read()
assert b'EVENT Interpolation_lock' in ude, 'UDE_SRC is not our event'
assert b'ASCALE_value' in ude, 'UDE_SRC has no ASCALE_value'
with open(os.path.join(BASE, 'LOMO_FG300C_ude.cdl'), 'wb') as f:
    f.write(ude)
print('   ok  new LOMO_FG300C_ude.cdl (%d bytes)' % len(ude))

for name in ('LOMO_FG300C.def', 'LOMO_FG300C.pui', 'LOMO_FG300C.cdl', 'LOMO_FG300C.tcl'):
    save(name)

# ------------------------------------------------------------- verification
t = data['LOMO_FG300C.tcl']
d_open = t.count(b'{') - BR_OPEN
d_close = t.count(b'}') - BR_CLOSE
print()
print('   brace delta: { %+d  } %+d' % (d_open, d_close))
assert d_open == d_close, 'unbalanced braces introduced'

checks = [
    ('LOMO_FG300C.tcl', 'proc MOM_Interpolation_lock { } {', 1),
    ('LOMO_FG300C.tcl', 'PB_CMD_MOM_interpolation_lock', 0),
    ('LOMO_FG300C.def', 'LOMO_FG300C.cdl', 1),
    ('LOMO_FG300C.cdl', 'EVENT Interpolation_lock', 1),
    ('LOMO_FG300C.cdl', 'EVENT interpolation_lock', 0),
    ('LOMO_FG300C.pui', 'PB_CMD_MOM_interpolation_lock', 0),
    ('LOMO_FG300C.pui', 'PB_CMD_MOM_Interpolation_lock', 2),
]
info = [
    ('LOMO_FG300C.tcl', 'PB_CMD_MOM_Interpolation_lock'),
    ('LOMO_FG300C.tcl', 'mom_ASCALE_value'),
    ('LOMO_FG300C.tcl', 'PB_CMD__lock_mode] } {'),
]
for name, pat, want in checks:
    got = data[name].count(pat.encode('ascii'))
    print('   %-20s %-38s %d (want %d)' % (name, pat, got, want))
    assert got == want, 'check failed: %s / %s' % (name, pat)
for name, pat in info:
    print('   %-20s %-38s %d' % (name, pat, data[name].count(pat.encode('ascii'))))
print()
for name in ('LOMO_FG300C.tcl', 'LOMO_FG300C.def', 'LOMO_FG300C.pui', 'LOMO_FG300C.cdl', 'LOMO_FG300C_ude.cdl'):
    raw = open(os.path.join(BASE, name), 'rb').read()
    print('   %-22s size %-8d nonascii %d  CRLF %d  lone-LF %d' %
          (name, len(raw), sum(1 for b in raw if b > 127), raw.count(CR), raw.count(LF) - raw.count(CR)))
print('ALL DONE')
