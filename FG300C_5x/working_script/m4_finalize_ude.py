# -*- coding: utf-8 -*-
# Finalize the UDE registration after the NX experiments:
#   1) .def  - drop the INCLUDE of LOMO_FG300C.cdl: the event is defined in
#              ude.cdl (the file both the UI catalog and the post engine read),
#              so a second definition is redundant.
#   2) README - document the verified mechanism: the operation dialog takes its
#              UDE list from USER_DEFINED_EVENTS in the CAM configuration
#              (cam_general.dat -> ${UGII_CAM_USER_DEF_EVENT_DIR}ude.cdl),
#              while the .def INCLUDE feeds the post engine only.
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'
CR = b'\r\n'
LF = b'\n'


def b_of(text, eol='crlf'):
    lines = text.replace('\r\n', '\n').strip('\n').split('\n')
    sep = CR if eol == 'crlf' else LF
    return sep.join(l.encode('utf-8') for l in lines) + sep


def load(name):
    with open(os.path.join(BASE, name), 'rb') as f:
        return f.read()


def rep(name, tag, old, new):
    raw = load(name)
    n = raw.count(old)
    assert n == 1, 'MISS %s: found %d' % (tag, n)
    raw = raw.replace(old, new)
    assert raw.count(LF) == raw.count(CR), '%s: mixed line endings' % name
    with open(os.path.join(BASE, name), 'wb') as f:
        f.write(raw)
    print('   ok  %s' % tag)


# ------------------------------------------------------------------ .def
rep('LOMO_FG300C.def', 'def/drop INCLUDE of LOMO_FG300C.cdl',
    b'$UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl' + CR +
    b'         $UGII_CAM_USER_DEF_EVENT_DIR/LOMO_FG300C.cdl' + CR,
    b'$UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl' + CR)

# ------------------------------------------------------------------ README
OLD_SECTION = '''
## Как NX находит пост и события (важно)

1. Список постов — `MACH\\resource\\postprocessor\\template_post.dat`:
   `LOMO_FG300C, ${UGII_CAM_POST_DIR}LOMO_FG300C\\LOMO_FG300C.tcl, …\\LOMO_FG300C.def`.
   В рантайме работают **только `.tcl` и `.def`** (+ файлы из `INCLUDE`); `.pui`
   нужен только Post Builder.
2. Каталог UDE подключается в `.def` — это и есть «мост» пост → CAM-UDE:
```
INCLUDE {
         $UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl
         $UGII_CAM_USER_DEF_EVENT_DIR/LOMO_FG300C.cdl
        }
```
   `INCLUDE` — список файлов; путь по умолчанию `$UGII_CAM_USER_DEF_EVENT_DIR`
   (`...\\MACH\\resource\\user_def_event`). Глобальный `ude.cdl` править не нужно:
   кастомные события живут в `LOMO_FG300C.cdl`. Сам постный `.cdl` в рантайме
   не читается (это проект Post Builder).
3. Из этих `.cdl` событие попадает в UI операции и в CLS (`$$UDE: <метка>/...`).
4. **Диспатч:** ядро вызывает `MOM_<имя события>`, поэтому в `.tcl` обязательна
   обёртка:
```tcl
proc MOM_Interpolation_lock { } {
   global mom_command_status mom_lock_axis mom_lock_axis_plane mom_ASCALE_value
   PB_CMD_MOM_Interpolation_lock
}
```
   Без обёртки событие «молчит»: данные в CLS есть, обработчик не вызывается.
5. Деплой: `.tcl`/`.def` (и `.pui`/`.cdl` — для Post Builder) →
   `...\\postprocessor\\LOMO_FG300C\\`, `LOMO_FG300C_ude.cdl` →
   `...\\user_def_event\\LOMO_FG300C.cdl`.
'''

NEW_SECTION = '''
## Как NX находит пост и события (важно)

Механизмов два, они независимы (проверено на NX 2312):

1. **Постпроцессирование.** Список постов — `MACH\\resource\\postprocessor\\
   template_post.dat`: `LOMO_FG300C, …\\LOMO_FG300C.tcl, …\\LOMO_FG300C.def`.
   В рантайме работают **только `.tcl` и `.def`** (+ файлы из `INCLUDE`); `.pui`
   нужен только Post Builder. Каталог событий для пост-движка задаётся в `.def`:
```
INCLUDE {
         $UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl
        }
```
   (`$UGII_CAM_USER_DEF_EVENT_DIR` = `...\\MACH\\resource\\user_def_event`).
2. **UI операции (список User Defined Events).** Берётся **не** из `.def`, а из
   CAM-конфигурации — `MACH\\resource\\configuration\\cam_general.dat` (активный
   конфиг задаёт переменная `UGII_CAM_CONFIG`), строка:
```
USER_DEFINED_EVENTS,${UGII_CAM_USER_DEF_EVENT_DIR}ude.cdl,${UGII_CAM_USER_DEF_EVENT_DIR}ude.tcl
```
   то есть UI читает именно `${UGII_CAM_USER_DEF_EVENT_DIR}ude.cdl` (+ `ude.tcl` —
   библиотека обработчиков событий). Каталог перечитывается на лету: правка
   `ude.cdl` видна в списке **без перезапуска NX**.
3. **Правило:** кастомное событие, которое должно быть и в UI, и в
   постпроцессировании, кладётся **в `ude.cdl`** — файл, который читают оба
   механизма (это же место рекомендует Siemens в
   `POSTBUILD\\pblib\\custom_command\\pb_cmd_set_custom_cycle.tcl`).
   `INCLUDE` отдельного `.cdl` в `.def` на список UI **не влияет** (проверено:
   событие, подключённое только так, после перезапуска NX в списке отсутствует).
   В репозитории блок события хранится в `LOMO_FG300C_ude.cdl`, деплой —
   `python working_script/deploy_ude.py` (идемпотентно вставляет/синхронизирует
   блок в `ude.cdl` и делает бэкап).
4. **Диспатч:** ядро вызывает `MOM_<имя события>`, поэтому в `.tcl` обязательна
   обёртка:
```tcl
proc MOM_Interpolation_lock { } {
   global mom_command_status mom_lock_axis mom_lock_axis_plane mom_ASCALE_value
   PB_CMD_MOM_Interpolation_lock
}
```
   Без обёртки событие «молчит»: данные события попадают в CLS строкой
   `$$UDE: <метка>/...`, но обработчик не вызывается.
5. **Если штатные файлы NX трогать нельзя:** сайтовый CAM-конфиг (копия
   `cam_general.dat` → `cam_lomo.dat` с изменённым `USER_DEFINED_EVENTS`) плюс
   `UGII_CAM_CONFIG` на него; либо `INCLUDE`-цепочка внутри `ude.cdl`
   (`MACHINE FANUC` + `INCLUDE {.../LOMO_FG300C.cdl}`). На этой сборке оба
   варианта не проверялись.
6. Деплой: `.tcl`/`.def` (и `.pui`/`.cdl` — для Post Builder) →
   `...\\postprocessor\\LOMO_FG300C\\`; блок кастомного события → `ude.cdl`
   (`working_script/deploy_ude.py`).
'''

rep('README.md', 'readme/раздел «Как NX находит пост и события»',
    b_of(OLD_SECTION), b_of(NEW_SECTION))

rep('README.md', 'readme/строка про LOMO_FG300C_ude.cdl',
    b_of('| `LOMO_FG300C_ude.cdl` | Кастомные UDE; деплой в `...\\user_def_event\\LOMO_FG300C.cdl` |'),
    b_of('| `LOMO_FG300C_ude.cdl` | Источник блока кастомного события; деплой — вставка блока в `...\\user_def_event\\ude.cdl` (`working_script/deploy_ude.py`) |'))

rep('README.md', 'readme/раздел «Как добавить новое UDE-событие»',
    b_of('''
## Как добавить новое UDE-событие

1. `LOMO_FG300C_ude.cdl`: `EVENT <Имя> { UI_LABEL "<метка>" CATEGORY MILL DRILL
   LATHE PARAM <параметр> { TYPE o DEFVAL "..." OPTIONS "..." UI_LABEL "..." } }`.
2. Развернуть файл в `...\\user_def_event\\LOMO_FG300C.cdl` (он уже в `INCLUDE`).
3. `.tcl`: обёртка `proc MOM_<Имя> { } { … }` + обработчик `PB_CMD_MOM_<Имя>`.
4. Проверка: в CLS появляется строка `$$UDE: <МЕТКА>/...`.
5. `.cdl`/`.pui` поста — по желанию, для консистентности Post Builder.
'''),
    b_of('''
## Как добавить новое UDE-событие

1. В `LOMO_FG300C_ude.cdl` (репозиторий) добавить блок
   `EVENT <Имя> { UI_LABEL "<метка>" CATEGORY MILL DRILL LATHE PARAM <параметр>
   { TYPE o DEFVAL "..." OPTIONS "..." UI_LABEL "..." } }`.
2. Задеплоить блок в каталог UDE: `python working_script/deploy_ude.py`
   (вставляет/синхронизирует блок в `${UGII_CAM_USER_DEF_EVENT_DIR}ude.cdl`,
   делает бэкап). UI подхватит событие сразу, без перезапуска NX.
3. `.tcl`: обёртка `proc MOM_<Имя> { } { … }` + обработчик `PB_CMD_MOM_<Имя>` —
   без неё событие не диспатчится.
4. Проверка: событие есть в списке UDE операции; в CLS есть строка
   `$$UDE: <МЕТКА>/...`.
5. `.cdl`/`.pui` поста — по желанию, для консистентности Post Builder.
'''))

rep('README.md', 'readme/история 2026-09-13',
    b_of('''
- 2026-09-13: кастомное событие `Interpolation_lock` (status / axis / plane /
  ASCALE); `R1` из `ASCALE_value`, `R1`/`ASCALE` — только в нём; обёртка
  `MOM_Interpolation_lock`; кастомный `.cdl` подключён через `INCLUDE`; фиксы
  `global` (`M52` + lock-комментарий и реальная очистка в `MOM_end_of_path`);
  легаси-событие `interpolation_lock` удалено; документация обновлена.
'''),
    b_of('''
- 2026-09-13: кастомное событие `Interpolation_lock` (status / axis / plane /
  ASCALE); `R1` из `ASCALE_value`, `R1`/`ASCALE` — только в нём; обёртка
  `MOM_Interpolation_lock`; фиксы `global` (`M52` + lock-комментарий и реальная
  очистка в `MOM_end_of_path`); легаси-событие `interpolation_lock` удалено.
  Установлено, что список UDE в UI берётся из `ude.cdl` по ключу
  `USER_DEFINED_EVENTS` CAM-конфига (перечитывается без перезапуска NX), а
  `INCLUDE` в `.def` влияет только на пост-движок; блок события деплоится в
  `ude.cdl` скриптом `working_script/deploy_ude.py`; документация обновлена.
'''))

# ------------------------------------------------------------- verification
print()
for name in ('LOMO_FG300C.def', 'README.md'):
    raw = load(name)
    raw.decode('utf-8')
    crlf, lf = raw.count(CR), raw.count(LF)
    print('   %-18s size %-7d CRLF %d  LF %d  lone-LF %d' % (name, len(raw), crlf, lf, lf - crlf))
    assert crlf == lf, '%s: mixed line endings' % name
d = load('LOMO_FG300C.def')
assert d.count(b'LOMO_FG300C.cdl') == 0, '.def still references the custom cdl'
assert d.count(b'$UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl') == 1
r = load('README.md').decode('utf-8')
for m in ('USER_DEFINED_EVENTS', 'cam_general.dat', 'deploy_ude.py', 'без перезапуска NX'):
    assert m in r, 'README misses %r' % m
    print('   README has %r' % m)
print('ALL DONE')
