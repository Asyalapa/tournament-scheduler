import logging
import os

from flask import Flask, jsonify, request, send_from_directory

from logic.match_generator import generate_round_robin_matches
from logic.scheduler import schedule_matches
from logic.validator import validate_request, verify_schedule

app = Flask(__name__)
log = logging.getLogger(__name__)

# Фронт отдаётся этим же Flask (same-origin) -> CORS не нужен.
# Если вернёшься к Live Server (:5500) — верни flask_cors и API_URL с портом.
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Реестр систем: новая система = запись здесь + генератор.
# {id: (генератор матчей, минимум команд)} — зеркало TOURNAMENT_SYSTEMS на фронте.
SYSTEMS = {
    "round_robin": (generate_round_robin_matches, 2),
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
    # silent=True: при кривом Content-Type/JSON вернём свой JSON, а не HTML-страницу 415/400
    clean, problem = validate_request(
        request.get_json(silent=True), {k: v[1] for k, v in SYSTEMS.items()}
    )
    if problem:
        return error(problem)

    generator = SYSTEMS[clean["system"]][0]
    matches = generator(clean["teams"])
    schedule_slots = schedule_matches(matches, clean["fields"])

    violations = verify_schedule(schedule_slots, clean["fields"], matches)
    if violations:  # не должно случаться; если случилось — лучше 500, чем неверное расписание
        log.error("Schedule invariant broken: %s", violations)
        return error("Не удалось составить расписание. Попробуйте ещё раз.", 500)

    schedule_response = [
        {
            "slot": i,
            "type": "match" if slot else "rest",
            "matches": [{"team1": a, "team2": b} for a, b in slot],
        }
        for i, slot in enumerate(schedule_slots, 1)
    ]

    total_slots = len(schedule_slots)
    theoretical_min = -(-len(matches) // clean["fields"])
    return jsonify(
        {
            "status": "success",
            "schedule": schedule_response,
            "stats": {
                "total_matches": len(matches),
                "total_slots": total_slots,
                "rest_slots": sum(1 for s in schedule_slots if not s),
                "theoretical_min": theoretical_min,
                "efficiency": round(theoretical_min / total_slots, 2) if total_slots else 0,
            },
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    # app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
