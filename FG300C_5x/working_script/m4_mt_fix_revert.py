# -*- coding: ascii -*-
# m4_mt_fix_revert.py
#
# Emergency fix: the previous machine-time change called
#     MOM_cycle_objects {SETUP {PROGRAMVIEW {MEMBERS {OPERATION}}}}
# which NX 2312 does not support (error 65 "Can not find translation for
# type: OPERATION"), aborting the post at the header. This script:
#   1. restores the header machine-time block to the previous working form,
#   2. reverts MOM_OPER_BODY to the empty stub,
#   3. adds temporary listing diagnostics (DBG ...) to learn where the real
#      machine time is available.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


OLD_HEADER = block(
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

NEW_HEADER = block(
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

OLD_OPER = block(
    'proc MOM_OPER_BODY  {} {',
    '   global mom_machine_time pb_program_time',
    '   if { ![info exists pb_program_time] } { set pb_program_time 0.0 }',
    '   if { [info exists mom_machine_time] && $mom_machine_time != "" } {',
    '      set pb_program_time [expr $pb_program_time + $mom_machine_time]',
    '   }',
    '}',
)

NEW_OPER = block('proc MOM_OPER_BODY  {} {}')

DBG_ENDPATH = block(
    '   MOM_output_to_listing_device "DBG endpath: mt=$mom_machine_time cut=$mom_cutting_time add_cut=$mom_sys_add_cutting_time add_non=$mom_sys_add_non_cutting_time"',
)

DBG_ENDPROG = block(
    '   global mom_machine_time mom_cutting_time mom_sys_machine_time',
    '   MOM_output_to_listing_device "DBG endprog: mt=$mom_machine_time cut=$mom_cutting_time sys_mt=$mom_sys_machine_time"',
)

DBG_TOOLBODY = block(
    '   global mom_machine_time mom_sys_tool_time',
    '   set __ttex 0',
    '   if { [info exists mom_sys_tool_time] } { set __ttex 1 }',
    '   MOM_output_to_listing_device "DBG toolbody: tool=$mom_tool_name mt=$mom_machine_time tool_time=$__ttex"',
)


def main():
    raw = open(PATH, 'rb').read()

    if b'DBG endprog' in raw:
        print('Already patched (DBG endprog present). No-op.')
        return

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    # A: restore the header machine-time block
    n = raw.count(OLD_HEADER)
    assert n == 1, 'OLD_HEADER found %d times' % n
    raw = raw.replace(OLD_HEADER, NEW_HEADER)

    # B: revert MOM_OPER_BODY
    n = raw.count(OLD_OPER)
    assert n == 1, 'OLD_OPER found %d times' % n
    raw = raw.replace(OLD_OPER, NEW_OPER)

    # C: diagnostic in MOM_end_of_path (after MOM_reload_variable mom_machine_time)
    a = raw.find(b'   MOM_reload_variable mom_machine_time')
    assert a >= 0, 'anchor: MOM_reload_variable mom_machine_time not found'
    a = raw.find(b'\r\n', a) + 2
    raw = raw[:a] + DBG_ENDPATH + raw[a:]

    # D: diagnostic in MOM_end_of_program (after LIST_FILE_TRAILER)
    d = raw.find(b'   LIST_FILE_TRAILER')
    assert d >= 0, 'anchor: LIST_FILE_TRAILER not found'
    d = raw.find(b'\r\n', d) + 2
    raw = raw[:d] + DBG_ENDPROG + raw[d:]

    # E: diagnostic in MOM_TOOL_BODY (before the field storage)
    e = raw.find(b'   set tool_data_buffer($mom_tool_name,number) $mom_tool_number')
    assert e >= 0, 'anchor: tool_data_buffer number not found'
    raw = raw[:e] + DBG_TOOLBODY + raw[e:]

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    for tag in [b'# Machine time (minutes, one digit)',
                b'proc MOM_OPER_BODY',
                b'DBG endpath',
                b'DBG endprog',
                b'DBG toolbody']:
        i = raw.find(tag)
        print('-----', tag.decode('ascii'), '-----')
        print(raw[i - 40:i + 260].decode('ascii'))
    print('OK: revert + diagnostics applied.')


if __name__ == '__main__':
    main()
