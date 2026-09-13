# -*- coding: utf-8 -*-
# Deploy the custom UDE block(s) into the catalog NX reads for the operation
# dialog and for the post engine:
#     %UGII_CAM_USER_DEF_EVENT_DIR%\ude.cdl
# (see README: the UI list comes from USER_DEFINED_EVENTS in the CAM
#  configuration, which points at this file; changes are picked up without an
#  NX restart.)
#
# Source of the block: FG300C_5x\LOMO_FG300C_ude.cdl (everything from the first
# "EVENT ..." to the end of the file).
#
#   python deploy_ude.py           sync  : insert / update the block (with backup)
#   python deploy_ude.py --check   check : only report whether it is up to date
import os
import shutil
import sys
import time

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
SOURCE = os.path.join(BASE, 'LOMO_FG300C_ude.cdl')
CRLF = b'\r\n'
CHECK = '--check' in sys.argv or '-c' in sys.argv


def catalog_path():
    d = os.environ.get('UGII_CAM_USER_DEF_EVENT_DIR')
    if not d:
        base = os.environ.get('UGII_BASE_DIR') or r'D:\Siemens\NX2312'
        d = os.path.join(base, 'MACH', 'resource', 'user_def_event')
    d = d.strip('"')
    return os.path.join(d, 'ude.cdl')


def source_block():
    raw = open(SOURCE, 'rb').read()
    i = raw.find(b'EVENT ')
    assert i >= 0, 'no EVENT in %s' % SOURCE
    block = raw[i:].rstrip(b'\r\n \t')
    assert block.endswith(b'}'), 'block does not end with a closing brace'
    return block


def find_block(raw):
    """Return (start, end_exclusive) of an EVENT block whose name matches ours."""
    name = open(SOURCE, 'rb').read()
    name = name[name.find(b'EVENT ') + 6:]
    name = name.split(b'\r\n')[0].split(b' ')[0].strip()
    head = b'EVENT ' + name
    i = raw.find(head)
    if i < 0:
        return None
    j = raw.find(b'{', i)
    assert j > 0, 'malformed block'
    depth = 0
    k = j
    while k < len(raw):
        if raw[k:k + 1] == b'{':
            depth += 1
        elif raw[k:k + 1] == b'}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    end = k + 1
    return (i, end)


def main():
    target = catalog_path()
    print('   source : %s' % SOURCE)
    print('   target : %s' % target)
    assert os.path.isfile(target), 'not found: %s' % target
    block = source_block()
    raw = open(target, 'rb').read()
    span = find_block(raw)

    if span is None:
        if CHECK:
            print('   RESULT : BLOCK MISSING - run without --check to deploy')
            return 1
        i = raw.find(b'MACHINE ')
        assert i >= 0, 'no MACHINE line in the catalog'
        eol = raw.find(CRLF, i)
        assert eol > 0
        new = raw[:eol + 2] + CRLF + block + raw[eol + 2:]
        shutil.copy2(target, target + '.bak_' + time.strftime('%Y%m%d_%H%M%S'))
        open(target, 'wb').write(new)
        print('   RESULT : inserted after the MACHINE line (backup kept)')
        return 0

    cur = raw[span[0]:span[1]]
    if cur == block:
        print('   RESULT : up to date (%d bytes, block at offset %d)' % (len(block), span[0]))
        return 0

    if CHECK:
        print('   RESULT : DIFFERS - deployed block is %d bytes, source is %d bytes'
              % (len(cur), len(block)))
        print('            run without --check to update (both are kept: backup is made)')
        return 1

    new = raw[:span[0]] + block + raw[span[1]:]
    shutil.copy2(target, target + '.bak_' + time.strftime('%Y%m%d_%H%M%S'))
    open(target, 'wb').write(new)
    print('   RESULT : updated (%d -> %d bytes, backup kept)' % (len(cur), len(block)))
    return 0


print('deploy_ude.py  %s' % ('CHECK' if CHECK else 'SYNC'))
sys.exit(main())
