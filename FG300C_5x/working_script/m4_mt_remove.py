# -*- coding: ascii -*-
# m4_mt_remove.py
#
# Remove the ;(Machine time: ...) header line entirely, and drop the
# temporary DBG diagnostics. The tool-list format stays.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


OLD_HEADER = block(
    '   # Machine time (minutes, one digit)',
    '   if {[info exists mom_machine_time] && $mom_machine_time != ""} {',
    '      set mtime [format "%.1f" $mom_machine_time]',
    '      PB_CMD_output_comment ";(Machine time: $mtime MIN)"',
    '   }',
    '   if { [info exists mom_sys_tool_time] } {',
    '      MOM_output_to_listing_device "DBG hdr: mt=$mom_machine_time tool_time=EXISTS"',
    '   } else {',
    '      MOM_output_to_listing_device "DBG hdr: mt=$mom_machine_time tool_time=MISSING"',
    '   }',
)

OLD_DBG_ENDPATH = block(
    '   MOM_output_to_listing_device "DBG endpath: mt=$mom_machine_time cut=$mom_cutting_time add_cut=$mom_sys_add_cutting_time add_non=$mom_sys_add_non_cutting_time"',
)

OLD_DBG_ENDPROG = block(
    '   global mom_machine_time mom_cutting_time mom_sys_machine_time',
    '   MOM_output_to_listing_device "DBG endprog: mt=$mom_machine_time cut=$mom_cutting_time sys_mt=$mom_sys_machine_time"',
)

OLD_DBG_TOOLBODY = block(
    '   global mom_machine_time mom_sys_tool_time',
    '   set __ttex 0',
    '   if { [info exists mom_sys_tool_time] } { set __ttex 1 }',
    '   MOM_output_to_listing_device "DBG toolbody: tool=$mom_tool_name mt=$mom_machine_time tool_time=$__ttex"',
)


def main():
    raw = open(PATH, 'rb').read()

    if b'Machine time' not in raw and b'DBG ' not in raw:
        print('Already clean. No-op.')
        return

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    for name, old in [('header', OLD_HEADER), ('endpath', OLD_DBG_ENDPATH),
                      ('endprog', OLD_DBG_ENDPROG), ('toolbody', OLD_DBG_TOOLBODY)]:
        n = raw.count(old)
        assert n == 1, '%s: block found %d times' % (name, n)
        raw = raw.replace(old, b'')

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    print('Machine time remaining:', b'Machine time' in raw)
    print('DBG remaining:', b'DBG ' in raw)
    # show the header tail
    i = raw.find(b';(NC name:$ncname)')
    print(raw[i:i + 220].decode('ascii'))
    print('OK: machine time + diagnostics removed.')


if __name__ == '__main__':
    main()
