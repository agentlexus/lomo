import io
path='LOMO_FG300C.tcl'
raw=open(path,'rb').read()
lines=raw.split(b'\n')
# sanity check on target lines (0-based index for display line 4357)
assert b'MOM_suppress Once fourth_axis fifth_axis' in lines[4356], lines[4356]
assert b'VEC3_is_equal mom_tool_axis mom_prev_tool_axis' in lines[4355], lines[4355]
new_lines=[
 b'        if { [info exists mom_tool_axis] && [info exists mom_prev_tool_axis] } {',
 b'           if { [VEC3_is_equal mom_tool_axis mom_prev_tool_axis] } {',
 b'              global mom_ude_interpolation_lock',
 b'              if { [info exists mom_ude_interpolation_lock] &&  == "Yes" } {',
 ('\u0420\u0435\u0436\u0438\u043c \u0432\u0440\u0430\u0449\u0435\u043d\u0438\u044f \u0441\u0442\u043e\u043b\u0430: \u043e\u0441\u044c A \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u0430 (\u043f\u043e\u0434\u0430\u0432\u043b\u044f\u0435\u043c),').encode('cp1251'),
 ('\u043e\u0441\u044c C (\u043f\u043e\u0432\u043e\u0440\u043e\u0442 \u0441\u0442\u043e\u043b\u0430) \u0432\u044b\u0432\u043e\u0434\u0438\u043c \u0434\u0430\u0436\u0435 \u043f\u0440\u0438 \u043f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u043e\u043c \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0438 \u0438\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u0430.').encode('cp1251'),
 b'                 MOM_suppress Once fourth_axis',
 b'              } else {',
 b'                 MOM_suppress Once fourth_axis fifth_axis',
 b'              }',
 b'           }',
 b'        }',
]
lines[4354:4359]=new_lines
out=b'\n'.join(lines)
open(path,'wb').write(out)
print('DONE. new line count around replaced block:')
for i in range(4353,4371):
    print(i+1, ascii(out.split(b'\n')[i]))
