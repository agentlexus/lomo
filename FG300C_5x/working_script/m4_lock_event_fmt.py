# -*- coding: ascii -*-
# Cosmetic follow-up: restore blank line separators after
#   - proc MOM_Interpolation_lock  (.tcl)
#   - EVENT Interpolation_lock     (.cdl)
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'


def fix(name, tag, old, new):
    path = os.path.join(BASE, name)
    raw = open(path, 'rb').read()
    print('   --- %s around %r ---' % (name, tag))
    i = raw.find(old.split(CR)[0])
    print('   ', raw[max(0, i - 80):i + 160].decode('ascii').replace('\r', ''))
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d' % (tag, n)
    raw = raw.replace(old, new)
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    assert max(raw) < 128, '%s: non-ASCII byte written' % name
    open(path, 'wb').write(raw)
    print('   ok  %s' % tag)


fix('LOMO_FG300C.tcl', 'tcl/blank lines after MOM_Interpolation_lock',
    b'}' + CR + b'#=============================================================' + CR +
    b'proc MOM_nurbs_move { } {' + CR,
    b'}' + CR + CR + CR + b'#=============================================================' + CR +
    b'proc MOM_nurbs_move { } {' + CR)

fix('LOMO_FG300C.cdl', 'cdl/blank lines before EVENT tool_preselect',
    b'}' + CR + b'EVENT tool_preselect' + CR,
    b'}' + CR + CR + CR + b'EVENT tool_preselect' + CR)

print('ALL DONE')
