import os, re
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = open(p, 'rb').read()
def rep(b, old, new, tag):
    n = b.count(old)
    assert n == 1, tag + ': ' + str(n)
    return b.replace(old, new)

# A. turn_block -> sign-aware IC
old = CR.join([
    b'proc PB_CMD__rotc_turn_block { } {',
    b'#=============================================================',
    b'# Single source of the rotary-table cutting block for the',
    b'# interpolation-lock mode. The tool stays stationary while table C',
    b'# rotates one full turn (slightly over 360 deg so the seam closes).',
    b'# Callers emit the matching G90 when the flat pass ends.',
    b'   MOM_output_literal "G1 G91 C-360.1 F200"',
    b'}',
]) + CR
new = CR.join([
    b'proc PB_CMD__rotc_turn_block { } {',
    b'#=============================================================',
    b'# Single source of the rotary-table cutting block for the',
    b'# interpolation-lock mode. The tool stays stationary while table C',
    b'# rotates one full turn (slightly over 360 deg so the seam closes).',
    b'# The sign comes from pb_lock_turn_sign (+ internal hole / - external boss).',
    b'# C=IC(...) rotates incrementally while keeping G90 absolute, so no',
    b'# G91/G90 pair is needed around the block.',
    b'   global pb_lock_turn_sign',
    b'   if { ![info exists pb_lock_turn_sign] } { set pb_lock_turn_sign -1 }',
    b'   set angle [format "%.1f" [expr $pb_lock_turn_sign * 360.1]]',
    b'   MOM_output_literal "G1 C=IC($angle) F200"',
    b'}',
]) + CR
b = rep(b, old, new, 'turn_block')

# B. arc_handle: globals
b = rep(b, b'  global mom_pos_arc_center mom_arc_radius' + CR,
           b'  global mom_pos_arc_center mom_arc_radius mom_arc_direction' + CR, 'arc-g1')
b = rep(b, b'  global pb_lock_arc_active pb_lock_arc_radius' + CR,
           b'  global pb_lock_arc_active pb_lock_arc_radius pb_lock_turn_sign' + CR, 'arc-g2')

# B2. arc_handle: sign before turn_block
old = CR.join([
    b'     if { $pb_lock_arc_active == 0 } {',
    b'        set pb_lock_arc_active 1',
    b'        set pb_lock_arc_radius $mom_arc_radius',
    b'        PB_CMD__rotc_turn_block',
    b'     }',
]) + CR
new = CR.join([
    b'     if { $pb_lock_arc_active == 0 } {',
    b'        set pb_lock_arc_active 1',
    b'        set pb_lock_arc_radius $mom_arc_radius',
    b'        set pb_lock_turn_sign -1',
    b'        if { [info exists mom_arc_direction] && $mom_arc_direction == "CCLW" } {',
    b'           set pb_lock_turn_sign 1',
    b'        }',
    b'        PB_CMD__rotc_turn_block',
    b'     }',
]) + CR
b = rep(b, old, new, 'arc-sign')

# B3. arc_handle: comment + remove G90
old = CR.join([
    b'  # Arc with a different center (engage approach / retract departure).',
    b'  # A just-finished working circle must be closed with G90 before the',
    b'  # departure arc is output (incremental C is still active). The literal',
    b'  # G1 block above does not update the post motion-G state, so force',
    b'  # G2/G3 so the retract arc starts with a circular code.',
    b'  if { $pb_lock_arc_active == 1 } {',
    b'     MOM_output_literal "G90"',
    b'     MOM_force Once G_motion',
    b'     set pb_lock_arc_active 0',
    b'  }',
]) + CR
new = CR.join([
    b'  # Arc with a different center (engage approach / retract departure).',
    b'  # The literal C=IC(...) block does not update the post motion-G state,',
    b'  # so force G2/G3 so the retract arc starts with a circular code.',
    b'  if { $pb_lock_arc_active == 1 } {',
    b'     MOM_force Once G_motion',
    b'     set pb_lock_arc_active 0',
    b'  }',
]) + CR
b = rep(b, old, new, 'arc-g90')

# C. linear_cut: globals
b = rep(b, b'   global pb_lock_cut_active pb_lock_cut_r pb_lock_prev_r pb_lock_prev_z' + CR,
           b'   global pb_lock_cut_active pb_lock_cut_r pb_lock_prev_r pb_lock_prev_z' + CR + b'   global pb_lock_prev_x pb_lock_prev_y pb_lock_turn_sign' + CR, 'lin-g')

# C2. linear_cut: init prev_x/prev_y
old = b'   if { ![info exists pb_lock_prev_z] }   { set pb_lock_prev_z  0.0 }' + CR
new = old + b'   if { ![info exists pb_lock_prev_x] }   { set pb_lock_prev_x  0.0 }' + CR + b'   if { ![info exists pb_lock_prev_y] }   { set pb_lock_prev_y  0.0 }' + CR
b = rep(b, old, new, 'lin-init')

# C3. linear_cut: sign before turn_block
old = CR.join([
    b'            # Just entered a flat run at (almost) constant radius around (0,0)',
    b'            set pb_lock_cut_active 1',
    b'            set pb_lock_cut_r $r',
    b'            PB_CMD_output_comment ";Cutting"',
    b'            PB_CMD__rotc_turn_block',
]) + CR
new = CR.join([
    b'            # Just entered a flat run at (almost) constant radius around (0,0)',
    b'            set pb_lock_cut_active 1',
    b'            set pb_lock_cut_r $r',
    b'            set pb_lock_turn_sign -1',
    b'            if { [expr $pb_lock_prev_x * $y - $pb_lock_prev_y * $x] > 0 } {',
    b'               set pb_lock_turn_sign 1',
    b'            }',
    b'            PB_CMD_output_comment ";Cutting"',
    b'            PB_CMD__rotc_turn_block',
]) + CR
b = rep(b, old, new, 'lin-sign')

# C4a. linear_cut: remove G90 (dZ branch)
old = CR.join([
    b'      if { $dZ > 0.01 } {',
    b'         MOM_output_literal "G90"',
    b'         set pb_lock_cut_active 0',
]) + CR
new = CR.join([
    b'      if { $dZ > 0.01 } {',
    b'         set pb_lock_cut_active 0',
]) + CR
b = rep(b, old, new, 'lin-g90a')

# C4b. linear_cut: remove G90 (radius exit)
old = CR.join([
    b'      # Left the circle radius -> stop rotary pass',
    b'      MOM_output_literal "G90"',
    b'      set pb_lock_cut_active 0',
]) + CR
new = CR.join([
    b'      # Left the circle radius -> stop rotary pass',
    b'      set pb_lock_cut_active 0',
]) + CR
b = rep(b, old, new, 'lin-g90b')

# C5. linear_cut: track prev_x/prev_y after each prev_z update
pat = rb'( *)set pb_lock_prev_z \$z' + CR
repl = rb'\1set pb_lock_prev_z $z' + CR + rb'\1set pb_lock_prev_x $x' + CR + rb'\1set pb_lock_prev_y $y' + CR
b, n = re.subn(pat, repl, b, count=4)
assert n == 4, 'lin-track: ' + str(n)

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
open(p, 'wb').write(b)
print('patched', len(b))
print('ALL DONE')
