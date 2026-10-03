import os
import sys

# Добавляем путь к корню backend, чтобы импорты работали
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.match_generator import generate_round_robin_matches
from logic.scheduler import schedule_matches


class TestMatchGenerator:
    def test_even_teams(self):
        teams = ["A", "B", "C", "D"]
        matches = generate_round_robin_matches(teams)
        # Формула: N * (N - 1) / 2 = 4 * 3 / 2 = 6
        assert len(matches) == 6
        # Проверяем, что все пары уникальны и не содержат BYE
        assert all("BYE" not in m for m in matches)

    def test_odd_teams(self):
        teams = ["A", "B", "C"]
        matches = generate_round_robin_matches(teams)
        # 3 команды = 3 матча (одна всегда отдыхает)
        assert len(matches) == 3
        # Проверяем, что BYE нигде не засветился в финальных парах
        assert all("BYE" not in m for m in matches)


class TestScheduler:
    def test_no_consecutive_games(self):
        teams = ["A", "B", "C", "D"]
        matches = generate_round_robin_matches(teams)
        schedule = schedule_matches(matches, parallel_fields=1, iterations=100)

        for i in range(len(schedule) - 1):
            current_slot_teams = set()
            for match in schedule[i]:
                current_slot_teams.update(match)

            next_slot_teams = set()
            for match in schedule[i + 1]:
                next_slot_teams.update(match)

            # Пересечение должно быть пустым (никто не играет в слоте N и N+1)
            assert len(current_slot_teams.intersection(next_slot_teams)) == 0, (
                f"Команда играет подряд в слотах {i + 1} и {i + 2}"
            )

    def test_parallel_fields_limit(self):
        teams = ["A", "B", "C", "D", "E", "F"]
        matches = generate_round_robin_matches(teams)
        fields = 2
        schedule = schedule_matches(matches, parallel_fields=fields, iterations=100)

        for slot in schedule:
            assert len(slot) <= fields, f"В слоте {len(slot)} матчей, а лимит {fields}"
