import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)

# ---- TCL ----
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()

# 1. handler: only "open" -> pb_doors_open_end, drop diagnostic and close
old = CR.join([
    b'proc PB_CMD_MOM_Automatic_doors { } {',
    b'#=============================================================',
    b'# UDE "Automatic doors" - snapshot the requested door action:',
    b'#   action "close"          -> pb_doors_close    (M58 at program start, before motion)',
    b'#   action "End of program" -> pb_doors_open_end (M57 at program end, after all SUPA)',
    b'   global mom_action pb_doors_close pb_doors_open_end',
    b'   if { [info exists mom_action] } {',
    b'      MOM_output_literal ";(DBG doors) action=[string toupper $mom_action]"',
    b'      set door_action [string tolower $mom_action]',
    b'      if { $door_action == "close" } {',
    b'         set pb_doors_close 1',
    b'      } elseif { $door_action == "end of program" } {',
    b'         set pb_doors_open_end 1',
    b'      }',
    b'   }',
    b'}',
]) + CR
new = CR.join([
    b'proc PB_CMD_MOM_Automatic_doors { } {',
    b'#=============================================================',
    b'# UDE "Automatic doors" - snapshot the requested door action:',
    b'#   action "open" -> pb_doors_open_end (M57 at program end, after all SUPA)',
    b'   global mom_action pb_doors_open_end',
    b'   if { [info exists mom_action] } {',
    b'      set door_action [string tolower $mom_action]',
    b'      if { $door_action == "open" } {',
    b'         set pb_doors_open_end 1',
    b'      }',
    b'   }',
    b'}',
]) + CR
b = rep(b, old, new, 'handler')

# 2. remove M58 from initial_move
old = CR.join([
    b'  global mom_programmed_feed_rate',
    b'',
    b'   # Automatic doors: close (M58) once, before the first cutting motion',
    b'   global pb_doors_close pb_doors_close_done',
    b'   if { [info exists pb_doors_close] && $pb_doors_close && ![info exists pb_doors_close_done] } {',
    b'      set pb_doors_close_done 1',
    b'      MOM_output_literal "M58"',
    b'   }',
    b'',
    b'   PB_CMD__output_3p2_retract',
]) + CR
new = CR.join([
    b'  global mom_programmed_feed_rate',
    b'',
    b'   PB_CMD__output_3p2_retract',
]) + CR
b = rep(b, old, new, 'rm-m58-init')

# 3. hardcode M58 in start_of_path (before SUPA)
old = CR.join([
    b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only',
    b'   # once at the program start, not on every operation.',
    b'   if { ![info exists pb_home_return_flag] } {',
    b'      set pb_home_return_flag 1',
    b'      MOM_do_template trafoof',
]) + CR
new = CR.join([
    b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only',
    b'   # once at the program start, not on every operation.',
    b'   if { ![info exists pb_home_return_flag] } {',
    b'      set pb_home_return_flag 1',
    b'',
    b'      # Automatic doors: close (M58) before the SUPA home return',
    b'      MOM_output_literal "M58"',
    b'',
    b'      MOM_do_template trafoof',
]) + CR
b = rep(b, old, new, 'm58-hardcode')

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
open(p, 'wb').write(b)
print('tcl ok', len(b))

# ---- CDL ----
p = os.path.join(BASE, 'LOMO_FG300C_ude.cdl')
b = open(p, 'rb').read()
old = CR.join([
    b'   PARAM action',
    b'   {',
    b'      TYPE o',
    b'      DEFVAL "close"',
    b'      OPTIONS "close","End of program"',
    b'      UI_LABEL "Action"',
    b'   }',
]) + CR
new = CR.join([
    b'   PARAM action',
    b'   {',
    b'      TYPE o',
    b'      DEFVAL "open"',
    b'      OPTIONS "open"',
    b'      UI_LABEL "Action"',
    b'   }',
]) + CR
b = rep(b, old, new, 'cdl')
open(p, 'wb').write(b)
print('cdl ok', len(b))
print('ALL DONE')
