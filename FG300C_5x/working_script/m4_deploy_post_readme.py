# -*- coding: utf-8 -*-
# README: document working_script/deploy_post.py (structure table + deploy step).
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(BASE, 'README.md')
CR = b'\r\n'


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF'

    if raw.count(b'deploy_post.py') > 0:
        print('Already patched. No-op.')
        return

    # 1) structure table: add a row after the ude.cdl row
    row = '| `LOMO_FG300C_ude.cdl` | Источник блока кастомного события; деплой — вставка блока в `...\\user_def_event\\ude.cdl` (`working_script/deploy_ude.py`) |'.encode('utf-8')
    newrow = '| `working_script/deploy_post.py` | Деплой `.tcl/.def/.pui/.cdl` в папку поста `...\\postprocessor\\LOMO_FG300C\\` (байтовое копирование + бэкап, `--check`) |'.encode('utf-8')
    anchor = row + CR
    assert raw.count(anchor) == 1, 'table row anchor count %d' % raw.count(anchor)
    raw = raw.replace(anchor, anchor + newrow + CR)

    # 2) deploy step (point 6): name deploy_post.py
    old = CR.join([
        '6. Деплой: `.tcl`/`.def` (и `.pui`/`.cdl` — для Post Builder) →'.encode('utf-8'),
        '   `...\\postprocessor\\LOMO_FG300C\\`; блок кастомного события → `ude.cdl`'.encode('utf-8'),
        '   (`working_script/deploy_ude.py`).'.encode('utf-8'),
    ]) + CR
    new = CR.join([
        '6. Деплой: `.tcl`/`.def` (и `.pui`/`.cdl` — для Post Builder) →'.encode('utf-8'),
        '   `...\\postprocessor\\LOMO_FG300C\\` — `working_script/deploy_post.py` (байтовое'.encode('utf-8'),
        '   копирование + бэкап, `--check` для сверки); блок кастомного события →'.encode('utf-8'),
        '   `ude.cdl` — `working_script/deploy_ude.py`.'.encode('utf-8'),
    ]) + CR
    assert raw.count(old) == 1, 'deploy step anchor count %d' % raw.count(old)
    raw = raw.replace(old, new)

    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF after'
    open(PATH, 'wb').write(raw)
    print('OK: README.md updated (%d bytes)' % len(raw))


if __name__ == '__main__':
    main()
