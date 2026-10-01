# -*- coding: ascii -*-
# m4_cycle800_canonical.py
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'
CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


DIAG = block(
    '        set __p {}',
    '        foreach __v {mom_operation_name mom_siemens_coord_rotation mom_siemens_5axis_mode dpp_ge(current_output_mode) dpp_ge(prev_output_mode) cycle800_dir mom_rotary_direction_4th mom_rotary_direction_5th mom_prev_rot_ang_4th mom_prev_rot_ang_5th coord_ang_A coord_ang_B coord_ang_C coord_angle(0) coord_angle(1) coord_angle(2) mom_out_angle_pos(0) mom_out_angle_pos(1) mom_pos(3) mom_pos(4) mom_alt_pos(3) mom_alt_pos(4) mom_result1} {',
    '            if { [uplevel #0 [list info exists $__v]] } {',
    '               lappend __p "$__v=[uplevel #0 [list set $__v]]"',
    '            } else {',
    '               lappend __p "$__v=<none>"',
    '            }',
    '         }',
    '         PB_CMD_output_comment ";(DBG-CYCLE800 [join $__p { }])"',
)

RULE = block(
    '        # Canonical Z-rotation of the swivel (3rd CYCLE800 angle) - per reference.',
    '        if { $coord_angle(0) > 0.0 } {',
    '           if { $coord_angle(1) > 0.0 } { set coord_angle(2) -180.0 } else { set coord_angle(2) 180.0 }',
    '        } else {',
    '           set coord_angle(2) 0.0',
    '        }',
    '        set coord_ang_C $coord_angle(2)',
)


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    assert max(raw) < 128, 'non-ascii'
    n = raw.count(DIAG)
    assert n == 1, 'DIAG %d' % n
    raw = raw.replace(DIAG, b'')
    anchor = b'        set cycle800_mode 57'
    assert raw.count(anchor) == 1, 'anchor'
    i = raw.find(anchor)
    e = raw.find(b'\r\n', i) + 2
    raw = raw[:e] + RULE + raw[e:]
    assert raw.count(b'{') == raw.count(b'}'), 'brace'
    open(PATH, 'wb').write(raw)
    j = raw.find(b'Canonical Z-rotation')
    print(raw[j - 80:j + 320].decode('ascii'))
    print('OK')


main()
