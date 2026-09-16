import os
BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
p = os.path.join(BASE, 'LOMO_FG300C.pui')
b = open(p, 'rb').read()
old = b'{"PB_CMD_MOM_Interpolation_lock" "" "Custom Command"} \\' + CR
new = old + b'      {"PB_CMD_MOM_Automatic_doors" "" "Custom Command"} \\' + CR
n = b.count(old)
assert n == 1, 'anchor %d' % n
b = b.replace(old, new)
open(p, 'wb').write(b)
print('pui custom cmd ok', len(b))
