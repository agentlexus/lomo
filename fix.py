import io
path='LOMO_FG300C.tcl'
raw=open(path,'rb').read()
lines=raw.split(b'\n')
# Fix lines 4359-4360 (0-based 4358,4359) -> prefix with '# '
for idx in (4358,4359):
    l=lines[idx]
    l2=b'# '+l
    lines[idx]=l2
    print('fixed',idx+1, ascii(l2.decode('cp1251')))
out=b'\n'.join(lines)
open(path,'wb').write(out)
print('DONE')
