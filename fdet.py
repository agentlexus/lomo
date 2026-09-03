import io
path='LOMO_FG300C.tcl'
raw=open(path,'rb').read()
lines=raw.split(b'\n')
# Find the if-block lines exactly
# lines 0-based: 6104 global, 6105 if, 6106-6107 set, 6108 }
assert b'global mom_ude_interpolation_lock' in lines[6103], lines[6103]
assert b'mom_ude_interpolation_lock == "Yes" } {' in lines[6104], lines[6104]
assert b'set dpp_ge(toolpath_axis_num) 5' in lines[6105], lines[6105]
assert b'set mom_siemens_5axis_mode "TRAORI"' in lines[6106], lines[6106]
# Replace global line to add ori_def global
lines[6103]=b'  global mom_ude_interpolation_lock mom_siemens_ori_def'
# Insert ROTARY set after mom_siemens_5axis_mode line
lines.insert(6107, b'     set mom_siemens_ori_def "ROTARY AXES" ; # \xd0\xb2\xd1\x80\xd0\xb0\xd1\x89\xd0\xb5\xd0\xbd\xd0\xb8\xd0\xb5 \xd1\x81\xd1\x82\xd0\xbe\xd0\xbb\xd0\xb0 -> \xd1\x83\xd0\xb3\xd0\xbb\xd1\x8b \xd0\xbe\xd1\x81\xd0\xb5\xd0\xb9 (C), \xd0\xbd\xd0\xb5 \xd0\xb2\xd0\xb5\xd0\xba\xd1\x82\xd0\xbe\xd1\x80')
out=b'\n'.join(lines)
open(path,'wb').write(out)
print('DONE')
for i in range(6103,6113):
    print(i+1, ascii(out.split(b'\n')[i].decode('cp1251')))
