# -*- coding: ascii -*-
# m4_tool_change_fix.py
#
# Fix: the post drops the tool change for the second (and later) tools.
#
# Cause: PB_auto_tool_change used the one-shot flag mom_sys_first_tool_handled
# to suppress a "duplicate" MOM_tool_change for the first tool. The flag was
# only ever cleared by that guard, so when the program's SECOND tool arrived,
# MOM_first_tool routed it to MOM_tool_change -> PB_auto_tool_change, the
# guard fired and swallowed the whole change block. The second operation then
# kept machining with the first tool (T3 instead of T6).
#
# Fix: suppress a repeated change by TOOL NUMBER (pb_last_tool_change_number),
# not by "first time". A change to another tool is always output in full.
# MOM_tool_change dispatch is made total so no path can drop the event.
#
# Run:  python working_script/m4_tool_change_fix.py

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    """Join ASCII lines into a CRLF-terminated byte block."""
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


# PB_auto_tool_change: replace the one-shot flag guard with a per-tool check.
OLD_A = block(
    '   global mom_sys_first_tool_handled',
    '',
    '   # After the first change (MOM_first_tool -> PB_CMD_output_first_tool)',
    '   # Post Builder additionally calls MOM_tool_change.',
    '   # If the first tool was already fully output, skip the repeat.',
    '   if {[info exists mom_sys_first_tool_handled] && $mom_sys_first_tool_handled == 1} {',
    '      set mom_sys_first_tool_handled 0',
    '      return',
    '   }',
)

NEW_A = block(
    '   global pb_last_tool_change_number',
    '',
    '   # The first tool block is emitted by PB_CMD_output_first_tool',
    '   # (MOM_first_tool). Skip only a repeated change for the SAME tool:',
    '   # a change to another tool must always be output in full, otherwise',
    '   # the operation would be machined with the previous tool.',
    '   if { [info exists mom_tool_number] && [info exists pb_last_tool_change_number] \\',
    '        && $pb_last_tool_change_number == $mom_tool_number } {',
    '      return',
    '   }',
    '',
    '   if { [info exists mom_tool_number] } {',
    '      set pb_last_tool_change_number $mom_tool_number',
    '   }',
)

# PB_CMD_output_first_tool: remember the tool number it emitted.
OLD_B = block(
    '   PB_CMD_output_comment ";(First Tool)"',
)

NEW_B = block(
    '   global mom_tool_number pb_last_tool_change_number',
    '',
    '   # Remember which tool this first-tool block belongs to: a repeated',
    '   # MOM_tool_change for the same tool must not be output twice.',
    '   if { [info exists mom_tool_number] } {',
    '      set pb_last_tool_change_number $mom_tool_number',
    '   }',
    '',
    '   PB_CMD_output_comment ";(First Tool)"',
)

# MOM_tool_change: make the dispatch total so no path can drop the event.
OLD_C = block(
    '   if { [info exists mom_tool_change_type] } {',
    '      switch $mom_tool_change_type {',
    '         MANUAL { PB_manual_tool_change }',
    '         AUTO   { PB_auto_tool_change }',
    '      }',
    '   } elseif { [info exists mom_manual_tool_change] } {',
    '      if { ![string compare $mom_manual_tool_change "TRUE"] } {',
    '         PB_manual_tool_change',
    '      }',
    '   }',
)

NEW_C = block(
    '   if { [info exists mom_tool_change_type] } {',
    '      switch $mom_tool_change_type {',
    '         MANUAL  { PB_manual_tool_change }',
    '         AUTO    { PB_auto_tool_change }',
    '         default { PB_auto_tool_change }',
    '      }',
    '   } elseif { [info exists mom_manual_tool_change] } {',
    '      if { ![string compare $mom_manual_tool_change "TRUE"] } {',
    '         PB_manual_tool_change',
    '      } else {',
    '         PB_auto_tool_change',
    '      }',
    '   } else {',
    '      PB_auto_tool_change',
    '   }',
)


def region(raw, needle, span):
    i = raw.find(needle)
    assert i >= 0, 'missing marker: ' + needle
    print('----- %s -----' % needle)
    print(raw[i:i + span].decode('ascii'))
    print()


def main():
    raw = open(PATH, 'rb').read()

    if b'pb_last_tool_change_number' in raw:
        print('Already patched: pb_last_tool_change_number present. No-op.')
        return

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII bytes present before patch'

    repl = [
        ('PB_auto_tool_change', OLD_A, NEW_A),
        ('PB_CMD_output_first_tool', OLD_B, NEW_B),
        ('MOM_tool_change', OLD_C, NEW_C),
    ]

    for name, old, new in repl:
        n = raw.count(old)
        assert n == 1, '%s: anchor found %d times (expected 1)' % (name, n)
        raw = raw.replace(old, new)

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII bytes after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    region(raw, b'proc MOM_tool_change', 1700)
    region(raw, b'proc PB_auto_tool_change', 3400)
    region(raw, b'proc PB_CMD_output_first_tool', 1800)

    print('OK: LOMO_FG300C.tcl patched (tool change emitted for every tool).')


if __name__ == '__main__':
    main()
