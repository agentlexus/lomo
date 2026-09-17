# -*- coding: utf-8 -*-
# Append the 2026-09-17 changelog entry to FG300C_5x/README.md (UTF-8, CRLF).
# Idempotent: skips if the entry is already present.

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\README.md'

ANCHOR = '## Примечание'.encode('utf-8')

ENTRY_LINES = [
    '- 2026-09-17: смена инструмента выводится для каждого инструмента, а не только',
    '  для первого. Причина: в `PB_auto_tool_change` флаг `mom_sys_first_tool_handled`',
    '  гасил смену на второй и последующие инструменты (`MOM_first_tool` ведёт их в',
    '  `MOM_tool_change`, а дублирующего `MOM_tool_change` для первого инструмента NX',
    '  не выдаёт, поэтому флаг не сбрасывался). Заменено проверкой по номеру',
    '  инструмента `pb_last_tool_change_number`; диспатч `MOM_tool_change` сделан',
    '  полным (`default`/`else` -> `PB_auto_tool_change`). Раньше вторая секция',
    '  (PLANAR_DEBURRING) обрабатывалась предыдущим инструментом (T3 вместо T6) без',
    '  `M9`/`M5`/`M8`/`M3`.',
]


def main():
    raw = open(PATH, 'rb').read()

    if '2026-09-17'.encode('utf-8') in raw:
        print('Already patched: 2026-09-17 entry present. No-op.')
        return

    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF'
    n = raw.count(ANCHOR)
    assert n == 1, 'anchor ## Примечание found %d times (expected 1)' % n

    entry = b'\r\n'.join(l.encode('utf-8') for l in ENTRY_LINES) + b'\r\n\r\n'
    raw = raw.replace(ANCHOR, entry + ANCHOR)

    assert raw.count(b'\r\n') == raw.count(b'\n'), 'not uniform CRLF after'
    open(PATH, 'wb').write(raw)

    i = raw.find('2026-09-17'.encode('utf-8'))
    print(raw[i:i + 1200].decode('utf-8'))
    print('OK: README.md changelog updated')


if __name__ == '__main__':
    main()
