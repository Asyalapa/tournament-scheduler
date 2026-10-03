import random


def assign_home_away(schedule, seed=None, passes=6000):
    """
    Первая команда в паре — хозяева. Расставляем так, чтобы у каждой команды
    домашние и гостевые матчи чередовались (Д-Г-Д-Г), а серии подряд были редки.
    Порядок матчей в расписании не меняем — только переворачиваем пары.
    """
    rng = random.Random(seed)
    games = [(si, mi) for si, slot in enumerate(schedule) for mi in range(len(slot))]
    seq = {}  # команда -> её матчи в хронологическом порядке
    for si, mi in games:
        for t in schedule[si][mi]:
            seq.setdefault(t, []).append((si, mi))

    def cost(team):
        flags = [schedule[si][mi][0] == team for si, mi in seq[team]]
        breaks = sum(1 for x, y in zip(flags, flags[1:], strict=False) if x == y)  # серии подряд
        return 3 * breaks + abs(2 * sum(flags) - len(flags))  # + перекос дом/гость

    for _ in range(passes if games else 0):
        si, mi = rng.choice(games)
        a, b = schedule[si][mi]
        before = cost(a) + cost(b)
        schedule[si][mi] = (b, a)
        if cost(a) + cost(b) > before:  # ухудшило — откатываем
            schedule[si][mi] = (a, b)
    return schedule
