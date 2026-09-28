# -*- coding: ascii -*-
# m4_cycle832_dbg.py
#
# Temporary diagnostic: dump the CYCLE832 method source (mom_cutmthd_libref,
# mom_oper_method, mom_siemens_method, mom_operation_type, sinumerik_version,
# plus any mom_* globals containing "method"/"mthd") as NC comments, to find
# out why the CAM FINISH method is mapped to _OFF instead of _FINISH.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


ANCHOR = block(
    '   } else {',
    '',
    '      set mom_siemens_method "DESELECTION"',
    '   }',
)

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


def main():
    raw = open(PATH, 'rb').read()

    if b'DBG-CYCLE832' in raw:
        print('Already patched (DBG-CYCLE832 present). No-op.')
        return

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    n = raw.count(ANCHOR)
    assert n == 1, 'ANCHOR found %d times (expected 1)' % n
    raw = raw.replace(ANCHOR, ANCHOR + DIAG)

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    i = raw.find(b'DBG-CYCLE832')
    print(raw[i - 200:i + 700].decode('ascii'))
    print('OK: cycle832 diagnostic added.')


if __name__ == '__main__':
    main()
