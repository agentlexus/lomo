# -*- coding: utf-8 -*-
"""Enable general N block numbering in the FT1000-5axis(AC) encrypted post (Original/original_encripted).

Variant B: one single numbering series.
  * turn the built-in sequence numbering ON where it gates program blocks;
  * keep pure comments "(...)" without N (wrapped in MOM_set_seq_off/on);
  * drive the operation marker + the header table from the engine number
    (mom_seqnum) so the header line numbers match the real program lines.

Works on the decoded copy only; the neighbouring FG300C post files are not
touched.  Finally re-encodes the result back into the protected form.
"""
import re
import os
import shutil

DEC     = r"C:\Users\BalagurovAI\Documents\GitHub\lomo\FT1000-5axis(AC)\Decoded\FT1000-5axis(AC).tcl"
ENC_SRC = r"C:\Users\BalagurovAI\Documents\GitHub\lomo\FT1000-5axis(AC)\Original\original_encripted\FT1000-5axis(AC).tcl"
OUT_DEC = r"C:\Users\BalagurovAI\Documents\GitHub\lomo\FT1000-5axis(AC)\Decoded\FT1000-5axis(AC)_seqnum.tcl"
OUT_ENC = r"C:\Users\BalagurovAI\Documents\GitHub\lomo\FT1000-5axis(AC)\Decoded\FT1000-5axis(AC)_seqnum_ENC.tcl"

LOG = []


def sub(d, pattern, repl, n_exp, tag):
    new, n = re.subn(pattern, repl, d)
    assert n == n_exp, "%s: expected %d, got %d" % (tag, n_exp, n)
    LOG.append("%-58s x%d" % (tag, n))
    return new


def off2on(m):
    return m.group(0).replace(b"MOM_set_seq_off", b"MOM_set_seq_on")


def decode(data):
    i = data.index(b"binary format c* {") + len(b"binary format c* {")
    j = data.index(b"}]", i)
    nums = [int(x) for x in re.findall(rb"-?\d+", data[i:j])]
    out = bytearray()
    for b in nums:
        b &= 0xFF
        out.append((((b // 4) | ((b % 4) * 64)) & 0xFF) ^ 0xFF)
    return bytes(out)


def encode_into_shell(shell, decoded):
    i = shell.index(b"binary format c* {") + len(b"binary format c* {")
    j = shell.index(b"}]", i)
    eol = b"\r\n" if b"\r\n" in shell[i:j] else b"\n"
    nums = []
    for b in decoded:
        v = (b ^ 0xFF) & 0xFF
        v = ((v << 2) | (v >> 6)) & 0xFF          # ROL2(x) = inverse of ROR2
        nums.append(v if v < 128 else v - 256)    # signed char (binary format c*)
    lines = [b"    " + b" ".join(str(x).encode() for x in nums[k:k + 20])
             for k in range(0, len(nums), 20)]
    return shell[:i] + eol + eol.join(lines) + eol + shell[j:]


def main():
    d = open(DEC, "rb").read()
    assert b"\r" not in d, "decoded file is expected to be LF-only"

    # ---- 1. enable numbering where it gates program blocks ----------------
    d = sub(d,
            rb"COOLANT_SET ; CUTCOM_SET ; SPINDLE_SET ; RAPID_SET\s+MOM_set_seq_off\s+PB_CMD_custom_command_1",
            off2on, 2, "MOM_first_move / MOM_initial_move: off -> on")
    d = sub(d,
            rb"set mom_sys_first_tool_handled 1\s+MOM_set_seq_off\s+MOM_do_template start_of_program_1",
            off2on, 1, "MOM_first_tool: off -> on")
    d = sub(d,
            rb"PB_CMD_souchaozuokaishi\s+MOM_set_seq_off(\s*)\}",
            lambda m: b"PB_CMD_souchaozuokaishi\n   MOM_set_seq_on" + m.group(1) + b"}",
            1, "MOM_start_of_path: off -> on (body numbered)")
    d = sub(d,
            rb'(MOM_set_seq_off\s+MOM_output_literal "\(Tool Change\)")',
            lambda m: m.group(1) + b"\n\n   MOM_set_seq_on",
            1, "PB_auto_tool_change: comment off, then on")
    d = sub(d, rb"#MOM_set_seq_on", b"MOM_set_seq_on", 1,
            "PB_CMD_path_info: uncomment MOM_set_seq_on")

    # ---- 2. keep pure comments without N ----------------------------------
    for tag in (b"End of Program", b"End of Path", b"Initial tool"):
        d = sub(d,
                rb'MOM_output_literal "\(' + tag + rb'\)"',
                b'MOM_set_seq_off\n   MOM_output_literal "(' + tag + b')"\n   MOM_set_seq_on',
                1, "wrap comment (%s)" % tag.decode())

    # ---- 3. number the operation marker via the engine --------------------
    d = sub(d,
            rb'MOM_output_literal "\(start of Path\)"\s+MOM_do_template opstop',
            b'MOM_set_seq_off\n   MOM_output_literal "(start of Path)"\n   MOM_set_seq_on\n\n   MOM_do_template opstop',
            1, "MOM_start_of_path: comment off, on for opstop+marker")
    d = sub(d,
            rb"global g_op_seq_counter g_last_tool_num g_tool_list g_op_index_list",
            b"global g_op_seq_counter g_last_tool_num g_tool_list g_op_index_list mom_seqnum",
            1, "output_op_marker: add mom_seqnum global")
    d = sub(d,
            rb"incr g_op_seq_counter[^\n]*",
            b"if {[info exists mom_seqnum]} { set g_op_seq_counter [expr {int($mom_seqnum)}] } else { incr g_op_seq_counter }",
            1, "output_op_marker: counter = engine number")
    d = sub(d,
            rb'MOM_output_literal "N\$g_op_seq_counter;\(Operation: \$mom_operation_name\)"',
            b'MOM_output_literal ";(Operation: $mom_operation_name)"',
            1, "output_op_marker: drop manual N (engine adds it)")

    open(OUT_DEC, "wb").write(d)
    print("patched decoded ->", OUT_DEC, "(%d bytes)" % len(d))
    for s in LOG:
        print("   ", s)

    # ---- 4. re-encode into the protected form -----------------------------
    shell = open(ENC_SRC, "rb").read()
    out = encode_into_shell(shell, d)
    open(OUT_ENC, "wb").write(out)
    print("protected ->", OUT_ENC, "(%d bytes)" % len(out))

    # ---- 5. round-trip sanity --------------------------------------------
    assert decode(out) == d, "round-trip mismatch!"
    print("round-trip OK (%d bytes decoded back)" % len(d))
    print("DONE")


if __name__ == "__main__":
    main()
