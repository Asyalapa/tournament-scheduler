import random
import time


def _build_schedule(matches, fields, rng, smart):
    """
    Строит расписание слот за слотом (а не матч за матчем).
    Слот добавляется ТОЛЬКО в конец, поэтому «окно» отдыха
    проверяется строго против предыдущего слота — вставки в прошлые
    «дырки» невозможны, баг с играми подряд исключён конструктивно.

    Если в слот нельзя поставить ни одного матча — это вынужденная
    пауза (пустой слот). После паузы prev пуст, значит следующий слот
    гарантированно получит матч — цикл не зависнет.
    """
    remaining = list(matches)
    rng.shuffle(remaining)

    # Сколько матчей осталось у каждой команды
    load = {}
    for a, b in remaining:
        load[a] = load.get(a, 0) + 1
        load[b] = load.get(b, 0) + 1

    schedule, prev = [], set()
    while remaining:
        # Эвристика: сначала матчи самых «загруженных» команд,
        # иначе в хвосте остаются матчи одной команды и копятся паузы.
        # sorted стабилен -> случайный порядок остаётся тай-брейком.
        pool = sorted(remaining, key=lambda m: -(load[m[0]] + load[m[1]])) if smart else remaining

        slot, busy = [], set()
        for a, b in pool:
            if len(slot) == fields:
                break
            if a in prev or b in prev or a in busy or b in busy:
                continue
            slot.append((a, b))
            busy.update((a, b))

        for a, b in slot:
            remaining.remove((a, b))
            load[a] -= 1
            load[b] -= 1

        schedule.append(slot)  # пустой slot == пауза
        prev = busy
    return schedule


class _Budget(Exception):
    """Попытка исчерпала лимит узлов — перезапускаем со случайным порядком."""


def _try_zero_rest(matches, fields, rng, node_limit):
    """
    Поиск расписания МИНИМАЛЬНОЙ длины и БЕЗ пауз (DFS с отсечениями).
    Ключевое отсечение: команде с n оставшимися матчами нужно минимум 2n-1
    слотов (между играми — отдых). Если слотов осталось меньше — ветка мертва.
    Возвращает расписание, None (доказано: без пауз нельзя) или бросает _Budget.
    """
    slots_total = -(-len(matches) // fields)
    deficit0 = fields * slots_total - len(matches)  # на сколько слотов можно недобрать
    remaining, load, schedule, nodes = set(matches), {}, [], [0]
    for a, b in matches:
        load[a] = load.get(a, 0) + 1
        load[b] = load.get(b, 0) + 1

    def solve(idx, prev, deficit):
        if not remaining:
            return True
        nodes[0] += 1
        if nodes[0] > node_limit:
            raise _Budget
        left = slots_total - idx
        if left <= 0 or any(n and 2 * n - 1 + (t in prev) > left for t, n in load.items()):
            return False
        cands = [m for m in remaining if m[0] not in prev and m[1] not in prev]
        rng.shuffle(cands)
        # Сначала матчи самых «подпирающих» команд (минимальный запас слотов)
        cands.sort(key=lambda m: min(left - 2 * load[m[0]], left - 2 * load[m[1]]))
        return pick(idx, deficit, cands, 0, [], set())

    def pick(idx, deficit, cands, start, slot, busy):
        if len(slot) < fields:
            for i in range(start, len(cands)):
                a, b = cands[i]
                if a in busy or b in busy:
                    continue
                slot.append(cands[i])
                busy.update((a, b))
                if pick(idx, deficit, cands, i + 1, slot, busy):
                    return True
                slot.pop()
                busy.difference_update((a, b))
        short = fields - len(slot)
        if not slot or short > deficit:
            return False
        placed = list(slot)
        for a, b in placed:
            remaining.discard((a, b))
            load[a] -= 1
            load[b] -= 1
        schedule.append(placed)
        if solve(idx + 1, set(busy), deficit - short):
            return True
        schedule.pop()
        for a, b in placed:
            remaining.add((a, b))
            load[a] += 1
            load[b] += 1
        return False

    return schedule if solve(0, set(), deficit0) else None


def _zero_rest(matches, fields, rng, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            return _try_zero_rest(matches, fields, rng, node_limit=20000)
        except _Budget:
            continue  # неудачный порядок — пробуем другой
    return None


def schedule_matches(matches, parallel_fields=1, iterations=None, seed=None):
    """
    Возвращает список слотов; слот — список матчей, пустой слот = пауза.
    Жёсткие правила: не больше parallel_fields матчей в слоте,
    команда не играет два слота подряд и не дважды в одном слоте.
    Среди валидных вариантов выбираем минимум слотов, затем минимум пауз.
    """
    if not matches:
        return []
    if iterations is None:
        # Ограничиваем работу для больших турниров (CPU-бюджет запроса)
        iterations = max(20, min(300, 20000 // len(matches)))

    rng = random.Random(seed)
    # 1) идеал: минимум слотов и ни одной паузы
    ideal = _zero_rest(matches, parallel_fields, rng, seconds=1.5)
    if ideal:
        return ideal
    # 2) без пауз нельзя -> лучший вариант с вынужденными паузами
    best, best_score = None, None
    for i in range(iterations):
        candidate = _build_schedule(matches, parallel_fields, rng, smart=(i % 4 != 3))
        score = (len(candidate), sum(1 for s in candidate if not s))
        if best_score is None or score < best_score:
            best, best_score = candidate, score
    return best
