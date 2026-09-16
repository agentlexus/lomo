import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
def rd(p): return open(os.path.join(BASE, p), 'rb').read()
def wr(p, b): open(os.path.join(BASE, p), 'wb').write(b)
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': found ' + str(n)
    return b.replace(old, new)

# 1. CDL: add Automatic_doors event
b = rd('LOMO_FG300C_ude.cdl')
old = CR.join([b'      UI_LABEL "ASCALE index"', b'   }', b'}']) + CR
new = CR.join([
    b'      UI_LABEL "ASCALE index"', b'   }', b'}',
    b'',
    b'EVENT Automatic_doors',
    b'{',
    b'   UI_LABEL "Automatic doors"',
    b'   CATEGORY MILL DRILL LATHE',
    b'   PARAM action',
    b'   {',
    b'      TYPE o',
    b'      DEFVAL "close"',
    b'      OPTIONS "close","End of program"',
    b'      UI_LABEL "Action"',
    b'   }',
    b'}',
]) + CR
b = rep(b, old, new, 'cdl')
wr('LOMO_FG300C_ude.cdl', b)
print('cdl ok', len(b))

# 2. PUI: register the UDE
b = rd('LOMO_FG300C.pui')
old = b'{Interpolation_lock}       {PB_CMD_MOM_Interpolation_lock}  {Interpolation lock} {UDE}' + CR
new = old + b'{Automatic_doors}          {PB_CMD_MOM_Automatic_doors}  {Automatic doors} {UDE}' + CR
b = rep(b, old, new, 'pui')
wr('LOMO_FG300C.pui', b)
print('pui ok', len(b))

# 3. TCL: handler procs
b = rd('LOMO_FG300C.tcl')
old = CR.join([b'#=============================================================', b'proc MOM_nurbs_move { } {']) + CR
new = CR.join([
    b'#=============================================================',
    b'proc MOM_Automatic_doors { } {',
    b'#=============================================================',
    b'# UDE "Automatic doors" - door control (see PB_CMD_MOM_Automatic_doors).',
    b'   global mom_action',
    b'   PB_CMD_MOM_Automatic_doors',
    b'}',
    b'',
    b'',
    b'#=============================================================',
    b'proc PB_CMD_MOM_Automatic_doors { } {',
    b'#=============================================================',
    b'# UDE "Automatic doors" - snapshot the requested door action:',
    b'#   action "close"          -> pb_doors_close    (M58 at program start, before motion)',
    b'#   action "End of program" -> pb_doors_open_end (M57 at program end, after all SUPA)',
    b'   global mom_action pb_doors_close pb_doors_open_end',
    b'   if { [info exists mom_action] } {',
    b'      if { [string match "close" $mom_action] } {',
    b'         set pb_doors_close 1',
    b'      } elseif { [string match "End of program" $mom_action] } {',
    b'         set pb_doors_open_end 1',
    b'      }',
    b'   }',
    b'}',
    b'',
    b'',
    b'#=============================================================',
    b'proc MOM_nurbs_move { } {',
]) + CR
b = rep(b, old, new, 'tcl-handler')

# 4. TCL: M58 at program start (before home return / any movement)
old = CR.join([b'   PB_CMD_set_fixture_offset', b'', b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only']) + CR
new = CR.join([
    b'   PB_CMD_set_fixture_offset',
    b'',
    b'   # Automatic doors: close (M58) before any movement',
    b'   global pb_doors_close',
    b'   if { [info exists pb_doors_close] && $pb_doors_close } {',
    b'      MOM_output_literal "M58"',
    b'   }',
    b'',
    b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only',
]) + CR
b = rep(b, old, new, 'tcl-m58')

# 5. TCL: M57 at very end (after all SUPA, before M30)
old = CR.join([b'   MOM_do_template tool_change_return_home_AC', b'', b'   MOM_do_template end_of_program']) + CR
new = CR.join([
    b'   MOM_do_template tool_change_return_home_AC',
    b'',
    b'   # Automatic doors: open (M57) at the very end, after all SUPA',
    b'   global pb_doors_open_end',
    b'   if { [info exists pb_doors_open_end] && $pb_doors_open_end } {',
    b'      MOM_output_literal "M57"',
    b'   }',
    b'',
    b'   MOM_do_template end_of_program',
]) + CR
b = rep(b, old, new, 'tcl-m57')

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
wr('LOMO_FG300C.tcl', b)
print('tcl ok', len(b))
print('ALL DONE')
