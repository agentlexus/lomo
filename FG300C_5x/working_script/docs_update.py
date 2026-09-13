# -*- coding: utf-8 -*-
# Documentation update (2026-09-13):
#   1) README.md is rewritten: the lock mode is now driven by the custom UDE
#      "Interpolation_lock", and the .cdl -> INCLUDE registration is documented.
#      The old README had a corrupted (cp1251) tail, so it is written from
#      scratch as UTF-8 + CRLF.
#   2) lock_axis_plan.md gets a final section with the actual implementation.
import os

BASE = r'd:\Programs\GitHub\lomo\FG300C_5x'


def to_crlf(text, lead_blank=0):
    lines = text.replace('\r\n', '\n').strip('\n').split('\n')
    return b'\r\n' * lead_blank + b''.join(l.encode('utf-8') + b'\r\n' for l in lines)


README_P2 = r"""
В лок-режиме выводится: `M52 ;(C-axis loose)` + `;INTERPOLATION LOCK. 4-AXIS
MACHINING (TABLE C ROTATION).`, `TRAFOOF`, `R1=<ASCALE_value>` и
`ASCALE X=R1 Y=R1`, а рабочий контур вокруг центра стола — одним кадром
`G1 G91 C-360.1 F200` + `G90`; дуги подхода/отхода остаются `G2/G3`.

Инварианты (не нарушать):
- `R1`/`ASCALE` — только при включённом событии;
- процедура, читающая `mom_ude_interpolation_lock` или `pb_lock_*`, обязана
  объявить их в `global`: без этого Tcl создаёт локальную переменную, условие
  «молча» ложно и вывод пропадает (так были потеряны `M52` и lock-комментарий);
- состояние чистится в `MOM_end_of_path` (тоже с `global`).

## M-коды осей

| Код | Значение |
|---|---|
| `M50` | разблокировка оси A (непрерывная 5-осевая) |
| `M52` | разблокировка оси C (5-осевая и лок-режим) |

## Режимы обработки (`PB_CMD_m50_m52_unlock`)

1. Лок-режим (событие `Interpolation_lock`) — `M52` + lock-комментарий, `TRAFOOF`.
2. Непрерывная 5-осевая — `M50` + `M52`, `TRAORI`.
3. 3-осевая / 3+2 — `;AXES LOCKED. 3-AXIS MILLING`, `TRAFOOF`.

## Ключевые соглашения

- `CYCLE832(_camtolerance, <метод>, 1)`, метод из CAM (`_ROUGH`/`_FINISH`/…);
  `_camtolerance` печатается с ведущим нулём (`0.06`, не `.06`) —
  `PB_CMD__format_cam_tolerance`.
- Ось C в позиционировании — `C=DC(0.0)` (адрес `fifth_axis_DC`).
- Возврат домой (`TRAFOOF` / `CYCLE800()` / `SUPA G0 Z0.0 D0` / `X0.0` / `Y0.0` /
  `A0.0`) — один раз в начале программы (`pb_home_return_flag`); `G0` в `SUPA`
  форсится (`MOM_force Once Text G_motion ...`), `C0.0` из `SUPA` убран.
- `MOM_first_move` повторяет цепочку `PB_CMD_output_initial_move`; `ORIRESET` и
  `CYCLE800(...)` выводятся только когда их требует операция (для планарной — нет).
- D-номер коррекции — `D[$mom_tool_adjust_register]`.

## Как добавить новое UDE-событие

1. `LOMO_FG300C_ude.cdl`: `EVENT <Имя> { UI_LABEL "<метка>" CATEGORY MILL DRILL
   LATHE PARAM <параметр> { TYPE o DEFVAL "..." OPTIONS "..." UI_LABEL "..." } }`.
2. Развернуть файл в `...\user_def_event\LOMO_FG300C.cdl` (он уже в `INCLUDE`).
3. `.tcl`: обёртка `proc MOM_<Имя> { } { … }` + обработчик `PB_CMD_MOM_<Имя>`.
4. Проверка: в CLS появляется строка `$$UDE: <МЕТКА>/...`.
5. `.cdl`/`.pui` поста — по желанию, для консистентности Post Builder.

## История правок

- 2026-08-28: метод `CYCLE832` из CAM; `C=DC()`; `M50`/`M52` с комментариями;
  preselect инструмента; возврат домой один раз; `SUPA X0.0`; событие
  `interpolation_lock`.
- 2026-09-01: план приведения лок-режима к эталону (`lock_axis_plan.md`).
- 2026-09-08: лок-режим — `TRAFOOF` вместо `TRAORI`, сохранение дуг (`G2/G3`),
  `PB_CMD__rotc_*` (перехват рабочего круга → `G1 G91 C-360.1 F200`).
- 2026-09-11: `G0` во всех `SUPA`; `C0.0` из `SUPA` убран; в планарной операции
  убраны `ORIRESET`/`CYCLE800`; фикс `global pb_home_return_flag`; `_camtolerance`
  с ведущим нулём и вывод в Start of Path; удалены русские комментарии; проект
  переехал в `FG300C_5x/`.
- 2026-09-13: кастомное событие `Interpolation_lock` (status / axis / plane /
  ASCALE); `R1` из `ASCALE_value`, `R1`/`ASCALE` — только в нём; обёртка
  `MOM_Interpolation_lock`; кастомный `.cdl` подключён через `INCLUDE`; фиксы
  `global` (`M52` + lock-комментарий и реальная очистка в `MOM_end_of_path`);
  легаси-событие `interpolation_lock` удалено; документация обновлена.

## Примечание

Автопуш-хук (`.git/hooks/post-commit`) в репозитории не хранится: в текущем клоне
его нет, поэтому пуш делается вручную.
"""


README_P1 = r"""
# Постпроцессор LOMO_FG300C (SINUMERIK ONE)

Памятка для ИИ и разработчиков: режимы, соглашения и история правок, чтобы
будущие изменения не ломали отлаженную логику.

## Назначение

5-осевой фрезерный станок SINUMERIK ONE (G300): стол A + стол C.
Пост: `LOMO_FG300C.tcl` (логика), `.def` (форматы и `INCLUDE`), `.pui` (проект
Post Builder), `.cdl` (объявления UDE), `LOMO_FG300C_ude.cdl` (кастомные UDE).

## Кодировки и переводы строк

| Файлы | Кодировка | EOL |
|---|---|---|
| `LOMO_FG300C.{tcl,def,pui,cdl}`, `LOMO_FG300C_ude.cdl` | ASCII | CRLF |
| `README.md`, `lock_axis_plan.md` | UTF-8 | CRLF |

Русские комментарии из файлов поста удалены (2026-09-11). Пост правится только
байтовыми python-скриптами из `working_script/`: обычный редактор может
перекодировать файл и испортить вывод/EOL.

## Структура проекта

| Путь | Назначение |
|---|---|
| `LOMO_FG300C.tcl` | Логика: обёртки `MOM_*`, обработчики событий, `PB_CMD_*` |
| `LOMO_FG300C.def` | Адреса, форматы, шаблоны блоков, `INCLUDE` каталогов UDE |
| `LOMO_FG300C.pui` | Проект Post Builder: UDE→обработчик, Custom Command |
| `LOMO_FG300C.cdl` | Объявления UDE для Post Builder |
| `LOMO_FG300C_ude.cdl` | Кастомные UDE; деплой в `...\user_def_event\LOMO_FG300C.cdl` |
| `lock_axis_plan.md` | История работ по лок-режиму (разделы 1–10 — предыстория, раздел 11 — актуально) |
| `working_script/*.py` | Патч-скрипты правок поста (байтовые, с assert) |
| `nc/*.mpf`, `raw.cls` | Тестовые УП и CLS для сверки с эталоном |

## Как NX находит пост и события (важно)

1. Список постов — `MACH\resource\postprocessor\template_post.dat`:
   `LOMO_FG300C, ${UGII_CAM_POST_DIR}LOMO_FG300C\LOMO_FG300C.tcl, …\LOMO_FG300C.def`.
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
   (`...\MACH\resource\user_def_event`). Глобальный `ude.cdl` править не нужно:
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
   `...\postprocessor\LOMO_FG300C\`, `LOMO_FG300C_ude.cdl` →
   `...\user_def_event\LOMO_FG300C.cdl`.

## Событие Interpolation_lock (вращение стола C)

| PARAM | Тип | Значения | Смысл |
|---|---|---|---|
| `command_status` | o | Active / Inactive | включение режима |
| `lock_axis` | o | Fourth / Off | ось (стол C) |
| `lock_axis_plane` | o | XYPLAN / NONE | плоскость прохода |
| `ASCALE_value` | d | число (`1.000`) | масштаб `R1` |

В посте это `mom_command_status`, `mom_lock_axis`, `mom_lock_axis_plane`,
`mom_ASCALE_value` (правило NX: `PARAM <имя>` → `mom_<имя>`, регистр важен).

Цепочка:
1. `MOM_Interpolation_lock` (обёртка) → `PB_CMD_MOM_Interpolation_lock` — снимок
   входов в `pb_lock_req`, `pb_lock_axis_req`, `pb_lock_plane_req`, `pb_ascale_req`.
2. `PB_CMD__lock_mode` — единственный источник истины: режим включён при
   `Active` + `fourth` + `xyplan*` (сравнение без учёта регистра: в CLS ось
   приходит как `FOURTH`).
3. `PB_CMD__lock_mode_apply` — публикует вердикт в `mom_ude_interpolation_lock`
   (её читают остальные процедуры); вызывается в начале каждой операции.
4. `MOM_end_of_path` — сброс режима и входов (обязательно через `global`).
"""


PLAN_ADD = r"""

========================================================
11. 2026-09-13. АКТУАЛЬНАЯ РЕАЛИЗАЦИЯ: КАСТОМНОЕ СОБЫТИЕ Interpolation_lock
========================================================
Разделы 1–10 выше — предыстория (в т.ч. открытые вопросы, которые уже закрыты).
Ниже — как лок-режим работает сейчас.

1) Триггер единственный: UDE `Interpolation_lock`
   (`FG300C_5x/LOMO_FG300C_ude.cdl`; деплой — MACH\resource\user_def_event\
   LOMO_FG300C.cdl, подключён в LOMO_FG300C.def через INCLUDE).
   Параметры: command_status (Active/Inactive), lock_axis (Fourth/Off),
   lock_axis_plane (XYPLAN/NONE), ASCALE_value (d) — это же R1 в УП.
   Легаси-событие `interpolation_lock` (ude_interpolation_lock Yes/No) удалено.

2) Цепочка в .tcl:
   MOM_Interpolation_lock (обёртка; ядро диспатчит событие как MOM_<Имя>)
   -> PB_CMD_MOM_Interpolation_lock (снимок входов: pb_lock_req,
      pb_lock_axis_req, pb_lock_plane_req, pb_ascale_req)
   -> PB_CMD__lock_mode (вердикт: Active + fourth + xyplan*, без учёта регистра)
   -> PB_CMD__lock_mode_apply (публикация в mom_ude_interpolation_lock)
   -> читатели: PB_CMD_detect_operation_type (TRAFOOF, ROTARY AXES, сохранение
      дуг), PB_CMD_m50_m52_unlock (M52 + lock-комментарий),
      PB_CMD_output_initial_move (R1 / ASCALE X=R1 Y=R1),
      PB_CMD__rotc_arc_handle / PB_CMD__rotc_linear_cut
      (рабочий круг -> G1 G91 C-360.1 F200 + G90).

3) R1 берётся из PARAM ASCALE_value (mom_ASCALE_value, формат %.3f) и выводится
   только в лок-режиме; в 3-осевой операции R1/ASCALE отсутствуют.

4) Закрытые пункты прежнего плана:
   - OQ1/OQ3: дуги подхода/отхода выходят одним кадром G2/G3 (LINEAR снят),
     рабочий круг гасится в один кадр C-360.1;
   - OQ2: в лок-режиме TRAFOOF, без RTCP;
   - раздел 6.F (позиция M52): M52 выводится в Initial Move (не перед Engage) —
     принято осознанно;
   - G90 выводится после маркера ;Retract Move (совпадает с эталоном);
   - дубль M8 устранён.

5) Проверено генерацией (2026-09-13):
   - interpolation_yes_lock_axis.mpf: R1=1.036, ASCALE X=R1 Y=R1,
     M52 ;(C-axis loose) + ;INTERPOLATION LOCK. 4-AXIS MACHINING (TABLE C
     ROTATION)., G1 G91 C-360.1 F200, G90;
   - interpolation_no_lock_axis.mpf (3-осевая): R1/ASCALE/поворота нет,
     ;AXES LOCKED. 3-AXIS MILLING.

6) Деплой и коммиты — см. README (раздел «Как NX находит пост и события»).
"""


# ---------------------------------------------------------------- write
readme = (README_P1.replace('\r\n', '\n').strip('\n') + '\n\n' +
          README_P2.replace('\r\n', '\n').strip('\n') + '\n')
readme_path = os.path.join(BASE, 'README.md')
open(readme_path, 'wb').write(to_crlf(readme))
print('   README.md written: %d bytes' % os.path.getsize(readme_path))

plan_path = os.path.join(BASE, 'lock_axis_plan.md')
raw = open(plan_path, 'rb').read()
assert raw.startswith(b'\xef\xbb\xbf'), 'lock_axis_plan.md: BOM expected'
text = raw.decode('utf-8-sig')
assert text.rstrip().endswith('Кодировку не менять!'), 'unexpected tail'
assert '11. 2026-09-13' not in text, 'section already added'
raw_new = raw + to_crlf(PLAN_ADD, lead_blank=1)
open(plan_path, 'wb').write(raw_new)
print('   lock_axis_plan.md appended: %d bytes' % len(raw_new))

# ---------------------------------------------------------------- verify
for name in ('README.md', 'lock_axis_plan.md'):
    b = open(os.path.join(BASE, name), 'rb').read()
    b.decode('utf-8')
    crlf, lf = b.count(b'\r\n'), b.count(b'\n')
    print('   %-18s size %-7d CRLF %d  LF %d  lone-LF %d' % (name, len(b), crlf, lf, lf - crlf))
    assert crlf == lf, '%s: mixed line endings' % name
r = open(readme_path, 'rb').read().decode('utf-8')
for m in ('# Постпроцессор LOMO_FG300C', 'INCLUDE', 'MOM_Interpolation_lock',
          'ASCALE_value', 'PB_CMD__lock_mode', '2026-09-13'):
    assert m in r, 'README misses %r' % m
    print('   README has %r' % m)
p = open(plan_path, 'rb').read().decode('utf-8-sig')
for m in ('11. 2026-09-13', 'MOM_Interpolation_lock', 'ASCALE_value'):
    assert m in p, 'plan misses %r' % m
    print('   plan has %r' % m)
print('ALL DONE')
