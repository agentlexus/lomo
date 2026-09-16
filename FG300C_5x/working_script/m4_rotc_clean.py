import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)
b = rep(b,
    b'  global mom_ude_interpolation_lock mom_siemens_ori_def pb_lock_arc_active pb_lock_turn_done' + CR,
    b'  global mom_ude_interpolation_lock mom_siemens_ori_def pb_lock_turn_done' + CR,
    'clean-g')
b = rep(b,
    b'     set pb_lock_arc_active 0' + CR + b'     set pb_lock_turn_done 0' + CR,
    b'     set pb_lock_turn_done 0' + CR,
    'clean-s')
assert b.count(b'\n') == b.count(b'\r')
assert max(b) < 128
open(p, 'wb').write(b)
print('cleaned', len(b))
