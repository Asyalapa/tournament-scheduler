import random


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
    best, best_score = None, None
    for i in range(iterations):
        candidate = _build_schedule(matches, parallel_fields, rng, smart=(i % 4 != 3))
        score = (len(candidate), sum(1 for s in candidate if not s))
        if best_score is None or score < best_score:
            best, best_score = candidate, score
    return best
