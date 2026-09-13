# -*- coding: ascii -*-
# Custom UDE "Interpolation_lock" for the LOMO_FG300C post.
# Files are ASCII + CRLF, so every edit is done byte-wise (like the other
# scripts in working_script/).
#   1) .cdl : declare EVENT Interpolation_lock (status / axis / plane / ASCALE)
#   2) .pui : register the UDE and its handler
#   3) .tcl : lock mode is driven by this UDE only; R1 is taken from
#             PARAM ASCALE_value; R1/ASCALE are emitted in lock mode only.
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'
data = {}


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        data[name] = f.read()
    return data[name]


def block(text):
    """LF separated text -> ASCII bytes with CRLF and one trailing CRLF."""
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def rep(name, tag, old, new):
    raw = data[name]
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d occurrence(s)' % (tag, n)
    data[name] = raw.replace(old, new)
    print('   ok  %s' % tag)


def save(name):
    raw = data[name]
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    assert max(raw) < 128, '%s: non-ASCII byte written' % name
    with open(os.path.join(BASE, name), 'wb') as f:
        f.write(raw)


# ---------------------------------------------------------------- .cdl
load('LOMO_FG300C.cdl')
rep('LOMO_FG300C.cdl', 'cdl/EVENT Interpolation_lock',
    b'EVENT tool_preselect',
    block('''
EVENT Interpolation_lock
{
   UI_LABEL "Interpolation lock"
   CATEGORY MILL DRILL LATHE
   PARAM command_status
   {
      TYPE o
      DEFVAL "Active"
      OPTIONS "Active","Inactive"
      UI_LABEL "Status"
   }
   PARAM lock_axis
   {
      TYPE o
      DEFVAL "Fourth"
      OPTIONS "Fourth","Off"
      UI_LABEL "Interpolation Axis"
   }
   PARAM lock_axis_plane
   {
      TYPE o
      DEFVAL "XYPLAN"
      OPTIONS "XYPLAN","NONE"
      UI_LABEL "Locked Interpolation"
   }
   PARAM ASCALE_value
   {
      TYPE d
      DEFVAL "1.000"
      TOGGLE Off
      UI_LABEL "ASCALE index"
   }
}
''') + CR + b'EVENT tool_preselect')
# (files are written at the end: nothing is touched unless every step passed)

# ---------------------------------------------------------------- .pui
load('LOMO_FG300C.pui')
rep('LOMO_FG300C.pui', 'pui/UDE table row',
    b'{Interpolation Lock} {UDE}',
    b'{Interpolation Lock} {UDE}' + CR +
    b'{Interpolation_lock}       {PB_CMD_MOM_Interpolation_lock}  {Interpolation lock} {UDE}')
BS = chr(92)


def lc(text):
    """Append the .pui line-continuation backslash."""
    return (text + ' ' + BS).encode('ascii')


rep('LOMO_FG300C.pui', 'pui/Custom Command row',
    lc('{"PB_CMD_MOM_interpolation_lock" "" "Custom Command"}'),
    lc('{"PB_CMD_MOM_interpolation_lock" "" "Custom Command"}') + CR +
    lc('      {"PB_CMD_MOM_Interpolation_lock" "" "Custom Command"}'))
# ================================================================ TCL
tcl = load('LOMO_FG300C.tcl')
BRACE_OPEN = tcl.count(b'{')
BRACE_CLOSE = tcl.count(b'}')

# --- new lock-mode helpers, inserted right before PB_CMD__rotc_linear_cut ---
ANCHOR_LC = block('#=============================================================\n'
                  'proc PB_CMD__rotc_linear_cut { } {')
rep('LOMO_FG300C.tcl', 'tcl/helpers PB_CMD__lock_mode + _apply',
    ANCHOR_LC,
    block('''
#=============================================================
proc PB_CMD__lock_mode { } {
#=============================================================
# Single source of truth for the rotary-table interpolation-lock mode.
# Accepted ONLY from the UDE "Interpolation_lock":
#    command_status  = Active
#    lock_axis       = Fourth   (rotary table C)
#    lock_axis_plane = XYPLAN   (planar XY pass)
# The verdict is cached in pb_lock_mode for the current operation.
   global pb_lock_req pb_lock_axis_req pb_lock_plane_req pb_lock_mode
   set pb_lock_mode 0
   if { [info exists pb_lock_req] && $pb_lock_req == 1 } {
      if { [info exists pb_lock_axis_req] && $pb_lock_axis_req == "Fourth" } {
         if { [info exists pb_lock_plane_req] && $pb_lock_plane_req == "XYPLAN" } {
            set pb_lock_mode 1
         }
      }
   }
   return $pb_lock_mode
}

#=============================================================
proc PB_CMD__lock_mode_apply { } {
#=============================================================
# Publish the lock-mode verdict into mom_ude_interpolation_lock - the state
# variable read by the rest of the post (TRAFOOF, arc handling, M52,
# R1/ASCALE, motion output). Evaluated at the start of every operation, so
# no operation can inherit the mode from a previous one.
   global mom_ude_interpolation_lock
   if { [PB_CMD__lock_mode] } {
      set mom_ude_interpolation_lock "Yes"
   } else {
      catch {unset mom_ude_interpolation_lock}
   }
}
''') + ANCHOR_LC)

# --- R1 (ASCALE factor) now comes from the UDE PARAM ASCALE_value -----------
rep('LOMO_FG300C.tcl', 'tcl/PB_CMD__rotc_r1 reads ASCALE_value',
    block('''
proc PB_CMD__rotc_r1 { } {
#=============================================================
# Return scale factor R1 (ASCALE) for interpolation-lock (table Y... rotation).
# Value comes from NC UDE parameter if provided, else defaults to 1.0.
   global mom_ude_interpolation_lock mom_ude_r1 mom_ude_rotation_scale_R1 mom_ude_interpolation_lock_R1 mom_ude_lock_axis_R1
   set r1 1.0
   if { [info exists mom_ude_r1] && $mom_ude_r1 != "" } {
      if { [catch {set r1 [expr double($mom_ude_r1)]}] } { set r1 1.0 }
   } elseif { [info exists mom_ude_rotation_scale_R1] && $mom_ude_rotation_scale_R1 != "" } {
      if { [catch {set r1 [expr double($mom_ude_rotation_scale_R1)]}] } { set r1 1.0 }
   }
   return $r1
'''),
    block('''
proc PB_CMD__rotc_r1 { } {
#=============================================================
# Return the scale factor R1 (ASCALE) for the interpolation-lock mode.
# The value comes from the UDE "Interpolation_lock" (PARAM ASCALE_value ->
# mom_ASCALE_value); 1.0 when the event does not provide a value.
   global pb_ascale_req mom_ASCALE_value
   set r1 1.0
   if { [info exists pb_ascale_req] && $pb_ascale_req != "" } {
      set r1 $pb_ascale_req
   } elseif { [info exists mom_ASCALE_value] && $mom_ASCALE_value != "" } {
      set r1 $mom_ASCALE_value
   }
   if { [catch {set r1 [expr double($r1)]}] } { set r1 1.0 }
   return $r1
'''))
# ================================================================ TCL-B2
# --- new UDE handler, right before PB_CMD_MOM_operator_message --------------
ANCHOR_OM = block('#=============================================================\n'
                  'proc PB_CMD_MOM_operator_message { } {')
rep('LOMO_FG300C.tcl', 'tcl/handler PB_CMD_MOM_Interpolation_lock',
    ANCHOR_OM,
    block('''
#=============================================================
proc PB_CMD_MOM_Interpolation_lock { } {
#=============================================================
# UDE "Interpolation lock" - the only trigger of the rotary-table
# interpolation-lock mode (see PB_CMD__lock_mode):
#    command_status  : Active / Inactive
#    lock_axis       : Fourth / Off
#    lock_axis_plane : XYPLAN / NONE
#    ASCALE_value    : scale factor R1 emitted to the NC program
# The inputs are snapshotted here, the verdict is taken in PB_CMD__lock_mode.
   global mom_command_status mom_lock_axis mom_lock_axis_plane mom_ASCALE_value
   global pb_lock_req pb_lock_axis_req pb_lock_plane_req pb_ascale_req

   set pb_lock_req 0
   if { [info exists mom_command_status] && $mom_command_status == "Active" } {
      set pb_lock_req 1
   }

   set pb_lock_axis_req "Off"
   if { [info exists mom_lock_axis] && $mom_lock_axis != "" } {
      set pb_lock_axis_req $mom_lock_axis
   }

   set pb_lock_plane_req "NONE"
   if { [info exists mom_lock_axis_plane] && $mom_lock_axis_plane != "" } {
      set pb_lock_plane_req $mom_lock_axis_plane
   }

   set pb_ascale_req 1.0
   if { [info exists mom_ASCALE_value] && $mom_ASCALE_value != "" } {
      if { [catch {set pb_ascale_req [expr double($mom_ASCALE_value)]}] } {
         set pb_ascale_req 1.0
      }
   }
}
''') + ANCHOR_OM)
# ================================================================ TCL-B3
# --- legacy UDE handlers: deprecated, they must not switch the mode on ------
rep('LOMO_FG300C.tcl', 'tcl/deprecate PB_CMD_MOM_interpolation_lock',
    block('''
# Interpolation lock (Interpolation Lock) - UDE.
# When active (mom_ude_interpolation_lock == "Yes") machining runs
# in 4-axis mode: table rotation C with TRAFOOF (no RTCP).
# Axis A stays locked, axis C is unlocked (M52).
# Applied to planar operations (e.g. circular milling by table rotation).
   global mom_ude_interpolation_lock
'''),
    block('''
# DEPRECATED: legacy UDE "interpolation_lock" (PARAM ude_interpolation_lock).
# It no longer switches the lock mode on - the only trigger is the UDE
# "Interpolation_lock" (see PB_CMD_MOM_Interpolation_lock / PB_CMD__lock_mode).
# The event stays declared in .cdl/.pui so that old parts do not fail.
   global mom_ude_interpolation_lock
'''))

rep('LOMO_FG300C.tcl', 'tcl/deprecate PB_CMD_MOM_lock_axis',
    block('''
# Stock UDE Lock Axis reworked for our needs.
# When active, the "interpolation lock" mode is turned on:
# linear XYZ interpolation is disabled, machining goes
# through rotating table C (4-axis mode).
#   - Axis A stays locked (M50 not output)
#   - Axis C is unlocked (M52), TRAFOOF (no RTCP)
#   - Circular arcs are kept as G2/G3; the working circle is
#     converted by PB_CMD__rotc_arc_handle to a C-axis rotation.
#
   global mom_ude_interpolation_lock

   # Enable the interpolation-lock mode.
   # PB_CMD_detect_operation_type (TRAFOOF, arc handling) and
   # PB_CMD_m50_m52_unlock (M52 + lock comment) already react
   # to this variable. No need to duplicate the logic.
   set mom_ude_interpolation_lock "Yes"
'''),
    block('''
# DEPRECATED: the stock UDE "Lock Axis" no longer switches the post into the
# rotary-table interpolation-lock mode. The only trigger is the UDE
# "Interpolation_lock" (see PB_CMD_MOM_Interpolation_lock / PB_CMD__lock_mode).
# The event stays declared in .cdl/.pui so that old parts do not fail.
   global mom_lock_axis
'''))

# --- clear the mode and all of its inputs at the end of every operation -----
rep('LOMO_FG300C.tcl', 'tcl/MOM_end_of_path cleanup',
    block('''
   # Reset the interpolation-lock mode so it does not affect
   # subsequent operations without an explicit UDE Lock Axis.
   catch {unset mom_ude_interpolation_lock}
'''),
    block('''
   # Reset the interpolation-lock mode and its UDE inputs so neither the mode
   # nor the stock Lock Axis variables leak into the following operations.
   catch {unset mom_ude_interpolation_lock}
   catch {unset pb_lock_mode}
   catch {unset pb_lock_req}
   catch {unset pb_lock_axis_req}
   catch {unset pb_lock_plane_req}
   catch {unset pb_ascale_req}
   catch {unset mom_lock_axis}
   catch {unset mom_lock_axis_plane}
'''))
# ================================================================ TCL-B4
# --- evaluate / publish the mode at the start of every operation ------------
rep('LOMO_FG300C.tcl', 'tcl/detect_operation_type apply',
    block('''
  # Interpolation-lock (UDE interpolation_lock): 4-axis machining by rotating
  # table C with TRAFOOF (no RTCP). Axis A stays locked, axis C is unlocked
  # (see PB_CMD_m50_m52_unlock).
  global mom_ude_interpolation_lock mom_siemens_ori_def pb_lock_arc_active
'''),
    block('''
  # Interpolation-lock (UDE "Interpolation_lock"): 4-axis machining by rotating
  # table C with TRAFOOF (no RTCP). Axis A stays locked, axis C is unlocked
  # (see PB_CMD_m50_m52_unlock). The mode is decided once per operation, here.
  PB_CMD__lock_mode_apply
  global mom_ude_interpolation_lock mom_siemens_ori_def pb_lock_arc_active
'''))

# --- initial move: drop the loose conversion, gate R1 on the UDE ------------
rep('LOMO_FG300C.tcl', 'tcl/initial_move R1',
    block('''
   # If the Lock-Axis UDE selected rotary FOURTH (table C), treat this whole path
   # as the rotary-table interpolation-lock mode. Ensure the downstream flags stay on.
   global mom_lock_axis mom_lock_axis_plane mom_ude_interpolation_lock
   if { [info exists mom_lock_axis] && $mom_lock_axis == "FOURTH" } {
      set mom_ude_interpolation_lock "Yes"
   }

   # Rotating-table (interpolation-lock): assign scale factor R1 (ASCALE).
   if { [info exists mom_ude_interpolation_lock] && $mom_ude_interpolation_lock == "Yes" } {
      set r1val [PB_CMD__rotc_r1]
      set r1str [format "%.3f" $r1val]
      MOM_output_literal "R1=$r1str"
   }
'''),
    block('''
   # The lock mode is driven by the UDE "Interpolation_lock" only (see
   # PB_CMD__lock_mode). Re-evaluate it here as well: the UDE event may be
   # posted after the operation was first examined, and the verdict must be in
   # force before R1/ASCALE are emitted.
   PB_CMD__lock_mode_apply

   # Rotating-table (interpolation-lock): R1/ASCALE are emitted in this mode only.
   if { [PB_CMD__lock_mode] } {
      set r1val [PB_CMD__rotc_r1]
      set r1str [format "%.3f" $r1val]
      MOM_output_literal "R1=$r1str"
   }
'''))

# --- ASCALE: same single condition -----------------------------------------
rep('LOMO_FG300C.tcl', 'tcl/initial_move ASCALE',
    block('''
   # Rotating-table (interpolation-lock): activate scaling before first XY approach.
   if { [info exists mom_ude_interpolation_lock] && $mom_ude_interpolation_lock == "Yes" } {
      MOM_output_literal "ASCALE X=R1 Y=R1"
   }
'''),
    block('''
   # Rotating-table (interpolation-lock): activate scaling before first XY approach.
   if { [PB_CMD__lock_mode] } {
      MOM_output_literal "ASCALE X=R1 Y=R1"
   }
'''))

# everything passed - now write the three files
for name in ('LOMO_FG300C.cdl', 'LOMO_FG300C.pui', 'LOMO_FG300C.tcl'):
    save(name)

# ------------------------------------------------------------- verification
t = data['LOMO_FG300C.tcl']
d_open = t.count(b'{') - BRACE_OPEN
d_close = t.count(b'}') - BRACE_CLOSE
print()
print('   brace delta: { %+d  } %+d' % (d_open, d_close))
assert d_open == d_close, 'unbalanced braces introduced'
for k in ('proc PB_CMD__lock_mode { } {', 'proc PB_CMD__lock_mode_apply { } {',
          'proc PB_CMD_MOM_Interpolation_lock { } {', 'mom_ASCALE_value',
          'if { [PB_CMD__lock_mode] } {'):
    print('   count %-42s %d' % (k, t.count(k.encode('ascii'))))
print()
for name in ('LOMO_FG300C.tcl', 'LOMO_FG300C.pui', 'LOMO_FG300C.cdl'):
    raw = open(os.path.join(BASE, name), 'rb').read()
    print('   %-20s size %-8d nonascii %d  CRLF %d  lone-LF %d' %
          (name, len(raw), sum(1 for b in raw if b > 127), raw.count(CR), raw.count(LF) - raw.count(CR)))
print('ALL DONE')
