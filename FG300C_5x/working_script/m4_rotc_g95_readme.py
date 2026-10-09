# -*- coding: utf-8 -*-
# README: refresh the lock-mode rotation description and add the changelog entry.
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(BASE, 'README.md')
CR = b'\r\n'


def main():
    raw = open(PATH, 'rb').read()
    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF'

    if 'G1 G95 C=IC'.encode('utf-8') in raw:
        print('Already patched. No-op.')
        return

    # 1) refresh the stale one-line rotation description
    old = CR.join([
        '`ASCALE X=R1 Y=R1`, а рабочий контур вокруг центра стола — одним кадром'.encode('utf-8'),
        '`G1 G91 C-360.1 F200` + `G90`; дуги подхода/отхода остаются `G2/G3`.'.encode('utf-8'),
    ]) + CR
    new = CR.join([
        '`ASCALE X=R1 Y=R1`, а рабочий контур вокруг центра стола — кадром'.encode('utf-8'),
        '`G1 G95 C=IC(±360.1) F0.03`, ниже `G94`; подача следующего кадра (дуга отхода)'.encode('utf-8'),
        'выводится принудительно (`MOM_force Once F`). Дуги подхода/отхода остаются `G2/G3`.'.encode('utf-8'),
    ]) + CR
    assert raw.count(old) == 1, 'desc anchor count %d' % raw.count(old)
    raw = raw.replace(old, new)

    # 2) changelog entry before the *_COPY explanation section
    anchor = '## Зеркальные координаты операций `*_COPY` (причина и решение)'.encode('utf-8') + CR
    assert raw.count(anchor) == 1, 'section anchor count %d' % raw.count(anchor)
    entry = CR.join([
        '- 2026-10-09: поворот стола C в лок-режиме переведён на подачу на оборот:'.encode('utf-8'),
        '  кадр `G1 G95 C=IC(±360.1) F0.03`, ниже `G94`; подача следующего кадра (дуга'.encode('utf-8'),
        '  отхода) выводится принудительно (`MOM_force Once F` в `PB_CMD__rotc_turn_block`).'.encode('utf-8'),
    ]) + CR + CR
    raw = raw.replace(anchor, entry + anchor)

    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF after'
    open(PATH, 'wb').write(raw)
    print('OK: README.md updated (%d bytes)' % len(raw))


if __name__ == '__main__':
    main()
