# -*- coding: ascii -*-
# m4_cycle800_dbg2.py
# Add a comprehensive CYCLE800 diagnostic (rotary solution + coordinates) to
# diagnose the mirrored coordinates of the *_COPY operations.
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'
CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


ANCHOR = b'        set cycle800_mode 57'

VARS = (
    'mom_operation_name mom_siemens_coord_rotation mom_siemens_5axis_mode '
    'dpp_ge(current_output_mode) dpp_ge(prev_output_mode) dpp_ge(coord_rot) '
    'cycle800_dir mom_rotary_direction_4th mom_rotary_direction_5th '
    'mom_prev_rot_ang_4th mom_prev_rot_ang_5th '
    'mom_kin_4th_axis_direction mom_kin_5th_axis_direction '
    'mom_kin_4th_axis_rotation mom_kin_5th_axis_rotation '
    'mom_kin_4th_axis_zero mom_kin_5th_axis_zero '
    'coord_ang_A coord_ang_B coord_ang_C '
    'coord_angle(0) coord_angle(1) coord_angle(2) '
    'mom_out_angle_pos(0) mom_out_angle_pos(1) mom_alt_pos(3) mom_alt_pos(4) '
    'mom_pos(0) mom_pos(1) mom_pos(2) mom_pos(3) mom_pos(4) '
    'mom_mcs_goto(0) mom_mcs_goto(1) mom_mcs_goto(2) '
    'mom_kin_4th_axis_vector(0) mom_kin_4th_axis_vector(1) mom_kin_4th_axis_vector(2) '
    'mom_kin_5th_axis_vector(0) mom_kin_5th_axis_vector(1) mom_kin_5th_axis_vector(2) '
    'mom_result1 rot_angle(0) rot_angle(1) rot_alt_angle(0) rot_alt_angle(1)'
)

DIAG = block(
    '        set __p {}',
    '        foreach __v {' + VARS + '} {',
    '            if { [uplevel #0 [list info exists $__v]] } {',
    '               lappend __p "$__v=[uplevel #0 [list set $__v]]"',
    '            } else {',
    '               lappend __p "$__v=<none>"',
    '            }',
    '         }',
    '         PB_CMD_output_comment ";(DBG-CYCLE800 [join $__p { }])"',
)


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    assert max(raw) < 128, 'non-ascii'
    if b'DBG-CYCLE800' in raw:
        print('already patched'); return
    n = raw.count(ANCHOR)
    assert n == 1, 'anchor %d' % n
    i = raw.find(ANCHOR)
    e = raw.find(b'\r\n', i) + 2
    raw = raw[:e] + DIAG + raw[e:]
    assert raw.count(b'{') == raw.count(b'}'), 'brace'
    open(PATH, 'wb').write(raw)
    j = raw.find(b'DBG-CYCLE800')
    print(raw[j - 30:j + 120].decode('ascii'))
    print('OK diag2 added')


if __name__ == '__main__':
    main()
