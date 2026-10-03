def generate_round_robin_matches(teams):
    """
    Генерирует все матчи для круговой системы (каждый с каждым).
    Возвращает плоский список пар команд.
    """
    teams = list(teams)
    n = len(teams)

    # Если команд нечётное количество — добавляем "bye" (пропуск)
    if n % 2 == 1:
        teams.append(None)
        n += 1

    all_matches = []
    fixed = teams[0]  # Первая команда фиксирована
    rotating = teams[1:]  # Остальные вращаются

    # N-1 раундов (каждая команда должна сыграть с каждой)
    for _ in range(n - 1):
        # Фиксированная команда играет с последней в списке вращающихся
        opponent = rotating[-1]
        if opponent is not None:
            all_matches.append((fixed, opponent))

        # Остальные пары: вторая с предпоследней, третья с третьей с конца и т.д.
        for i in range(len(rotating) // 2):
            team1 = rotating[i]
            team2 = rotating[-(i + 2)]

            # Пропускаем пары с None (bye)
            if team1 is not None and team2 is not None:
                all_matches.append((team1, team2))

        # Вращаем круг: последний элемент становится первым
        rotating = [rotating[-1]] + rotating[:-1]

    return all_matches
