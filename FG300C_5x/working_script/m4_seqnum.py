# -*- coding: utf-8 -*-
# 1) Empty separator line between operations: MOM_set_seq_off / on around it
#    (no sequence number on the blank line).
# 2) Sequential numbering 1,2,3,4,... for the whole program: seqnum start=1,
#    increment=1 (was 10/10) in .tcl, .pui and .def.
import os
import re

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'


def read(p):
    with open(p, 'rb') as f:
        return f.read()


def write(p, b):
    with open(p, 'wb') as f:
        f.write(b)


# ---------- .tcl ----------
p = os.path.join(BASE, 'LOMO_FG300C.tcl')
b = read(p)

# 1. seqnum start / increment 10 -> 1
b, n1 = re.subn(rb'(set\s+mom_sys_seqnum_start\s+)"10"', rb'\1"1"', b, count=1)
b, n2 = re.subn(rb'(set\s+mom_sys_seqnum_incr\s+)"10"', rb'\1"1"', b, count=1)
assert n1 == 1 and n2 == 1, (n1, n2)

# 2. separator: turn seq off for the blank line
old = CR.join([
    b'   MOM_output_literal ";(End of Path)"',
    b'   MOM_output_literal " "',
])
new = CR.join([
    b'   MOM_output_literal ";(End of Path)"',
    b'   MOM_set_seq_off',
    b'   MOM_output_literal " "',
    b'   MOM_set_seq_on',
])
n = b.count(old)
assert n == 1, 'separator anchor found %d' % n
b = b.replace(old, new)

assert b.count(b'\n') == b.count(b'\r'), 'mixed line endings'
assert max(b) < 128, 'non-ASCII byte'
write(p, b)
print('   .tcl ok (%d bytes)' % len(b))

# ---------- .pui ----------
p = os.path.join(BASE, 'LOMO_FG300C.pui')
b = read(p)
b, n1 = re.subn(rb'(\$mom_sys_seqnum_start"\s+)"10"', rb'\1"1"', b, count=1)
b, n2 = re.subn(rb'(\$mom_sys_seqnum_incr"\s+)"10"', rb'\1"1"', b, count=1)
assert n1 == 1 and n2 == 1, (n1, n2)
write(p, b)
print('   .pui ok (%d bytes)' % len(b))

# ---------- .def ----------
p = os.path.join(BASE, 'LOMO_FG300C.def')
b = read(p)
old = b'SEQUENCE sequence_number 10  10 1 99999999'
new = b'SEQUENCE sequence_number 1  1 1 99999999'
n = b.count(old)
assert n == 1, '.def SEQUENCE anchor found %d' % n
b = b.replace(old, new)
write(p, b)
print('   .def ok (%d bytes)' % len(b))

print('ALL DONE')
