import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)

# Fix 1: case-insensitive action compare
old = CR.join([
    b'   if { [info exists mom_action] } {',
    b'      if { [string match "close" $mom_action] } {',
    b'         set pb_doors_close 1',
    b'      } elseif { [string match "End of program" $mom_action] } {',
    b'         set pb_doors_open_end 1',
    b'      }',
    b'   }',
]) + CR
new = CR.join([
    b'   if { [info exists mom_action] } {',
    b'      set door_action [string tolower $mom_action]',
    b'      if { $door_action == "close" } {',
    b'         set pb_doors_close 1',
    b'      } elseif { $door_action == "end of program" } {',
    b'         set pb_doors_open_end 1',
    b'      }',
    b'   }',
]) + CR
b = rep(b, old, new, 'handler')

# Fix 2: M58 only once (inside pb_home_return_flag guard)
old = CR.join([
    b'   PB_CMD_set_fixture_offset',
    b'',
    b'   # Automatic doors: close (M58) before any movement',
    b'   global pb_doors_close',
    b'   if { [info exists pb_doors_close] && $pb_doors_close } {',
    b'      MOM_output_literal "M58"',
    b'   }',
    b'',
    b'   # Return home (TRAFOOF / CYCLE800 / SUPA ...) is output only',
    b'   # once at the program start, not on every operation.',
    b'   if { ![info exists pb_home_return_flag] } {',
    b'      set pb_home_return_flag 1',
    b'      MOM_do_template trafoof',
]) + CR
new = CR.join([
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
b = rep(b, old, new, 'm58')

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
open(p, 'wb').write(b)
print('patched', len(b))
