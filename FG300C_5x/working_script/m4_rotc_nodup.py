import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()
CR = b'\r\n'
old = CR.join([
    b'        CATCH_WARNING "$mom_operation_name:A3B3C3 should work with TRAORI mode, change to rotary output"',
    b'     }',
    b'',
    b' return 1',
    b'  } else {',
]) + CR
new = CR.join([
    b'        CATCH_WARNING "$mom_operation_name:A3B3C3 should work with TRAORI mode, change to rotary output"',
    b'     }',
    b'',
    b'     # 3+2 (SWIVELING): CYCLE800 positions the table (A and C), so the rotary',
    b'     # axes must not be output again in the motion block.',
    b'     if { [info exists mom_siemens_coord_rotation] && $mom_siemens_coord_rotation != 0 && [string match "SWIVELING" $mom_siemens_5axis_mode] } {',
    b'        MOM_suppress Once fourth_axis fifth_axis',
    b'     }',
    b'',
    b' return 1',
    b'  } else {',
]) + CR
n = b.count(old)
assert n == 1, 'anchor %d' % n
b = b.replace(old, new)
assert b.count(b'\n') == b.count(b'\r')
assert max(b) < 128
open(p, 'wb').write(b)
print('patched', len(b))
