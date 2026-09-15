# -*- coding: utf-8 -*-
# End-of-operation cleanup for 3+2:
#   1) CYCLE800() close at end of path when the operation used CYCLE800 (3+2).
#      Reuses the existing (previously unused) PB_CMD__check_block_reset_cycle800.
#   2) SUPA G0 Z0.0 retract right before a 3+2 operation (with no tool change in
#      between), so the tool clears the part before CYCLE800 swivels the table.
#      NX has no look-ahead for the next operation's type, so the retract is
#      emitted from the start of the 3+2 operation and lands between the previous
#      ;(End of Path) and the 3+2 positioning.
#   3) README: history + modes section.
import os

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'
data = {}


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        data[name] = f.read()
    return data[name]


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def rep(name, tag, old, new):
    raw = data[name]
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d' % (tag, n)
    data[name] = raw.replace(old, new)
    print('   ok  %s' % tag)


# ------------------------------------------------------------------ .tcl
tcl = load('LOMO_FG300C.tcl')
BR_OPEN = tcl.count(b'{')
BR_CLOSE = tcl.count(b'}')

# 1) helper procs, inserted right before PB_CMD_m50_m52_unlock
ANCHOR_M52 = block('#=============================================================\n'
                  'proc PB_CMD_m50_m52_unlock { } {')
rep('LOMO_FG300C.tcl', 'tcl/new helpers PB_CMD__is_3p2 + PB_CMD__output_3p2_retract',
    ANCHOR_M52,
    block('''
#=============================================================
proc PB_CMD__is_3p2 { } {
#=============================================================
# Return 1 if the current operation is a positioned 3+2 operation
# (CYCLE800 / A-C rotation frame), 0 otherwise. Same condition as the
# 3+2 branch in PB_CMD__mode_comment: not the interpolation-lock mode,
# not continuous 5-axis, and mom_siemens_coord_rotation != 0.
   global mom_siemens_coord_rotation
   if { [PB_CMD__lock_mode] } { return 0 }
   if { [PB_CMD_detect_5axis_tool_path] } { return 0 }
   if { [info exists mom_siemens_coord_rotation] && $mom_siemens_coord_rotation != 0 } { return 1 }
   return 0
}


#=============================================================
proc PB_CMD__output_3p2_retract { } {
#=============================================================
# Retract Z to the machine reference point (SUPA G0 Z0.0) right before a
# 3+2 operation, so the tool clears the part before the table is swivelled
# by CYCLE800. Emitted only when:
#   - this is not the first operation in the program;
#   - no tool change happened right before this operation (a tool change
#     already retracts to the reference point);
#   - the current operation really is 3+2.
# pb_3p2_retract_done guards against the First-Move and Initial-Move chains
# emitting the retract twice for the same operation.
   global pb_operation_count pb_3p2_retract_done pb_next_oper_has_tool_change
   if { ![info exists pb_operation_count] || $pb_operation_count <= 1 } { return }
   if { [info exists pb_3p2_retract_done] && $pb_3p2_retract_done } { return }
   if { [info exists pb_next_oper_has_tool_change] && $pb_next_oper_has_tool_change } { return }
   if { ![PB_CMD__is_3p2] } { return }
   set pb_3p2_retract_done 1
   MOM_suppress Once D
   MOM_force Once Text G_motion
   MOM_do_template tool_change_return_home_Z
}
''') + CR + CR + ANCHOR_M52)

# 2) operation counter + once-flag reset at the start of every operation
rep('LOMO_FG300C.tcl', 'tcl/MOM_start_of_path operation counter',
    block('''  global mom_sys_in_operation
   set mom_sys_in_operation 1'''),
    block('''  global mom_sys_in_operation
   set mom_sys_in_operation 1

   global pb_operation_count pb_3p2_retract_done
   if { ![info exists pb_operation_count] } { set pb_operation_count 0 }
   incr pb_operation_count
   set pb_3p2_retract_done 0'''))

# 3) First-Move chain: retract before a 3+2 operation
rep('LOMO_FG300C.tcl', 'tcl/MOM_first_move retract before 3+2',
    block('''   PB_CMD_detect_operation_type
   PB_CMD_define_feed_variable_value

   MOM_do_template g17'''),
    block('''   PB_CMD_detect_operation_type
   PB_CMD_define_feed_variable_value

   PB_CMD__output_3p2_retract

   MOM_do_template g17'''))

# 4) Initial-Move chain: retract before a 3+2 operation
rep('LOMO_FG300C.tcl', 'tcl/PB_CMD_output_initial_move retract before 3+2',
    block('''  global mom_programmed_feed_rate

   MOM_do_template g17'''),
    block('''  global mom_programmed_feed_rate

   PB_CMD__output_3p2_retract

   MOM_do_template g17'''))

# 5) end of path: close CYCLE800 (reset the 3+2 swivel frame)
rep('LOMO_FG300C.tcl', 'tcl/output_end_of_path close CYCLE800',
    block('''   # Switch CYCLE832 off
   if { [PB_CMD__check_block_reset_cycle832] } {
      MOM_do_template reset_cycle832
   }'''),
    block('''   # Close CYCLE800 (reset the 3+2 swivel frame) when the operation used it
   if { [PB_CMD__check_block_reset_cycle800] } {
      MOM_do_template reset_cycle800
   }

   # Switch CYCLE832 off
   if { [PB_CMD__check_block_reset_cycle832] } {
      MOM_do_template reset_cycle832
   }'''))

# 6) end of path: remember whether the next operation has a tool change
rep('LOMO_FG300C.tcl', 'tcl/output_end_of_path tool-change flag',
    block('''   MOM_output_literal ";(End of Path)"

   PB_CMD_reset_control_mode'''),
    block('''   MOM_output_literal ";(End of Path)"

   # Remember whether the next operation has a tool change: the 3+2 retract
   # (SUPA G0 Z0.0) must only be emitted when there is NO tool change, because
   # a tool change already retracts to the reference point.
   global mom_next_oper_has_tool_change pb_next_oper_has_tool_change
   set pb_next_oper_has_tool_change 0
   if { [info exists mom_next_oper_has_tool_change] && $mom_next_oper_has_tool_change == "YES" } {
      set pb_next_oper_has_tool_change 1
   }

   PB_CMD_reset_control_mode'''))

# ------------------------------------------------------------------ README
def blocku(text):
    return CR.join(l.encode('utf-8') for l in text.strip('\n').split('\n')) + CR


load('README.md')

# modes section: document the end-of-operation cleanup
rep('README.md', 'readme/режимы (конец операции)',
    blocku('(`MOM_first_move`), поэтому режим помечается в каждой операции.'),
    blocku('''(`MOM_first_move`), поэтому режим помечается в каждой операции.

В конце операции 3+2 выводится `CYCLE800()` (сброс разворота стола); перед
3+2 операцией без смены инструмента — ретракт `SUPA G0 Z0.0`, чтобы фреза
отошла от детали до разворота стола.'''))

# history entry
rep('README.md', 'readme/история (3+2 cleanup)',
    blocku('## Примечание'),
    blocku('''- 2026-09-14: в конце 3+2 операции закрывается `CYCLE800()` (существующий
  `PB_CMD__check_block_reset_cycle800`), а перед 3+2 операцией, идущей без смены
  инструмента, выводится ретракт `SUPA G0 Z0.0` (новые `PB_CMD__is_3p2` +
  `PB_CMD__output_3p2_retract`, вызываются в First-Move и Initial-Move цепочках).

## Примечание'''))

# ---------------------------------------------------------------- write + check
for name in ('LOMO_FG300C.tcl', 'README.md'):
    raw = data[name]
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    with open(os.path.join(BASE, name), 'wb') as f:
        f.write(raw)
    print('   written %-18s %d bytes' % (name, len(raw)))

t = data['LOMO_FG300C.tcl']
assert max(t) < 128, 'tcl: non-ASCII byte written'
print('   tcl brace delta { %+d  } %+d' % (t.count(b'{') - BR_OPEN, t.count(b'}') - BR_CLOSE))
assert (t.count(b'{') - BR_OPEN) == (t.count(b'}') - BR_CLOSE), 'unbalanced braces'
for pat in (b'proc PB_CMD__is_3p2 { } {', b'proc PB_CMD__output_3p2_retract { } {',
            b'PB_CMD__check_block_reset_cycle800', b'PB_CMD__output_3p2_retract',
            b'pb_next_oper_has_tool_change', b'pb_operation_count'):
    print('   count %-42s %d' % (pat.decode(), t.count(pat)))
r = data['README.md'].decode('utf-8')
for m in ('CYCLE800()', 'SUPA G0 Z0.0', 'PB_CMD__output_3p2_retract'):
    assert m in r, m
    print('   README has %r' % m)
print('ALL DONE')

