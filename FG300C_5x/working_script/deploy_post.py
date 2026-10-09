# -*- coding: utf-8 -*-
# Deploy the post files into the NX post folder:
#     ${UGII_CAM_POST_DIR}LOMO_FG300C\
# (at runtime only .tcl/.def are used; .pui is for Post Builder, .cdl kept for
#  consistency). Byte copy - encoding and EOL stay untouched.
#
#   python deploy_post.py           sync  : copy every differing file (with backup)
#   python deploy_post.py --check   check : only report what would change
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POST_NAME = 'LOMO_FG300C'
FILES = ('LOMO_FG300C.tcl', 'LOMO_FG300C.def', 'LOMO_FG300C.pui', 'LOMO_FG300C.cdl')
CHECK = '--check' in sys.argv or '-c' in sys.argv


def post_dir():
    env = os.environ.get('UGII_CAM_POST_DIR')
    if env:
        return os.path.join(env.strip('"').rstrip('\\'), POST_NAME)
    root = os.environ.get('UGII_BASE_DIR') or r'D:\Siemens\NX2312'
    return os.path.join(root.strip('"'), 'MACH', 'resource', 'postprocessor', POST_NAME)


def main():
    target = post_dir()
    print('   source : %s' % BASE)
    print('   target : %s' % target)
    assert os.path.isdir(target), 'not found: %s' % target

    todo = []
    for f in FILES:
        src = os.path.join(BASE, f)
        assert os.path.isfile(src), 'missing source: %s' % src
        dst = os.path.join(target, f)
        if not os.path.isfile(dst):
            todo.append((f, 'new'))
        elif open(src, 'rb').read() != open(dst, 'rb').read():
            todo.append((f, 'differs'))
        else:
            print('   up to date : %s' % f)

    if not todo:
        print('   RESULT : up to date (%d files)' % len(FILES))
        return 0

    if CHECK:
        print('   RESULT : need deploy -> %s' % ', '.join('%s (%s)' % x for x in todo))
        print('            run without --check to copy (backup is made)')
        return 1

    bak = os.path.join(target, 'backup_' + time.strftime('%Y%m%d_%H%M%S'))
    os.makedirs(bak)
    for f in FILES:
        dst = os.path.join(target, f)
        if os.path.isfile(dst):
            shutil.copy2(dst, os.path.join(bak, f))
    for f, why in todo:
        shutil.copy2(os.path.join(BASE, f), os.path.join(target, f))
        print('   copied %-18s (%s)' % (f, why))
    print('   RESULT : deployed %d of %d file(s); backup: %s' % (len(todo), len(FILES), bak))
    return 0


print('deploy_post.py  %s' % ('CHECK' if CHECK else 'SYNC'))
sys.exit(main())
