# -*- coding: ascii -*-
# Add the leading zero to the CAM tolerance assignment: 0.06 instead of .06.
# 1) new helper PB_CMD__format_cam_tolerance
# 2) Start of Path: emit "_camtolerance=..." via the helper instead of the
#    start_of_path_2 template (AbsCoord format drops the leading zero)
# 3) update the reference comment line
path = r'd:\Programs\repository\lomo-1\LOMO_FG300C.tcl'
raw = open(path, 'rb').read()

anchor_tpl = b'   MOM_do_template start_of_path_2\r\n'
assert raw.count(anchor_tpl) == 1, raw.count(anchor_tpl)
new_block = (b'   # _camtolerance from CAM (intol + outtol) with a leading zero (0.06, not .06)\r\n'
             b'   if { [info exists mom_inside_outside_tolerances] } {\r\n'
             b'      set cam_tolerance_total [expr {double($mom_inside_outside_tolerances(0)) + double($mom_inside_outside_tolerances(1))}]\r\n'
             b'      MOM_output_literal "_camtolerance=[PB_CMD__format_cam_tolerance $cam_tolerance_total]"\r\n'
             b'   }\r\n')
raw = raw.replace(anchor_tpl, new_block)

anchor_proc = b'#=============================================================\r\nproc PB_CMD_output_start_of_path { } {\r\n'
assert raw.count(anchor_proc) == 1, raw.count(anchor_proc)
helper = (b'#=============================================================\r\n'
          b'proc PB_CMD__format_cam_tolerance { value } {\r\n'
          b'#=============================================================\r\n'
          b'# Format a tolerance the way the post does (up to 4 decimals, trailing\r\n'
          b'# zeros suppressed) but keep the leading zero: 0.06 instead of .06.\r\n'
          b'   set text [format "%.4f" $value]\r\n'
          b'   regsub -all {0+$} $text "" text\r\n'
          b'   if { [string match "*." $text] } {\r\n'
          b'      append text "0"\r\n'
          b'   }\r\n'
          b'   return $text\r\n'
          b'}\r\n'
          b'\r\n'
          b'\r\n')
raw = raw.replace(anchor_proc, helper + anchor_proc)

raw = raw.replace(b'#     _camtolerance=.01\r\n', b'#     _camtolerance=0.01\r\n')

open(path, 'wb').write(raw)
print('OK: camtolerance patch applied')
