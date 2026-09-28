# -*- coding: ascii -*-
# m4_initial_move_dup.py
#
# Fix the duplicated first positioning move: MOM_initial_move called the move
# twice - once inside PB_CMD_output_initial_move (which already ends with
# MOM_rapid_move / MOM_linear_move) and once again in its own tail. Remove the
# redundant tail so the approach is emitted only once (matches the reference).

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


OLD_TAIL = block(
    '  global mom_programmed_feed_rate',
    '   if { [EQ_is_equal $mom_programmed_feed_rate 0] } {',
    '      MOM_rapid_move',
    '   } else {',
    '      MOM_linear_move',
    '   }',
    '',
    '  # Configure turbo output settings',
    '   if { [CMD_EXIST CONFIG_TURBO_OUTPUT] } {',
    '      CONFIG_TURBO_OUTPUT',
    '   }',
)


def main():
    raw = open(PATH, 'rb').read()

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    n = raw.count(OLD_TAIL)
    assert n == 1, 'OLD_TAIL found %d times (expected 1)' % n
    raw = raw.replace(OLD_TAIL, b'')

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    i = raw.find(b'proc MOM_initial_move')
    print(raw[i:i + 320].decode('ascii'))
    print('OK: initial_move duplicate removed.')


if __name__ == '__main__':
    main()
