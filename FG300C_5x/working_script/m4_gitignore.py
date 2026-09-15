# -*- coding: utf-8 -*-
# Append FG300C_5x/nc/ to .gitignore (keep UTF-8 + CRLF).
import os

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo'
p = os.path.join(BASE, '.gitignore')

with open(p, 'rb') as f:
    b = f.read()

entry = 'FG300C_5x/nc/'.encode('utf-8')
if entry not in b:
    if not b.endswith(b'\r\n'):
        b += b'\r\n'
    b += entry + b'\r\n'
    with open(p, 'wb') as f:
        f.write(b)
    print('   appended FG300C_5x/nc/')
else:
    print('   already present, no change')

print('ALL DONE')
