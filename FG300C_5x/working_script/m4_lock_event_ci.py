# -*- coding: ascii -*-
# Follow-up to m4_lock_event.py:
#  1) compare the UDE values case-insensitively - the stock post compares
#     "FOURTH" (upper case) while the .cdl OPTIONS are "Fourth"; the plane is
#     accepted as XYPLAN / XYPLANE (the stock docs use both spellings);
#  2) cosmetic: one blank line between the inserted procedures.
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
TCL = os.path.join(BASE, 'LOMO_FG300C.tcl')
CR = b'\r\n'
LF = b'\n'
raw = open(TCL, 'rb').read()


def blk(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def rep(tag, old, new):
    global raw
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d occurrence(s)' % (tag, n)
    raw = raw.replace(old, new)
    print('   ok  %s' % tag)


# 1a) verdict: axis / plane comparisons
rep('tcl/lock_mode ci compare',
    blk('''
      if { [info exists pb_lock_axis_req] && $pb_lock_axis_req == "Fourth" } {
         if { [info exists pb_lock_plane_req] && $pb_lock_plane_req == "XYPLAN" } {
'''),
    blk('''
      if { [info exists pb_lock_axis_req] && $pb_lock_axis_req == "fourth" } {
         if { [info exists pb_lock_plane_req] && [string match "xyplan*" $pb_lock_plane_req] } {
'''))

# 1b) verdict: comment
rep('tcl/lock_mode comment',
    blk('''
#    lock_axis       = Fourth   (rotary table C)
#    lock_axis_plane = XYPLAN   (planar XY pass)
'''),
    blk('''
#    lock_axis       = Fourth   (rotary table C, any case)
#    lock_axis_plane = XYPLAN   (planar XY pass, XYPLANE also accepted)
'''))

# 1c) handler: normalise the snapshot to lower case
rep('tcl/handler ci snapshot',
    blk('''
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
'''),
    blk('''
   # Values are compared case-insensitively (see PB_CMD__lock_mode).
   set pb_lock_req 0
   if { [info exists mom_command_status] } {
      if { [string tolower $mom_command_status] == "active" } { set pb_lock_req 1 }
   }

   set pb_lock_axis_req "off"
   if { [info exists mom_lock_axis] && $mom_lock_axis != "" } {
      set pb_lock_axis_req [string tolower $mom_lock_axis]
   }

   set pb_lock_plane_req "none"
   if { [info exists mom_lock_axis_plane] && $mom_lock_axis_plane != "" } {
      set pb_lock_plane_req [string tolower $mom_lock_axis_plane]
   }
'''))

# 2a) blank line before PB_CMD__rotc_linear_cut
rep('tcl/blank line rotc_linear_cut',
    blk('''
   }
}
#=============================================================
proc PB_CMD__rotc_linear_cut { } {
'''),
    blk('''
   }
}

#=============================================================
proc PB_CMD__rotc_linear_cut { } {
'''))

# 2b) blank line before PB_CMD_MOM_operator_message
rep('tcl/blank line MOM_operator_message',
    blk('''
}
#=============================================================
proc PB_CMD_MOM_operator_message { } {
'''),
    blk('''
}

#=============================================================
proc PB_CMD_MOM_operator_message { } {
'''))

assert raw.count(LF) == raw.count(CR), 'mixed line endings'
assert max(raw) < 128, 'non-ASCII byte written'
open(TCL, 'wb').write(raw)
print()
print('   size %d  nonascii %d  CRLF %d  lone-LF %d' %
      (len(raw), sum(1 for b in raw if b > 127), raw.count(CR), raw.count(LF) - raw.count(CR)))
print('ALL DONE')
