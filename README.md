# Постпроцессор LOMO_FG300C (SINUMERIK ONE)

Памятка для ИИ и разработчиков. Содержит ключевые соглашения и историю правок,
чтобы будущие изменения не ломали уже отлаженную логику.

## Назначение

5-осевой фрезерный станок SINUMERIK ONE (G300, стол A + стол C).
Файлы: `LOMO_FG300C.tcl`, `.def`, `.pui`, `.cdl`.

## Структура файлов

| Файл | Назначение |
|---|---|
| `LOMO_FG300C.cdl` | Описание событий (UDE): имена, параметры, UI-метки |
| `LOMO_FG300C.def` | Адреса, форматы, шаблоны блоков (`BLOCK_TEMPLATE`) |
| `LOMO_FG300C.pui` | Привязки событий → обработчики, список Custom Command |
| `LOMO_FG300C.tcl` | Основная логика: обработчики, `PB_CMD_*` процедуры |

**Важно:** файлы в кодировке Windows-1251 (ANSI), CRLF. Русские комментарии
в `.tcl` — в 1251. При правках редактором сохранять кодировку 1251.

## M-коды осей

| Код | Значение |
|---|---|
| `M50` | Разблокировка оси A (`A-axis loose`) |
| `M52` | Разблокировка оси C (`C-axis loose`) |
| `M51` | Блокировка оси (зарезервировано, пока не выводится) |

## Режимы обработки (логика `PB_CMD_m50_m52_unlock`)

1. **Блокировка интерполяции** (`mom_ude_interpolation_lock == "Yes"`):
   4-осевая обработка вращением стола C + `TRAORI` (RTCP). Выводится только
   `M52 ;(C-axis loose)`, ось A заблокирована (без `M50`). Для planar операций
   (например, расфрезеровка вращением стола).
2. **Непрерывная 5-осевая** (`PB_CMD_detect_5axis_tool_path`): `M50` + `M52` + `TRAORI`.
3. **3-осевая / 3+2**: оси заблокированы, `TRAFOOF`.

`TRAORI` включается/выключается через `mom_siemens_5axis_mode` (proc
`PB_CMD_detect_operation_type`).

## Ключевые соглашения (проверено на эталоне 2.mpf)

- **CYCLE832**: `CYCLE832(_camtolerance,_FINISH,1)` — первый параметр переменная
  `_camtolerance`, второй — метод из CAM (`_ROUGH`/`_SEMIFIN`/`_FINISH`/`_OFF`).
  Логика в `PB_CMD__check_block_CYCLE832` (ветка V7) и макрос `CYCLE832_v7`
  (формат `$cycle832_tolm` = `0`, строковый).
- **Ось C в позиционировании**: `C=DC(0.0)` — адрес `fifth_axis_DC`
  (`LEADER "C=DC("`, `TRAILER ")"`), шаблон `rotation_axes`.
- **Возврат домой** (`TRAFOOF`/`CYCLE800()`/`SUPA Z0.0 D0`/`X0.0`/`Y0.0`/`A0.0 C0.0`)
  выводится **один раз** в начале программы (флаг `pb_home_return_flag`
  в `PB_CMD_output_start_of_path`).
- **Смена инструмента**: `M9`/`M5`/`SUPA Z0.0 D0`/`X0.0`/`Y0.0`/`M1`/`T D`/`M6`/
  `T(preselect)`/`SUPA X0.0`/`SUPA Y-400.0` (в `PB_auto_tool_change`,
  `PB_CMD_output_first_tool`).
- **Принудительный вывод `SUPA G0 X0.0`**: перед `return_first_ref_X` стоит
  `MOM_force Once X` (иначе при модальном X0.0 выходит пустой `SUPA`).
- **D-номер коррекции**: `D[$mom_tool_adjust_register]` (не захардкожено в 1,
  в отличие от эталона — оставлено осознанно).

## Событие «Блокировка интерполяции» (Interpolation Lock)

- **UDE-имя**: `interpolation_lock`, параметр `ude_interpolation_lock` (Yes/No).
- **Обработчик**: `PB_CMD_MOM_interpolation_lock` (только объявляет global).
- **Регистрация**: `.cdl` (EVENT), `.pui` (UDE + Custom Command).
- **Эффект**: при `Yes` для planar — 4-осевой режим:
  `M52 ;(C-axis loose)` + `TRAORI` (RTCP, компенсация смещения детали от центра
  вращения стола), ось A заблокирована.
- Реализовано в `PB_CMD_detect_operation_type` (форс `TRAORI`) и
  `PB_CMD_m50_m52_unlock` (только `M52`).

## Как добавить новое UDE-событие (шаблон)

1. `.cdl`: `EVENT <имя> { UI_LABEL "..." CATEGORY MILL PARAM <параметр> { TYPE o DEFVAL "..." OPTIONS "..." UI_LABEL "..." } }`.
2. `.tcl`: `proc PB_CMD_MOM_<имя> { } { global mom_ude_<параметр> }`.
3. `.pui`: строка в списке UDE `{<имя>} {PB_CMD_MOM_<имя>} {Label} {UDE}` +
   в списке Custom Command `{"PB_CMD_MOM_<имя>" "" "Custom Command"} \`.
4. Логика: читать `mom_ude_<параметр>` в нужных `PB_CMD_*`.

## История правок

- 2026-08-28: CYCLE832 метод из CAM; `C=DC()`; M50/M52 с комментариями;
  preselect инструмента; чистый конец пути; возврат домой один раз;
  принудительный `SUPA X0.0`; новое событие `interpolation_lock`.

## ������� (git hook post-commit)

- ����� ������ ���������� ������� ������������� ����������� push � origin/main.
- ���: `.git/hooks/post-commit` (���������, �� � �����������).
- ���� ��� �� ������ (��� ����), ������ ������� �������� � ��� ���������� ��� ��������� `git push`.
