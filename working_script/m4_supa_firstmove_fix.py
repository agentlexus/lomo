# -*- coding: ascii -*-
# Byte-level patch for LOMO_FG300C.tcl / .def  (files are cp1251 + CRLF).
# Edits:
#  1) MOM_first_move  - align First-Move chain to Initial-Move reference logic
#     (no bogus ORIRESET / CYCLE800(...) for planar 3-axis first moves).
#  2) Force "G0" on every SUPA home/return block (per-block MOM_force).
#  3) .def tool_change_return_home_AC - drop fifth_axis (C0.0).

TCL = r'd:\Programs\repository\lomo-1\LOMO_FG300C.tcl'
DEF = r'd:\Programs\repository\lomo-1\LOMO_FG300C.def'

def load(path):
    raw = open(path, 'rb').read()
    return raw, raw.split(b'\n')

def check(cond, msg):
    if not cond:
        raise SystemExit('ASSERT FAILED: ' + msg)

def apply_edits(path, edits):
    """edits: list of (start_line, end_line_incl, old_lines, new_lines), 1-based.
    Must be sorted by start_line descending (bottom-up)."""
    raw, lines = load(path)
    cur = list(lines)
    prev_start = 10 ** 9
    for (s, e, old, new) in edits:
        check(s < prev_start, 'edits not in descending order at line %d' % s)
        prev_start = s
        check(e >= s, 'bad range %d..%d' % (s, e))
        got = cur[s - 1:e]
        check(got == old,
              'old content mismatch at lines %d..%d\nGOT : %r\nWANT: %r'
              % (s, e, got[:3], old[:3]))
        cur[s - 1:e] = new
    out = b'\n'.join(cur)
    open(path, 'wb').write(out)
    print('PATCHED %s (%d edits)' % (path, len(edits)))

# ============================================================ TCL
# ---------- 1) MOM_first_move body 1652..1673 ----------
old_first = [
 b'   MOM_output_literal ";First Move"\r',
 b'   PB_call_macro CYCLE832_v7\r',
 b'\r',
 b'   if { [PB_CMD__check_block_CYCLE832] } {\r',
 b'      MOM_do_template rotation_axes\r',
 b'   }\r',
 b'\r',
 b'   if { [PB_CMD__check_block_rotation_axes] } {\r',
 b'      PB_call_macro ORIRESET\r',
 b'   }\r',
 b'\r',
 b'   if { [PB_CMD__check_block_ORIRESET] } {\r',
 b'      MOM_do_template traori_trafoof\r',
 b'   }\r',
 b'\r',
 b'   MOM_do_template fixture_offset\r',
 b'   PB_CMD_output_trans_arot\r',
 b'   PB_call_macro CYCLE800_sl\r',
 b'\r',
 b'   if { [PB_CMD__check_block_CYCLE800] } {\r',
 b'      PB_CMD_move_force_addresses\r',
 b'   }\r',
]
new_first = [
 b'   MOM_output_literal ";First Move"\r',
 b'\r',
 b'   # First-Move chain mirrors the reference Initial-Move chain\r',
 b'   # (PB_CMD_output_initial_move): G54 -> G0 A0.0 C=DC(0.0) ->\r',
 b'   # COMPOF/CYCLE832 -> TRAFOOF.  ORIRESET and CYCLE800(...) are\r',
 b'   # output only when the operation really needs them (3+2 swivel),\r',
 b'   # never for a plain planar / 3-axis first move.\r',
 b'\r',
 b'   MOM_force Once G_offset\r',
 b'   MOM_do_template fixture_offset_1\r',
 b'\r',
 b'   if { [PB_CMD__check_block_rotation_axes] } {\r',
 b'      MOM_force Once G_motion fourth_axis fifth_axis_DC\r',
 b'      MOM_do_template rotation_axes\r',
 b'   }\r',
 b'\r',
 b'   if { [PB_CMD__check_block_ORIRESET] } {\r',
 b'      PB_call_macro ORIRESET\r',
 b'   }\r',
 b'\r',
 b'   if { [PB_CMD__check_block_CYCLE832] } {\r',
 b'      PB_call_macro CYCLE832_v7\r',
 b'   }\r',
 b'\r',
 b'   MOM_force Once transf\r',
 b'   MOM_do_template traori_trafoof\r',
 b'\r',
 b'   PB_CMD_output_trans_arot\r',
 b'\r',
 b'   if { [PB_CMD__check_block_CYCLE800] } {\r',
 b'      PB_call_macro CYCLE800_sl\r',
 b'   }\r',
 b'\r',
 b'   PB_CMD_move_force_addresses\r',
]
# ---------- 2a) PB_auto_tool_change SUPA home 2443..2446 ----------
old_atc_home = [
 b'   MOM_force Once Text G_motion D\r',
 b'   MOM_do_template tool_change_return_home_Z\r',
 b'   MOM_do_template tool_change_return_home_X\r',
 b'   MOM_do_template tool_change_return_home_Y\r',
]
new_atc_home = [
 b'   MOM_force Once Text G_motion D\r',
 b'   MOM_do_template tool_change_return_home_Z\r',
 b'\r',
 b'   MOM_force Once Text G_motion X\r',
 b'   MOM_do_template tool_change_return_home_X\r',
 b'\r',
 b'   MOM_force Once Text G_motion Y\r',
 b'   MOM_do_template tool_change_return_home_Y\r',
]
# ---------- 2b) PB_auto_tool_change return-first-refs 2461..2464 ----------
old_atc_ref = [
 b'   MOM_force Once X\r',
 b'   MOM_do_template return_first_ref_X\r',
 b'\r',
 b'   MOM_do_template return_first_ref_Y\r',
]
new_atc_ref = [
 b'   MOM_force Once Text G_motion X\r',
 b'   MOM_do_template return_first_ref_X\r',
 b'\r',
 b'   MOM_force Once Text G_motion Y\r',
 b'   MOM_do_template return_first_ref_Y\r',
]
# ---------- 3a) end_of_program comment 8964 ----------
old_eop_comment = [b'#     SUPA G00 A0.0 C0.0\r']
new_eop_comment = [b'#     SUPA G00 A0.0\r']
# ---------- 3b) end_of_program SUPA block 8976..8982 ----------
old_eop = [
 b'   # Return home with numeric coordinates, as in reference NC 2.mpf.\r',
 b'   # Force addresses so each SUPA block always outputs its coordinate.\r',
 b'   MOM_force Once Text G_motion Z X Y fourth_axis fifth_axis D\r',
 b'   MOM_do_template tool_change_return_home_Z\r',
 b'   MOM_do_template tool_change_return_home_X\r',
 b'   MOM_do_template tool_change_return_home_Y\r',
 b'   MOM_do_template tool_change_return_home_AC\r',
]
new_eop = [
 b'   # Return home with numeric coordinates, as in reference NC 2.mpf.\r',
 b'   # Force G0 and every coordinate on each SUPA block so no SUPA\r',
 b'   # line comes out empty or without the rapid word.\r',
 b'   MOM_force Once Text G_motion D Z\r',
 b'   MOM_do_template tool_change_return_home_Z\r',
 b'\r',
 b'   MOM_force Once Text G_motion X\r',
 b'   MOM_do_template tool_change_return_home_X\r',
 b'\r',
 b'   MOM_force Once Text G_motion Y\r',
 b'   MOM_do_template tool_change_return_home_Y\r',
 b'\r',
 b'   MOM_force Once Text G_motion fourth_axis\r',
 b'   MOM_do_template tool_change_return_home_AC\r',
]
# ---------- 4) output_first_tool 9133..9135 ----------
old_oft = [
 b'   MOM_force Once X\r',
 b'   MOM_do_template return_first_ref_X\r',
 b'   MOM_do_template return_first_ref_Y\r',
]
new_oft = [
 b'   MOM_force Once Text G_motion X\r',
 b'   MOM_do_template return_first_ref_X\r',
 b'\r',
 b'   MOM_force Once Text G_motion Y\r',
 b'   MOM_do_template return_first_ref_Y\r',
]
# ---------- 5a) start_of_path comment 9350 ----------
old_sop_comment = [b'#     SUPA G00 Z0.0 D0 / X0.0 / Y0.0 / A0.0 C0.0\r']
new_sop_comment = [b'#     SUPA G00 Z0.0 D0 / X0.0 / Y0.0 / A0.0\r']
# ---------- 5b) start_of_path home block 9363..9368 ----------
old_sop = [
 b'      MOM_do_template trafoof\r',
 b'      MOM_do_template reset_cycle800\r',
 b'      MOM_do_template tool_change_return_home_Z\r',
 b'      MOM_do_template tool_change_return_home_X\r',
 b'      MOM_do_template tool_change_return_home_Y\r',
 b'      MOM_do_template tool_change_return_home_AC\r',
]
new_sop = [
 b'      MOM_do_template trafoof\r',
 b'      MOM_do_template reset_cycle800\r',
 b'\r',
 b'      MOM_force Once Text G_motion D Z\r',
 b'      MOM_do_template tool_change_return_home_Z\r',
 b'\r',
 b'      MOM_force Once Text G_motion X\r',
 b'      MOM_do_template tool_change_return_home_X\r',
 b'\r',
 b'      MOM_force Once Text G_motion Y\r',
 b'      MOM_do_template tool_change_return_home_Y\r',
 b'\r',
 b'      MOM_force Once Text G_motion fourth_axis\r',
 b'      MOM_do_template tool_change_return_home_AC\r',
]

tcl_edits = [
 (9363, 9368, old_sop, new_sop),
 (9350, 9350, old_sop_comment, new_sop_comment),
 (9133, 9135, old_oft, new_oft),
 (8976, 8982, old_eop, new_eop),
 (8964, 8964, old_eop_comment, new_eop_comment),
 (2461, 2464, old_atc_ref, new_atc_ref),
 (2443, 2446, old_atc_home, new_atc_home),
 (1652, 1673, old_first, new_first),
]
apply_edits(TCL, tcl_edits)

# ============================================================ DEF
# tool_change_return_home_AC 1390..1393 - drop fifth_axis (C0.0)
old_ac = [
 b'       Text[SUPA]\r',
 b'       G_motion[$mom_sys_rapid_code]\r',
 b'       fourth_axis[0.0]\r',
 b'       fifth_axis[0.0]\r',
]
new_ac = [
 b'       Text[SUPA]\r',
 b'       G_motion[$mom_sys_rapid_code]\r',
 b'       fourth_axis[0.0]\r',
]
def_edits = [
 (1390, 1393, old_ac, new_ac),
]
apply_edits(DEF, def_edits)

print('ALL DONE')


