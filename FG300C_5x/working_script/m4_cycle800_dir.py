# -*- coding: ascii -*-
# m4_cycle800_dir.py
# CYCLE800: always the lower rotary solution (per working reference).
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'
CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


OLD = block('        set cycle800_dir $mom_rotary_direction_4th')
NEW = block('        set cycle800_dir -1 ;# Hardcoded: lower rotary solution (per reference)')


def main():
    raw = open(PATH, 'rb').read()
    n = raw.count(OLD)
    assert n == 1, 'anchor %d' % n
    raw = raw.replace(OLD, NEW)
    assert raw.count(b'{') == raw.count(b'}'), 'brace'
    assert max(raw) < 128, 'non-ascii'
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    open(PATH, 'wb').write(raw)
    i = raw.find(b'set cycle800_dir')
    print(raw[i - 100:i + 180].decode('ascii'))
    print('OK cycle800_dir patched')


if __name__ == '__main__':
    main()
