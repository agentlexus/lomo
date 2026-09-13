# -*- coding: utf-8 -*-
# 3+2 machining mode gets its own comment instead of ";AXES LOCKED. 3-AXIS MILLING".
#   1) new helper PB_CMD__mode_comment - single place that prints the mode comment
#      (lock / continuous 5-axis / 3+2 / plain 3-axis);
#      the 3+2 condition is mom_siemens_coord_rotation != 0, i.e. the operation is
#      positioned (CYCLE800 or the A/C rotation frame) - exactly the same test the
#      post uses to decide whether to output CYCLE800.
#   2) PB_CMD_m50_m52_unlock: the mode comments go through the helper (M-codes stay).
#   3) MOM_first_move: the helper is called as well, so the First-Move chain labels
#      every operation too.
#   4) README: modes list + history.
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'
data = {}


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        data[name] = f.read()
    return data[name]


def block(text):
    return CR.join(l.encode('ascii') for l in text.strip('\n').split('\n')) + CR


def rep(name, tag, old, new):
    raw = data[name]
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d' % (tag, n)
    data[name] = raw.replace(old, new)
    print('   ok  %s' % tag)


def save(name):
    raw = data[name]
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    assert max(raw) < 128, '%s: non-ASCII byte written' % name
    with open(os.path.join(BASE, name), 'wb') as f:
        f.write(raw)


# ------------------------------------------------------------------ .tcl
tcl = load('LOMO_FG300C.tcl')
BR_OPEN = tcl.count(b'{')
BR_CLOSE = tcl.count(b'}')

# 1) helper proc, inserted right before PB_CMD_m50_m52_unlock
ANCHOR = block('#=============================================================\n'
               'proc PB_CMD_m50_m52_unlock { } {')
rep('LOMO_FG300C.tcl', 'tcl/new proc PB_CMD__mode_comment',
    ANCHOR,
    block('''
#=============================================================
proc PB_CMD__mode_comment { } {
#=============================================================
# Output the machining-mode comment of the current operation. Called from the
# Initial-Move chain (via PB_CMD_m50_m52_unlock) and from the First-Move chain,
# so every operation is labelled:
#   interpolation lock -> ;INTERPOLATION LOCK. 4-AXIS MACHINING (TABLE C ROTATION).
#   continuous 5-axis  -> ;AXES UNLOCKED. CONTINUOUS 5-AXIS MACHINING ON.
#   3+2 (positioned)   -> ;3+2 MILLING MODE
#   plain 3-axis       -> ;AXES LOCKED. 3-AXIS MILLING
   global mom_siemens_coord_rotation
   if { [PB_CMD__lock_mode] } {
      MOM_output_literal ";INTERPOLATION LOCK. 4-AXIS MACHINING (TABLE C ROTATION)."
   } elseif { [PB_CMD_detect_5axis_tool_path] } {
      MOM_output_literal ";AXES UNLOCKED. CONTINUOUS 5-AXIS MACHINING ON."
   } elseif { [info exists mom_siemens_coord_rotation] && $mom_siemens_coord_rotation != 0 } {
      # 3+2: the table/detail is positioned by CYCLE800 (or by the A/C rotation
      # frame) and machining itself runs in 3 axes - the axes stay locked.
      MOM_output_literal ";3+2 MILLING MODE"
   } else {
      MOM_output_literal ";AXES LOCKED. 3-AXIS MILLING"
   }
}

''') + ANCHOR)

# 2) the four mode comments now come from the helper (M-codes stay where they are)
rep('LOMO_FG300C.tcl', 'tcl/m50_m52_unlock uses PB_CMD__mode_comment',
    block('''
    # 4-axis machining: table rotation C, axis A locked
    MOM_output_literal "M52 ;(C-axis loose)"
    MOM_output_literal ";INTERPOLATION LOCK. 4-AXIS MACHINING (TABLE C ROTATION)."
} elseif { [PB_CMD_detect_5axis_tool_path] } {
    # Continuous 5-axis machining
    MOM_output_literal "M50 ;(A-axis loose)"
    MOM_output_literal "M52 ;(C-axis loose)"
    MOM_output_literal ";AXES UNLOCKED. CONTINUOUS 5-AXIS MACHINING ON."
} else {
    # 3-axis or 3+2 machining
    MOM_output_literal ";AXES LOCKED. 3-AXIS MILLING"
}
'''),
    block('''
    # 4-axis machining: table rotation C, axis A locked
    MOM_output_literal "M52 ;(C-axis loose)"
    PB_CMD__mode_comment
} elseif { [PB_CMD_detect_5axis_tool_path] } {
    # Continuous 5-axis machining
    MOM_output_literal "M50 ;(A-axis loose)"
    MOM_output_literal "M52 ;(C-axis loose)"
    PB_CMD__mode_comment
} else {
    # 3-axis or 3+2 machining - the comment tells which one
    PB_CMD__mode_comment
}
'''))
# ================================================================ PART2
# 3) First-Move chain labels the operation as well
rep('LOMO_FG300C.tcl', 'tcl/MOM_first_move mode comment',
    block('''
   if { [PB_CMD__check_block_CYCLE832] } {
      PB_call_macro CYCLE832_v7
   }

   MOM_force Once transf
   MOM_do_template traori_trafoof
'''),
    block('''
   if { [PB_CMD__check_block_CYCLE832] } {
      PB_call_macro CYCLE832_v7
   }

   # Machining-mode comment (lock / 5-axis / 3+2 / 3-axis), same as in the
   # Initial-Move chain, so every operation is labelled.
   PB_CMD__mode_comment

   MOM_force Once transf
   MOM_do_template traori_trafoof
'''))

# ------------------------------------------------------------------ README
def blocku(text):
    return CR.join(l.encode('utf-8') for l in text.strip('\n').split('\n')) + CR


load('README.md')
rep('README.md', 'readme/режимы обработки',
    blocku('''
1. Лок-режим (событие `Interpolation_lock`) — `M52` + lock-комментарий, `TRAFOOF`.
2. Непрерывная 5-осевая — `M50` + `M52`, `TRAORI`.
3. 3-осевая / 3+2 — `;AXES LOCKED. 3-AXIS MILLING`, `TRAFOOF`.
'''),
    blocku('''
1. Лок-режим (событие `Interpolation_lock`) — `M52` + `;INTERPOLATION LOCK. 4-AXIS
   MACHINING (TABLE C ROTATION).`, `TRAFOOF`.
2. Непрерывная 5-осевая — `M50` + `M52`, `;AXES UNLOCKED. CONTINUOUS 5-AXIS
   MACHINING ON.`, `TRAORI`.
3. 3+2 (позиционирование через `CYCLE800` / кадр A-C, `mom_siemens_coord_rotation != 0`)
   — `;3+2 MILLING MODE`, `TRAFOOF`.
4. Чистая 3-осевая — `;AXES LOCKED. 3-AXIS MILLING`, `TRAFOOF`.

Комментарий режима печатает `PB_CMD__mode_comment` (единое место): он вызывается и
в Initial-Move-цепочке (через `PB_CMD_m50_m52_unlock`), и в First-Move-цепочке
(`MOM_first_move`), поэтому режим помечается в каждой операции.
'''))

rep('README.md', 'readme/история (3+2 MILLING MODE)',
    blocku('''
  `ude.cdl` скриптом `working_script/deploy_ude.py`; документация обновлена.
'''),
    blocku('''
  `ude.cdl` скриптом `working_script/deploy_ude.py`; документация обновлена.
- 2026-09-13: 3+2 получил собственный комментарий режима — было общее
  `;AXES LOCKED. 3-AXIS MILLING`, стало `;3+2 MILLING MODE` (условие:
  `mom_siemens_coord_rotation != 0`, т.е. операция позиционируется CYCLE800 или
  кадром A-C). Комментарий выводит `PB_CMD__mode_comment`, он же вызывается в
  First-Move-цепочке, поэтому режим помечается в каждой операции.
'''))

# ---------------------------------------------------------------- write + check
for name in ('LOMO_FG300C.tcl', 'README.md'):
    raw = data[name]
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    with open(os.path.join(BASE, name), 'wb') as f:
        f.write(raw)
    print('   written %-18s %d bytes' % (name, len(raw)))

t = data['LOMO_FG300C.tcl']
assert max(t) < 128, 'tcl: non-ASCII byte written'
print('   tcl brace delta { %+d  } %+d' % (t.count(b'{') - BR_OPEN, t.count(b'}') - BR_CLOSE))
assert (t.count(b'{') - BR_OPEN) == (t.count(b'}') - BR_CLOSE), 'unbalanced braces'
for pat in (b'proc PB_CMD__mode_comment { } {', b'PB_CMD__mode_comment', b';3+2 MILLING MODE',
            b';AXES LOCKED. 3-AXIS MILLING', b'MOM_output_literal "M52 ;(C-axis loose)"'):
    print('   count %-42s %d' % (pat.decode(), t.count(pat)))
r = data['README.md'].decode('utf-8')
for m in (';3+2 MILLING MODE', 'PB_CMD__mode_comment'):
    assert m in r, m
    print('   README has %r' % m)
print('ALL DONE')
