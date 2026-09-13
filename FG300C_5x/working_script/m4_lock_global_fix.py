# -*- coding: ascii -*-
# Two missing "global" declarations in LOMO_FG300C.tcl (same bug class):
#   1) PB_CMD_m50_m52_unlock read mom_ude_interpolation_lock as a LOCAL
#      variable, so the lock branch never fired: no "M52 ;(C-axis loose)",
#      no lock comment, and ";AXES LOCKED. 3-AXIS MILLING" was printed even
#      in interpolation-lock mode.
#   2) MOM_end_of_path cleared the lock state with "catch {unset ...}" but
#      without "global", so the cleanup silently did nothing and the UDE
#      snapshot leaked into the next operation.
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
TCL = os.path.join(BASE, 'LOMO_FG300C.tcl')
CR = b'\r\n'
LF = b'\n'
raw = open(TCL, 'rb').read()
BR_OPEN = raw.count(b'{')
BR_CLOSE = raw.count(b'}')


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def rep(tag, old, new):
    global raw
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d occurrence(s)' % (tag, n)
    raw = raw.replace(old, new)
    print('   ok  %s' % tag)


# 1) the lock branch of PB_CMD_m50_m52_unlock
rep('tcl/m50_m52_unlock global',
    block('''
# Separate mode: "Interpolation lock" (UDE interpolation_lock).
# When active, machining runs in 4-axis mode (table rotation C
# with TRAFOOF, no RTCP): axis A stays locked, axis C unlocked (M52).
if { [info exists mom_ude_interpolation_lock] && $mom_ude_interpolation_lock == "Yes" } {
'''),
    block('''
# Separate mode: "Interpolation lock" (UDE "Interpolation_lock").
# When active, machining runs in 4-axis mode (table rotation C
# with TRAFOOF, no RTCP): axis A stays locked, axis C unlocked (M52).
   global mom_ude_interpolation_lock
if { [info exists mom_ude_interpolation_lock] && $mom_ude_interpolation_lock == "Yes" } {
'''))

# 2) make the end-of-path cleanup actually reach the global variables
rep('tcl/MOM_end_of_path global',
    block('''
   # Reset the interpolation-lock mode and its UDE inputs so neither the mode
   # nor the stock Lock Axis variables leak into the following operations.
   catch {unset mom_ude_interpolation_lock}
'''),
    block('''
   # Reset the interpolation-lock mode and its UDE inputs so neither the mode
   # nor the stock Lock Axis variables leak into the following operations.
   # The "global" line is required - without it "unset" would address
   # non-existent local variables and the whole cleanup would be a no-op.
   global mom_ude_interpolation_lock pb_lock_mode pb_lock_req
   global pb_lock_axis_req pb_lock_plane_req pb_ascale_req
   global mom_lock_axis mom_lock_axis_plane
   catch {unset mom_ude_interpolation_lock}
'''))

d_open = raw.count(b'{') - BR_OPEN
d_close = raw.count(b'}') - BR_CLOSE
print('   brace delta: { %+d  } %+d' % (d_open, d_close))
assert d_open == d_close, 'unbalanced braces introduced'
assert raw.count(LF) == raw.count(CR), 'mixed line endings'
assert max(raw) < 128, 'non-ASCII byte written'
open(TCL, 'wb').write(raw)

print()
for pat, want in ((b'   global mom_ude_interpolation_lock\r\nif { [info exists mom_ude_interpolation_lock]', 1),
                  (b'   global mom_ude_interpolation_lock pb_lock_mode pb_lock_req', 1),
                  # 5 = the new comment in m50_m52_unlock + 4 earlier ones
                  (b'UDE "Interpolation_lock"', 5)):
    got = raw.count(pat)
    print('   %-70s %d (want %d)' % (pat.decode('ascii').replace('\r', ''), got, want))
    assert got == want, 'check failed: %s' % pat
print('   size %d  nonascii %d  CRLF %d  lone-LF %d' %
      (len(raw), sum(1 for b in raw if b > 127), raw.count(CR), raw.count(LF) - raw.count(CR)))
print('ALL DONE')
