# -*- coding: ascii -*-
# m4_cycle800_canonical2.py
# Move the CYCLE800 Z-rotation canonicalization out of PB_CMD__check_block_CYCLE800
# and into DPP_GE_CALCULATE_COOR_ROT_ANGLE (XYZ branch). Canonicalizing at the source
# keeps rot_angle and coord_angle in sync, so the output-mode switch does not emit
# duplicate CYCLE800 blocks.
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'
CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


# 1) Revert the rule from PB_CMD__check_block_CYCLE800.
REV_OLD = block(
    '        set cycle800_mode 57',
    '        # Canonical Z-rotation of the swivel (3rd CYCLE800 angle) - per reference.',
    '        if { $coord_angle(0) > 0.0 } {',
    '           if { $coord_angle(1) > 0.0 } { set coord_angle(2) -180.0 } else { set coord_angle(2) 180.0 }',
    '        } else {',
    '           set coord_angle(2) 0.0',
    '        }',
    '        set coord_ang_C $coord_angle(2)',
    '',
    '        MOM_do_template rotation_axes CREATE',
)
REV_NEW = block(
    '        set cycle800_mode 57',
    '',
    '        MOM_do_template rotation_axes CREATE',
)

# 2) Add canonicalization at the source (XYZ branch of DPP_GE_CALCULATE_COOR_ROT_ANGLE).
SRC_OLD = block(
    '      set C [expr -atan2($sin_c,$cos_c)*$RAD2DEG]',
    '',
    '      set rot_ang(0) $A; set rot_ang(1) $B; set rot_ang(2) $C',
    '      set status OK',
)
SRC_NEW = block(
    '      set C [expr -atan2($sin_c,$cos_c)*$RAD2DEG]',
    '',
    '      set rot_ang(0) $A; set rot_ang(1) $B; set rot_ang(2) $C',
    '      # Canonical Z-rotation (3rd CYCLE800 angle) - per reference.',
    '      if { $rot_ang(0) > 0.0 } {',
    '         if { $rot_ang(1) > 0.0 } { set rot_ang(2) -180.0 } else { set rot_ang(2) 180.0 }',
    '      } else {',
    '         set rot_ang(2) 0.0',
    '      }',
    '      set status OK',
)


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(REV_OLD) == 1, 'rev anchor %d' % raw.count(REV_OLD)
    assert raw.count(SRC_OLD) == 1, 'src anchor %d' % raw.count(SRC_OLD)
    raw = raw.replace(REV_OLD, REV_NEW)
    raw = raw.replace(SRC_OLD, SRC_NEW)
    assert raw.count(b'{') == raw.count(b'}'), 'brace'
    assert max(raw) < 128, 'non-ascii'
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    open(PATH, 'wb').write(raw)
    print('OK canonical2 patched (revert + source)')


if __name__ == '__main__':
    main()
