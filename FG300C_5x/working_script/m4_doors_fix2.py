import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)

# 1. diagnostic in handler
old = CR.join([
    b'   global mom_action pb_doors_close pb_doors_open_end',
    b'   if { [info exists mom_action] } {',
    b'      set door_action [string tolower $mom_action]',
]) + CR
new = CR.join([
    b'   global mom_action pb_doors_close pb_doors_open_end',
    b'   if { [info exists mom_action] } {',
    b'      MOM_output_literal ";(DBG doors) action=[string toupper $mom_action]"',
    b'      set door_action [string tolower $mom_action]',
]) + CR
b = rep(b, old, new, 'diag')

# 2. remove M58 from start_of_path (restore original)
old = CR.join([
    b'   PB_CMD_set_fixture_offset',
    b'',
    b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only',
    b'   # once at the program start, not on every operation.',
    b'   if { ![info exists pb_home_return_flag] } {',
    b'      set pb_home_return_flag 1',
    b'',
    b'      # Automatic doors: close (M58) before any movement',
    b'      global pb_doors_close',
    b'      if { [info exists pb_doors_close] && $pb_doors_close } {',
    b'         MOM_output_literal "M58"',
    b'      }',
    b'',
    b'      MOM_do_template trafoof',
]) + CR
new = CR.join([
    b'   PB_CMD_set_fixture_offset',
    b'',
    b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only',
    b'   # once at the program start, not on every operation.',
    b'   if { ![info exists pb_home_return_flag] } {',
    b'      set pb_home_return_flag 1',
    b'      MOM_do_template trafoof',
]) + CR
b = rep(b, old, new, 'rm-m58')

# 3. insert M58 in initial_move (once)
old = CR.join([
    b'  global mom_programmed_feed_rate',
    b'',
    b'   PB_CMD__output_3p2_retract',
]) + CR
new = CR.join([
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
b = rep(b, old, new, 'ins-m58')

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
open(p, 'wb').write(b)
print('patched', len(b))
