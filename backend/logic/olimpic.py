def seed_order(size):
    """Порядок посева в сетке: сильнейшие встречаются как можно позже, пары 1-N, 2-(N-1)..."""
    order = [1, 2]
    while len(order) < size:
        n = len(order) * 2 + 1
        order = [x for s in order for x in (s, n - s)]
    return order


def _stage(rounds_left):
    return "Финал" if rounds_left == 0 else f"1/{2**rounds_left} финала"


def _hint(pool):
    return " / ".join(pool[:4]) + (" …" if len(pool) > 4 else "")


def build_bracket(teams):
    """
    Полная сетка с плейсхолдерами. Посев = порядок ввода (первые команды получают
    «автопроходы» при нечётном числе). Матч: number, stage, team1/team2 (имя или
    «Победитель матча N»), hint1/hint2 (кто может там оказаться), deps [(номер, мин. зазор)].
    """
    n = len(teams)
    k = max(1, (n - 1).bit_length())
    pools, matches, third = {}, [], None

    def make(rnd, stage, x, y, word="Победитель"):
        num = len(matches) + 1
        labels, hints, pool = [], [], []
        for e in (x, y):
            if e[0] == "team":
                labels.append(e[1])
                hints.append("")
                pool.append(e[1])
            else:
                labels.append(f"{word} матча {e[1]}")
                hints.append(_hint(pools[e[1]]))
                pool += pools[e[1]]
        pools[num] = pool
        m = {
            "number": num,
            "round": rnd,
            "stage": stage,
            "team1": labels[0],
            "team2": labels[1],
            "hint1": hints[0],
            "hint2": hints[1],
            "deps": [(e[1], 2) for e in (x, y) if e[0] == "match"],
        }  # 2 = слот отдыха между играми
        matches.append(m)
        return m

    entries = [("team", teams[s - 1]) if s <= n else None for s in seed_order(1 << k)]
    for r in range(1, k + 1):
        semis = [m for m in matches if m["round"] == k - 1]
        if r == k and k >= 2 and len(semis) == 2:  # матч за 3-е место — до финала
            third = make(
                r,
                "Матч за 3-е место",
                ("match", semis[0]["number"]),
                ("match", semis[1]["number"]),
                "Проигравший",
            )
        nxt = []
        for i in range(0, len(entries), 2):
            x, y = entries[i], entries[i + 1]
            if x is None or y is None:  # автопроход
                nxt.append(x or y)
                continue
            nxt.append(("match", make(r, _stage(k - r), x, y)["number"]))
        entries = nxt
    if third:
        matches[-1]["deps"].append((third["number"], 0))  # финал не раньше матча за 3-е
    return matches


def schedule_olympic(bracket, fields):
    """
    Слот за слотом. Матч готов, когда стоят оба «питающих» матча не позже чем
    за слот до него (победителю/проигравшему нужен отдых). Нет готовых — пауза.
    """
    placed, slots = {}, []
    pending = sorted(bracket, key=lambda m: (m["round"], m["number"]))
    while pending:
        s, slot = len(slots), []
        for m in list(pending):
            if len(slot) == fields:
                break
            if all(d in placed and placed[d] <= s - gap for d, gap in m["deps"]):
                slot.append(m)
                placed[m["number"]] = s
                pending.remove(m)
        slots.append(slot)
    return slots


def verify_olympic(slots, fields, bracket):
    pos = {m["number"]: i for i, s in enumerate(slots) for m in s}
    errors = [
        f"слот {i + 1}: больше {fields} матчей" for i, s in enumerate(slots) if len(s) > fields
    ]
    if sorted(pos) != sorted(m["number"] for m in bracket):
        errors.append("набор матчей не совпадает с сеткой")
        return errors
    for m in bracket:
        for d, gap in m["deps"]:
            if pos[m["number"]] - pos[d] < gap:
                errors.append(f"матч {m['number']} стоит слишком близко к матчу {d}")
    return errors


def stage_summary(slots):
    """Оглавление: какие этапы есть, сколько в них матчей и в каких слотах идут."""
    out = {}
    for i, s in enumerate(slots, 1):
        for m in s:
            d = out.setdefault(
                m["stage"], {"name": m["stage"], "matches": 0, "first_slot": i, "last_slot": i}
            )
            d["matches"] += 1
            d["last_slot"] = i
    return list(out.values())
