# -*- coding: ascii -*-
# m4_cycle800_coord_fix.py
# 1) Revert the temporary DBG-CYCLE800 diagnostic.
# 2) In DPP_GE_COOR_ROT_AUTO3D, compute the linear position with the LOWER
#    rotary solution (cycle800_dir = -1) while keeping the CYCLE800 rotation
#    matrix on the primary solution. This fixes the mirrored coordinates of the
#    *_COPY operations (mom_rotary_direction_4th = +1 -> A = +90 -> mirrored).
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'
CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


POS_OLD = block(
    '   VECTOR_ROTATE mom_kin_5th_axis_vector [expr $rot_dir_5th*$rot1] mom_mcs_goto V',
    '   VECTOR_ROTATE mom_kin_4th_axis_vector [expr $rot_dir_4th*$rot0] V pos',
)
POS_NEW = block(
    '   # Select the lower rotary solution (cycle800_dir=-1) for the linear position only.',
    '   # The CYCLE800 rotation matrix below keeps the primary solution.',
    '   set pos_rot0 $rot0',
    '   set pos_rot1 $rot1',
    '   if { $ang_pos(0) > 0.0 } {',
    '      set pos_rot0 [expr $rot0 - 180.0*$DEG2RAD]',
    '      set pos_rot1 [expr $rot1 - 180.0*$DEG2RAD]',
    '   }',
    '',
    '   VECTOR_ROTATE mom_kin_5th_axis_vector [expr $rot_dir_5th*$pos_rot1] mom_mcs_goto V',
    '   VECTOR_ROTATE mom_kin_4th_axis_vector [expr $rot_dir_4th*$pos_rot0] V pos',
)


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    assert max(raw) < 128, 'non-ascii'

    # 1) Revert the diagnostic block between the two anchors.
    a = b'        set cycle800_mode 57'
    b = b'        MOM_do_template rotation_axes CREATE'
    ia = raw.find(a)
    assert ia != -1, 'anchor A'
    ea = raw.find(b'\r\n', ia) + 2
    ib = raw.find(b, ea)
    assert ib != -1, 'anchor B'
    seg = raw[ea:ib]
    assert b'DBG-CYCLE800' in seg, 'diag block not found'
    raw = raw[:ea] + b'\r\n' + raw[ib:]

    # 2) Fix the coordinate computation.
    assert raw.count(POS_OLD) == 1, 'pos anchor %d' % raw.count(POS_OLD)
    raw = raw.replace(POS_OLD, POS_NEW)

    assert raw.count(b'{') == raw.count(b'}'), 'brace'
    assert max(raw) < 128, 'non-ascii'
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    assert b'DBG-CYCLE800' not in raw, 'diag still present'
    open(PATH, 'wb').write(raw)
    j = raw.find(b'pos_rot0 $rot0')
    print(raw[j - 40:j + 260].decode('ascii'))
    print('OK coord fix applied (diag reverted + lower solution)')


if __name__ == '__main__':
    main()
