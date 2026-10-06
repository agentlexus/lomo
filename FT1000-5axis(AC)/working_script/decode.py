# -*- coding: utf-8 -*-
"""Decode the obfuscated FT1000-5axis(AC) post (Seq_num_Tool) and place the
readable post (all 4 files) into the target 'decoded' folder.

Obfuscation (see _yfacabd in the .tcl):
    decoded = rotr2(byte) XOR 0xFF,  keys 0x5A / 0xA5  ->  k2 ^ k1 == 0xFF
so the reverse used here is:
    v = ((b >> 2) | ((b & 3) << 6)) & 0xFF ; v ^= 0xFF

This only READS the source and WRITES the decoded copies - it never touches
the original encrypted file.
"""
import os
import re
import shutil

SRC = r"C:\Users\BalagurovAI\Documents\GitHub\lomo\FT1000-5axis(AC)\Original\original_encripted"
DST = r"C:\Users\BalagurovAI\Documents\GitHub\lomo\FT1000-5axis(AC)\Decoded"
BASE = "FT1000-5axis(AC)"


def decode(data):
    m1 = b"binary format c* {"
    i = data.index(m1) + len(m1)
    j = data.index(b"}]", i)
    nums = [int(x) for x in re.findall(rb"-?\d+", data[i:j])]
    out = bytearray()
    for b in nums:
        b &= 0xFF
        v = (((b // 4) | ((b % 4) * 64)) & 0xFF) ^ 0xFF
        out.append(v)
    return bytes(out)


def main():
    os.makedirs(DST, exist_ok=True)

    tcl_path = os.path.join(SRC, BASE + ".tcl")
    raw = open(tcl_path, "rb").read()
    assert b"eval [_yfacabd $xdabbee 0x5A 0xA5]" in raw, "wrapper not found"
    dec = decode(raw)
    assert dec.startswith(b"########################## TCL Event Handlers"), \
        "unexpected decoded header: %r" % dec[:60]

    out_tcl = os.path.join(DST, BASE + ".tcl")
    with open(out_tcl, "wb") as f:
        f.write(dec)
    print("decoded .tcl -> %s (%d bytes, %d lines)" %
          (out_tcl, len(dec), dec.count(b"\n")))

    for name in (b"proc MOM_tool_change", b"proc PB_CMD_output_op_marker",
                 b"proc PB_start_of_program"):
        print("  contains %s: %s" % (name.decode(), name in dec))

    for ext in ("def", "pui", "cdl"):
        src = os.path.join(SRC, BASE + "." + ext)
        dst = os.path.join(DST, BASE + "." + ext)
        shutil.copyfile(src, dst)
        print("copied .%s -> %s" % (ext, dst))

    print("DONE")


if __name__ == "__main__":
    main()
