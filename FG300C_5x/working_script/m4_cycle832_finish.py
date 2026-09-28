# -*- coding: ascii -*-
# m4_cycle832_finish.py
#
# 1) Remove the temporary CYCLE832 method diagnostic (DBG-CYCLE832 / DBG-MTHD).
# 2) Hardcode the CYCLE832 method to finishing (_FINISH) in the V7 branch.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


# The diagnostic block added by m4_cycle832_dbg.py (exact bytes).
DIAG = block(
    '',
    '   # DBG (temporary): reveal the CYCLE832 method source',
    '   global mom_oper_method',
    '   set __dbg "libref="',
    '   if {[info exists mom_cutmthd_libref]} { append __dbg $mom_cutmthd_libref } else { append __dbg "<none>" }',
    '   append __dbg " oper_method="',
    '   if {[info exists mom_oper_method]} { append __dbg $mom_oper_method } else { append __dbg "<none>" }',
    '   append __dbg " op_type=$mom_operation_type method=$mom_siemens_method ver=$sinumerik_version"',
    '   PB_CMD_output_comment ";(DBG-CYCLE832 $__dbg)"',
    '   foreach __g [uplevel #0 [list info globals mom_*]] {',
    '      if { [string match "*ethod*" $__g] || [string match "*mthd*" $__g] } {',
    '         if { ![uplevel #0 [list array exists $__g]] && [uplevel #0 [list info exists $__g]] } {',
    '            PB_CMD_output_comment ";(DBG-MTHD $__g=[uplevel #0 [list set $__g]])"',
    '         }',
    '      }',
    '   }',
)

HARDCODE = block(
    '            # Hardcoded: always finishing (per customer requirement).',
    '            set cycle832_tolm "_FINISH"',
)


def main():
    raw = open(PATH, 'rb').read()

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    # 1) remove the diagnostic
    n = raw.count(DIAG)
    assert n == 1, 'DIAG block found %d times (expected 1)' % n
    raw = raw.replace(DIAG, b'')

    # 2) hardcode the V7 branch (the first 'switch -- $mom_siemens_method {')
    s = raw.find(b'switch -- $mom_siemens_method {')
    assert s >= 0, 'V7 switch not found'
    d = raw.find(b'{set cycle832_tolm "_OFF"}', s)
    assert d > s, 'V7 default not found'
    e = raw.find(b'\r\n', d) + 2            # end of the default line
    e = raw.find(b'\r\n', e) + 2            # end of the closing '            }' line
    raw = raw[:s] + HARDCODE + raw[e:]

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    print('DBG remaining:', b'DBG' in raw)
    i = raw.find(b'Hardcoded: always finishing')
    print(raw[i - 80:i + 240].decode('ascii'))
    print('OK: diagnostic removed, CYCLE832 method hardcoded to _FINISH.')


if __name__ == '__main__':
    main()
