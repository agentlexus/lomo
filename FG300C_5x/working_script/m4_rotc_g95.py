# -*- coding: utf-8 -*-
# Rotary-table turn (interpolation-lock mode): feed-per-rev around the turn,
# restore G94, and force F on the next motion frame.
#   G1 G95 C=IC(+-360.1) F0.03   ->   G94   (next arc/linear carries its own F)
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(BASE, 'LOMO_FG300C.tcl')
CR = b'\r\n'

ANCHOR = b'   MOM_output_literal "G1 C=IC($angle) F200"' + CR
REPL = CR.join([
    b'   MOM_output_literal "G1 G95 C=IC($angle) F0.03"',
    b'   MOM_output_literal "G94"',
    b'   MOM_force Once F',
]) + CR


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF'
    assert max(raw) < 128, 'non-ASCII byte in tcl'

    if b'MOM_output_literal "G1 G95 C=IC($angle) F0.03"' in raw:
        print('Already patched. No-op.')
        return

    assert raw.count(b'G95') == 0 and raw.count(b'G94') == 0, 'G95/G94 already present'
    assert raw.count(ANCHOR) == 1, 'anchor count %d' % raw.count(ANCHOR)

    raw = raw.replace(ANCHOR, REPL)
    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF after'
    assert max(raw) < 128, 'non-ASCII byte after'
    open(PATH, 'wb').write(raw)

    i = raw.find(b'MOM_output_literal "G1 G95')
    print(raw[i - 90:i + 230].decode('ascii'))
    print('OK: LOMO_FG300C.tcl patched (%d bytes)' % len(raw))


if __name__ == '__main__':
    main()
