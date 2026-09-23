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
| `LOMO_FG300C_ude.cdl` | Источник блока кастомного события; деплой — вставка блока в `...\user_def_event\ude.cdl` (`working_script/deploy_ude.py`) |
| `lock_axis_plan.md` | История работ по лок-режиму (разделы 1–10 — предыстория, раздел 11 — актуально) |
| `working_script/*.py` | Патч-скрипты правок поста (байтовые, с assert) |
| `nc/*.mpf`, `raw.cls` | Тестовые УП и CLS для сверки с эталоном |

## Как NX находит пост и события (важно)

Механизмов два, они независимы (проверено на NX 2312):

1. **Постпроцессирование.** Список постов — `MACH\resource\postprocessor\
   template_post.dat`: `LOMO_FG300C, …\LOMO_FG300C.tcl, …\LOMO_FG300C.def`.
   В рантайме работают **только `.tcl` и `.def`** (+ файлы из `INCLUDE`); `.pui`
   нужен только Post Builder. Каталог событий для пост-движка задаётся в `.def`:
```
INCLUDE {
         $UGII_CAM_USER_DEF_EVENT_DIR/ude.cdl
        }
```
   (`$UGII_CAM_USER_DEF_EVENT_DIR` = `...\MACH\resource\user_def_event`).
2. **UI операции (список User Defined Events).** Берётся **не** из `.def`, а из
   CAM-конфигурации — `MACH\resource\configuration\cam_general.dat` (активный
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
   `POSTBUILD\pblib\custom_command\pb_cmd_set_custom_cycle.tcl`).
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
   `...\postprocessor\LOMO_FG300C\`; блок кастомного события → `ude.cdl`
   (`working_script/deploy_ude.py`).

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

В конце операции 3+2 выводится `CYCLE800()` (сброс разворота стола); перед
3+2 операцией без смены инструмента — ретракт `SUPA G0 Z0.0`, чтобы фреза
отошла от детали до разворота стола.

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
  `MOM_Interpolation_lock`; фиксы `global` (`M52` + lock-комментарий и реальная
  очистка в `MOM_end_of_path`); легаси-событие `interpolation_lock` удалено.
  Установлено, что список UDE в UI берётся из `ude.cdl` по ключу
  `USER_DEFINED_EVENTS` CAM-конфига (перечитывается без перезапуска NX), а
  `INCLUDE` в `.def` влияет только на пост-движок; блок события деплоится в
  `ude.cdl` скриптом `working_script/deploy_ude.py`; документация обновлена.
- 2026-09-13: 3+2 получил собственный комментарий режима — было общее
  `;AXES LOCKED. 3-AXIS MILLING`, стало `;3+2 MILLING MODE` (условие:
  `mom_siemens_coord_rotation != 0`, т.е. операция позиционируется CYCLE800 или
  кадром A-C). Комментарий выводит `PB_CMD__mode_comment`, он же вызывается в
  First-Move-цепочке, поэтому режим помечается в каждой операции.

- 2026-09-14: в конце 3+2 операции закрывается `CYCLE800()` (существующий
  `PB_CMD__check_block_reset_cycle800`), а перед 3+2 операцией, идущей без смены
  инструмента, выводится ретракт `SUPA G0 Z0.0` (новые `PB_CMD__is_3p2` +
  `PB_CMD__output_3p2_retract`, вызываются в First-Move и Initial-Move цепочках).

- 2026-09-15: исправлена инверсия знака Z подхода для 3+2 операций со стороны
  +/-X (M4_rotate / M4 floor_facing): ось C (поворотный стол) была настроена
  SIGN_DETERMINES_DIRECTION, из-за чего обратная кинематика давала зеркальную
  ветку решения (сдвиг 180° в C) для оси инструмента +X. Установлено
  MAGNITUDE_DETERMINES_DIRECTION (mom_kin_5th_axis_direction).

- 2026-09-17: смена инструмента выводится для каждого инструмента, а не только
  для первого. Причина: в `PB_auto_tool_change` флаг `mom_sys_first_tool_handled`
  гасил смену на второй и последующие инструменты (`MOM_first_tool` ведёт их в
  `MOM_tool_change`, а дублирующего `MOM_tool_change` для первого инструмента NX
  не выдаёт, поэтому флаг не сбрасывался). Заменено проверкой по номеру
  инструмента `pb_last_tool_change_number`; диспатч `MOM_tool_change` сделан
  полным (`default`/`else` -> `PB_auto_tool_change`). Раньше вторая секция
  (PLANAR_DEBURRING) обрабатывалась предыдущим инструментом (T3 вместо T6) без
  `M9`/`M5`/`M8`/`M3`.

- 2026-09-23: шапка УП — список инструментов приведён к эталонному формату
  `;(T<номер>=<имя> D=<диаметр> R=<радиус> H<NN> D00)` (раньше форматы
  `MOM_TOOL_BODY` и `PB_CMD_creat_tool_list_2` не совпадали — мусорная строка),
  добавлен `PB_CMD__fmt_toolval` (число с «точкой»). Machine time из шапки
  убран полностью: движок не отдаёт время на старте программы, а обход
  объектов `OPERATION` в NX 2312 не поддерживается (ошибка 65).

## Примечание

Автопуш-хук (`.git/hooks/post-commit`) в репозитории не хранится: в текущем клоне
его нет, поэтому пуш делается вручную.
