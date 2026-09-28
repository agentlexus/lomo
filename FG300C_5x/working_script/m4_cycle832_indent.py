# -*- coding: ascii -*-
# m4_cycle832_indent.py
# Cosmetic: fix the doubled indentation on the hardcode comment line.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

OLD = b'                        # Hardcoded: always finishing (per customer requirement).\r\n'
NEW = b'            # Hardcoded: always finishing (per customer requirement).\r\n'


def main():
    raw = open(PATH, 'rb').read()
    n = raw.count(OLD)
    assert n == 1, 'comment found %d times' % n
    raw = raw.replace(OLD, NEW)
    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL'
    open(PATH, 'wb').write(raw)
    print('OK')


if __name__ == '__main__':
    main()
