# -*- coding: utf-8 -*-
# Correct the 2026-09-23 README entry: machine time was removed, not fixed.

BASE = r'c:\Users\BalagurovAI\Documents\GitHub\lomo\FG300C_5x'
PATH = BASE + r'\README.md'

OLD = '\r\n'.join([
    '- 2026-09-23: шапка УП доведена до эталона. Список инструментов выводится',
    '  в формате `;(T<номер>=<имя> D=<диаметр> R=<радиус> H<NN> D00)` — раньше',
    '  форматы производителя (`MOM_TOOL_BODY`) и потребителя',
    '  (`PB_CMD_creat_tool_list_2`) не совпадали (поле `NAME SUBTYPE DIA ...`',
    '  парсилось как `NUMBER NAME ...`), и строка выходила мусорной; добавлен',
    '  `PB_CMD__fmt_toolval` (число с «точкой»). Machine time в шапке был `0.0`,',
    '  т.к. заголовок печатался до обхода операций; теперь `MOM_OPER_BODY`',
    '  накапливает `mom_machine_time` по объектам `OPERATION` (обход',
    '  `MOM_cycle_objects`), и шапка выводит `;(Machine time: X.XX MIN)`.',
]).encode('utf-8')

NEW = '\r\n'.join([
    '- 2026-09-23: шапка УП — список инструментов приведён к эталонному формату',
    '  `;(T<номер>=<имя> D=<диаметр> R=<радиус> H<NN> D00)` (раньше форматы',
    '  `MOM_TOOL_BODY` и `PB_CMD_creat_tool_list_2` не совпадали — мусорная строка),',
    '  добавлен `PB_CMD__fmt_toolval` (число с «точкой»). Machine time из шапки',
    '  убран полностью: движок не отдаёт время на старте программы, а обход',
    '  объектов `OPERATION` в NX 2312 не поддерживается (ошибка 65).',
]).encode('utf-8')


def main():
    raw = open(PATH, 'rb').read()
    n = raw.count(OLD)
    assert n == 1, 'old entry found %d times' % n
    raw = raw.replace(OLD, NEW)
    open(PATH, 'wb').write(raw)
    print('OK: README entry corrected')


if __name__ == '__main__':
    main()
