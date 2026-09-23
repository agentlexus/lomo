# -*- coding: ascii -*-
# m4_header_machine_time.py
#
# Fix the ;(Machine time: 0.0 MIN) header: the header is emitted in
# PB_start_of_program, before any operation is posted, so mom_machine_time
# is still 0 there. The total is obtained by cycling the OPERATION objects
# of the object model (Shop Doc style); MOM_OPER_BODY accumulates each
# operation's mom_machine_time into pb_program_time.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


NEW_OPER_BODY = block(
    'proc MOM_OPER_BODY  {} {',
    '   global mom_machine_time pb_program_time',
    '   if { ![info exists pb_program_time] } { set pb_program_time 0.0 }',
    '   if { [info exists mom_machine_time] && $mom_machine_time != "" } {',
    '      set pb_program_time [expr $pb_program_time + $mom_machine_time]',
    '   }',
    '}',
)

NEW_TIME_BLOCK = block(
    '   # Machine time (minutes, two digits). The total is accumulated by',
    '   # MOM_OPER_BODY while cycling the operation objects of the object model.',
    '   global pb_program_time',
    '   if { ![info exists pb_program_time] } {',
    '      set pb_program_time 0.0',
    '      if [llength [info commands MOM_cycle_objects]] {',
    '         MOM_cycle_objects {SETUP {PROGRAMVIEW {MEMBERS {OPERATION}}}}',
    '      }',
    '   }',
    '   set mtime [format "%.2f" $pb_program_time]',
    '   PB_CMD_output_comment ";(Machine time: $mtime MIN)"',
)


def main():
    raw = open(PATH, 'rb').read()

    if b'pb_program_time' in raw:
        print('Already patched (pb_program_time present). No-op.')
        return

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    # M1: MOM_OPER_BODY accumulates the per-operation machine time
    a = raw.find(b'proc MOM_OPER_BODY  {} {}')
    assert a >= 0, 'anchor: MOM_OPER_BODY not found'
    e = raw.find(b'proc MOM_TOOL_HDR', a)
    assert e > a, 'anchor: MOM_TOOL_HDR not found after MOM_OPER_BODY'
    raw = raw[:a] + NEW_OPER_BODY + raw[e:]

    # M2: replace the machine-time output in the header
    s = raw.find(b'   # Machine time (minutes, one digit)')
    u = raw.find(b'PB_CMD_output_comment ";(Machine time: $mtime MIN)"', s)
    assert s >= 0, 'anchor: machine time comment not found'
    assert u > s, 'anchor: machine time output not found'
    line_end = raw.find(b'\r\n', u) + 2
    block_end = raw.find(b'\r\n', line_end) + 2  # skip the closing '   }' line
    raw = raw[:s] + NEW_TIME_BLOCK + raw[block_end:]

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    print('----- MOM_OPER_BODY -----')
    i = raw.find(b'proc MOM_OPER_BODY')
    print(raw[i:i + 320].decode('ascii'))
    print('----- machine time block -----')
    j = raw.find(b'# Machine time (minutes, two digits)')
    print(raw[j - 120:j + 640].decode('ascii'))
    print('OK: machine time patched.')


if __name__ == '__main__':
    main()
