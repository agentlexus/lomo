import io
path='LOMO_FG300C.tcl'
raw=open(path,'rb').read()
lines=raw.split(b'\n')
lines[4357]=('              if { [info exists mom_ude_interpolation_lock] && $mom_ude_interpolation_lock == "Yes" } {').encode('ascii')
out=b'\n'.join(lines)
open(path,'wb').write(out)
print('fixed 4358:')
print(ascii(out.split(b'\n')[4357]))
