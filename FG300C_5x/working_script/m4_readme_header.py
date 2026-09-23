# -*- coding: utf-8 -*-
# Append the 2026-09-23 changelog entry to FG300C_5x/README.md (UTF-8, CRLF).

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\README.md'

ANCHOR = '## Примечание'.encode('utf-8')

ENTRY_LINES = [
    '- 2026-09-23: шапка УП доведена до эталона. Список инструментов выводится',
    '  в формате `;(T<номер>=<имя> D=<диаметр> R=<радиус> H<NN> D00)` — раньше',
    '  форматы производителя (`MOM_TOOL_BODY`) и потребителя',
    '  (`PB_CMD_creat_tool_list_2`) не совпадали (поле `NAME SUBTYPE DIA ...`',
    '  парсилось как `NUMBER NAME ...`), и строка выходила мусорной; добавлен',
    '  `PB_CMD__fmt_toolval` (число с «точкой»). Machine time в шапке был `0.0`,',
    '  т.к. заголовок печатался до обхода операций; теперь `MOM_OPER_BODY`',
    '  накапливает `mom_machine_time` по объектам `OPERATION` (обход',
    '  `MOM_cycle_objects`), и шапка выводит `;(Machine time: X.XX MIN)`.',
]


def main():
    raw = open(PATH, 'rb').read()

    if '2026-09-23'.encode('utf-8') in raw:
        print('Already patched: 2026-09-23 entry present. No-op.')
        return

    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF'
    n = raw.count(ANCHOR)
    assert n == 1, 'anchor ## Примечание found %d times (expected 1)' % n

    entry = b'\r\n'.join(l.encode('utf-8') for l in ENTRY_LINES) + b'\r\n\r\n'
    raw = raw.replace(ANCHOR, entry + ANCHOR)

    open(PATH, 'wb').write(raw)

    i = raw.find('2026-09-23'.encode('utf-8'))
    print(raw[i:i + 1200].decode('utf-8'))
    print('OK: README.md changelog updated')


if __name__ == '__main__':
    main()
