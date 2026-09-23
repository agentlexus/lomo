# -*- coding: ascii -*-
# m4_header_tool_list.py
#
# Fix the program-header tool list format to match the reference header:
#     ;(T3=D16-54-100L-T3 D=16. R=0. H01 D00 ...)
#
# The previous code stored the tool line as "NAME SUBTYPE DIA COR RAD FLUTE ADJ"
# (in MOM_TOOL_BODY) but parsed it as "NUMBER NAME DIA COR RAD FLUTE ADJ"
# (in PB_CMD_creat_tool_list_2), producing garbage like
#     ;(T;D16-54-100L-T3=MILL D=16.0000 DR_angle=0.0000 H1 D00)
#
# Change: MOM_TOOL_BODY now also stores the individual fields, and
# PB_CMD_creat_tool_list_2 builds the reference-format line from them.

import sys

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\LOMO_FG300C.tcl'

CRLF = b'\r\n'


def block(*lines):
    return CRLF.join(l.encode('ascii') for l in lines) + CRLF


HELPER = block(
    '#=============================================================',
    'proc PB_CMD__fmt_toolval { value } {',
    '#=============================================================',
    '# Format a tool dimension the way the reference header shows it:',
    '# trailing zeros stripped, a trailing dot kept for whole numbers',
    '# (16. , 0. , -6. , 16.5).',
    '   set text [format "%.3f" $value]',
    '   regsub -all {0+$} $text "" text',
    '   return $text',
    '}',
    '',
    '',
)

FIELDS = block(
    '   set tool_data_buffer($mom_tool_name,number) $mom_tool_number',
    '   set tool_data_buffer($mom_tool_name,name)   $mom_tool_name',
    '   set tool_data_buffer($mom_tool_name,dia)    $mom_tool_diameter',
    '   set tool_data_buffer($mom_tool_name,rad)    $mom_tool_corner1_radius',
    '   set tool_data_buffer($mom_tool_name,adj)    $mom_tool_length_adjust_register',
    '',
)

NEW_LOOP = block(
    '      if { [info exists tool_data_buffer($tool,number)] } {',
    '         set tnum $tool_data_buffer($tool,number)',
    '         set tname $tool_data_buffer($tool,name)',
    '         set tdia  $tool_data_buffer($tool,dia)',
    '         set trad  $tool_data_buffer($tool,rad)',
    '         set tadj  $tool_data_buffer($tool,adj)',
    '         incr tool_count',
    '         if { $tool_list_output != "" } {',
    '            append tool_list_output "\\n"',
    '         }',
    '         append tool_list_output ";(T${tnum}=${tname} D=[PB_CMD__fmt_toolval $tdia] R=[PB_CMD__fmt_toolval $trad] H[format %02d $tadj] D00)"',
    '      }',
)


def main():
    raw = open(PATH, 'rb').read()

    if b'PB_CMD__fmt_toolval' in raw:
        print('Already patched (PB_CMD__fmt_toolval present). No-op.')
        return

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL before patch'
    assert max(raw) < 128, 'non-ASCII byte before patch'

    # E1: insert the helper proc before PB_CMD_creat_tool_list_2
    a = raw.find(b'proc PB_CMD_creat_tool_list_2 { } {')
    assert a >= 0, 'anchor: creat_tool_list_2 header not found'
    raw = raw[:a] + HELPER + raw[a:]

    # E2: store individual fields in MOM_TOOL_BODY
    b = raw.find(b'   set tool_data_buffer($mom_tool_name,output) "$co$output$tool_time$ci"')
    assert b >= 0, 'anchor: tool_data_buffer output not found'
    raw = raw[:b] + FIELDS + raw[b:]

    # E3: replace the parse loop with field access
    s = raw.find(b'      if [info exists tool_data_buffer($tool,output)] {')
    e = raw.find(b'      set prev_tool_type $tool_type', s)
    assert s >= 0 and e > s, 'anchor: output loop not found'
    raw = raw[:s] + NEW_LOOP + raw[e:]

    assert raw.count(b'\r') == raw.count(b'\n'), 'mixed EOL after patch'
    assert max(raw) < 128, 'non-ASCII byte after patch'
    assert raw.count(b'{') == raw.count(b'}'), 'brace imbalance after patch'

    open(PATH, 'wb').write(raw)

    print('----- PB_CMD__fmt_toolval -----')
    i = raw.find(b'proc PB_CMD__fmt_toolval')
    print(raw[i:i + 480].decode('ascii'))
    print('----- field storage -----')
    j = raw.find(b'set tool_data_buffer($mom_tool_name,number)')
    print(raw[j - 80:j + 420].decode('ascii'))
    print('----- output loop -----')
    k = raw.find(b'if { [info exists tool_data_buffer($tool,number)] }')
    print(raw[k - 80:k + 720].decode('ascii'))
    print('OK: tool list format patched.')


if __name__ == '__main__':
    main()
