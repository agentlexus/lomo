# -*- coding: ascii -*-
# m4_camtolerance_hardcode.py
#
# Hardcode the _camtolerance value to 0.002 (per customer requirement),
# instead of computing it from the CAM inside/outside tolerances.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


NEW = block(
    '   # _camtolerance hardcoded (per customer requirement).',
    '   MOM_output_literal "_camtolerance=0.002"',
)


def main():
    raw = open(PATH, 'rb').read()

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    s = raw.find(b'   # _camtolerance from CAM')
    assert s >= 0, 'anchor: comment not found'
    u = raw.find(b'MOM_output_literal "_camtolerance=[PB_CMD__format_cam_tolerance $cam_tolerance_total]"', s)
    assert u > s, 'anchor: output line not found'
    e = raw.find(b'\r\n', u) + 2      # end of the output line
    e = raw.find(b'\r\n', e) + 2      # end of the closing '   }' line

    raw = raw[:s] + NEW + raw[e:]

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    i = raw.find(b'_camtolerance hardcoded')
    print(raw[i - 40:i + 120].decode('ascii'))
    print('OK: _camtolerance hardcoded to 0.002.')


if __name__ == '__main__':
    main()
