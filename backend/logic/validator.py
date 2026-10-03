MAX_FIELDS = 50
MAX_NAME_LEN = 60


def validate_request(data, systems):
    """
    systems: {id: (min_teams, max_teams)} только для РЕАЛИЗОВАННЫХ на бэке систем.
    Возвращает (clean, None) или (None, "сообщение человеческим языком").
    Фронт валидирует для UX, бэк — для безопасности: клиенту не доверяем.
    """
    if not isinstance(data, dict):
        return None, "Пустой или некорректный запрос"

    system = data.get("system", "round_robin")
    if system not in systems:
        return None, "Эта система турнира пока недоступна"

    raw = data.get("teams")
    if not isinstance(raw, list) or not all(isinstance(t, str) for t in raw):
        return None, "Список команд передан в неверном формате"

    teams = [t.strip() for t in raw if t.strip()]
    lo, hi = systems[system]
    if len(teams) < lo:
        return None, f"Нужно ввести минимум {lo} команды"
    if len(teams) > hi:
        return None, f"Для этой системы максимум {hi} команд"
    if any(len(t) > MAX_NAME_LEN for t in teams):
        return None, f"Название команды — не длиннее {MAX_NAME_LEN} символов"
    if len({t.casefold() for t in teams}) != len(teams):
        return None, "Названия команд не должны повторяться"

    fields = data.get("parallel_fields")
    # bool — подкласс int, True прошёл бы как 1
    if isinstance(fields, bool) or not isinstance(fields, int) or fields < 1:
        return None, "Нужно минимум 1 поле"

    # Полей больше, чем матчей в слоте, не бывает — не даём раздувать входные данные
    return {"teams": teams, "system": system, "fields": min(fields, MAX_FIELDS)}, None


def verify_schedule(schedule, fields, matches):
    """Страховочная проверка результата. Возвращает список нарушений"""
    errors = []
    prev = set()
    for i, slot in enumerate(schedule, 1):
        busy = {t for m in slot for t in m}
        if len(slot) > fields:
            errors.append(f"слот {i}: больше {fields} матчей")
        if len(busy) != 2 * len(slot):
            errors.append(f"слот {i}: команда играет дважды")
        if busy & prev:
            errors.append(f"слот {i}: игра подряд у {sorted(busy & prev)}")
        prev = busy
    placed = sorted(tuple(sorted(m)) for s in schedule for m in s)
    if placed != sorted(tuple(sorted(m)) for m in matches):
        errors.append("набор матчей не совпадает с исходным")
    return errors
