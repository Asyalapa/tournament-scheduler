import logging
import os

from flask import Flask, jsonify, request, send_from_directory

from logic.home_away import assign_home_away
from logic.match_generator import generate_round_robin_matches
from logic.olimpic import build_bracket, schedule_olympic, stage_summary, verify_olympic
from logic.scheduler import schedule_matches
from logic.validator import validate_request, verify_schedule

app = Flask(__name__)
log = logging.getLogger(__name__)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def plan_round_robin(teams, fields):
    matches = generate_round_robin_matches(teams)
    slots = schedule_matches(matches, fields)
    errors = verify_schedule(slots, fields, matches)  # проверяем ДО переворота пар
    slots = assign_home_away(slots)  # первая команда в паре — хозяева
    return {
        "slots": [[{"team1": a, "team2": b} for a, b in s] for s in slots],
        "total": len(matches),
        "errors": errors,
        "stages": [],
        "rest_note": "Без них какая-то команда играла бы два матча подряд.",
    }


def plan_olympic(teams, fields):
    bracket = build_bracket(teams)
    slots = schedule_olympic(bracket, fields)
    keys = ("number", "stage", "team1", "team2", "hint1", "hint2")
    return {
        "slots": [[{k: m[k] for k in keys} for m in s] for s in slots],
        "total": len(bracket),
        "errors": verify_olympic(slots, fields, bracket),
        "stages": stage_summary(slots),
        "rest_note": "Участнику предыдущего матча нужен слот отдыха, а свободных матчей без этого нет.",
    }


# Реестр систем: {id: (планировщик, минимум команд, максимум команд)}
SYSTEMS = {
    "round_robin": (plan_round_robin, 2, 30),
    "olympic": (plan_olympic, 2, 128),
}


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


def error(message, code=400):
    return jsonify({"status": "error", "message": message}), code


@app.route("/api/schedule", methods=["POST"])
def make_schedule():
    clean, problem = validate_request(
        request.get_json(silent=True), {k: (v[1], v[2]) for k, v in SYSTEMS.items()}
    )
    if problem:
        return error(problem)

    plan = SYSTEMS[clean["system"]][0](clean["teams"], clean["fields"])
    if plan["errors"]:  # не должно случаться; лучше 500, чем неверное расписание
        log.error("Schedule invariant broken: %s", plan["errors"])
        return error("Не удалось составить расписание. Попробуйте ещё раз.", 500)

    slots = plan["slots"]
    total_slots = len(slots)
    rests = sum(1 for s in slots if not s)
    theoretical_min = -(-plan["total"] // clean["fields"])
    warnings = [f"Добавлено пауз: {rests}. {plan['rest_note']}"] if rests else []
    return jsonify(
        {
            "status": "success",
            "schedule": [
                {"slot": i, "type": "match" if s else "rest", "matches": s}
                for i, s in enumerate(slots, 1)
            ],
            "stages": plan["stages"],
            "warnings": warnings,
            "stats": {
                "total_matches": plan["total"],
                "total_slots": total_slots,
                "rest_slots": rests,
                "theoretical_min": theoretical_min,
                "efficiency": round(theoretical_min / total_slots, 2) if total_slots else 0,
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
