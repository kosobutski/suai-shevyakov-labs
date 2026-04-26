"""
Адрес в браузере: http://127.0.0.1:5000/
Лабораторная работа №4 – добавлены управляющие команды
"""

from __future__ import annotations

import json

from flask import Flask, jsonify, render_template, request
from markupsafe import Markup

import things

app = Flask(__name__)


@app.template_filter("tojson_ru")
def tojson_ru(value: object) -> Markup:
    return Markup(json.dumps(value, ensure_ascii=False, indent=2))

_db = things.GreenhouseDatabase()
_climate = things.ClimateSensor("climate-A1", "A", temperature_c=21.3, humidity_percent=58.0)
_soil = things.SoilMoistureSensor("soil-A1", "A", moisture_percent=38.0)
_valve = things.IrrigationValve("valve-A", "A", is_open=False, flow_l_per_min=0.0)
_hub = things.GreenhouseCoordinator(
    sensors=[_climate, _soil],
    actuators=[_valve],
    database=_db,
)


@app.route("/lab3")
def lab2_index():
    # (оставлен как в ЛР3 для демонстрации, но не используется в ЛР4)
    app.logger.info("Маршрут GET /lab3 — демонстрация вызовов методов классов")
    snapshot = _hub.snapshot()
    command_result = _hub.dispatch("valve-A", "set_valve", {"open": True, "flow_l_per_min": 2.0})
    valve_view = _valve.read_telemetry()
    return render_template(
        "index.html",
        climate=_climate,
        soil=_soil,
        valve=valve_view,
        snapshot=snapshot,
        command_result=command_result,
        last_batch=_db.last_sensor_batch(),
        last_commands=_db.command_history()[-3:],
    )


@app.route("/")
def lab3_index():
    """Интерфейс ЛР №4: мониторинг + управление."""
    app.logger.info("Маршрут GET / — интерфейс лабораторной работы №4")
    return render_template("lab3_emulator.html")


@app.route("/connect/climate")
def connect_climate():
    app.logger.info("GET /connect/climate")
    return jsonify(_climate.connect())


@app.route("/connect/soil")
def connect_soil():
    app.logger.info("GET /connect/soil")
    return jsonify(_soil.connect())


@app.route("/connect/valve")
def connect_valve():
    app.logger.info("GET /connect/valve")
    return jsonify(_valve.connect())


# ---------- Маршруты управления (НОВЫЕ для ЛР4) ----------
@app.route("/control/climate")
def control_climate():
    """Управление датчиком климата: установка температуры и/или влажности."""
    temp = request.args.get("temperature_c", type=float)
    hum = request.args.get("humidity_percent", type=float)
    payload = {}
    if temp is not None:
        payload["temperature_c"] = temp
    if hum is not None:
        payload["humidity_percent"] = hum
    if not payload:
        return jsonify({"error": "Не передано ни одного параметра"}), 400
    result = _climate.apply_command("set", payload)
    app.logger.info(f"Управление климатом: {result}")
    return jsonify({"status": "ok", "result": result, "new_telemetry": _climate.read_telemetry()})


@app.route("/control/soil")
def control_soil():
    """Управление датчиком почвы: установка влажности."""
    moisture = request.args.get("moisture_percent", type=float)
    if moisture is None:
        return jsonify({"error": "Не указан параметр moisture_percent"}), 400
    result = _soil.apply_command("set", {"moisture_percent": moisture})
    app.logger.info(f"Управление почвой: {result}")
    return jsonify({"status": "ok", "result": result, "new_telemetry": _soil.read_telemetry()})


@app.route("/control/valve")
def control_valve():
    """Управление клапаном: открыть/закрыть, установить расход."""
    open_valve = request.args.get("open", type=lambda v: v.lower() == "true")
    flow = request.args.get("flow_l_per_min", type=float)
    payload = {}
    if open_valve is not None:
        payload["open"] = open_valve
    if flow is not None:
        payload["flow_l_per_min"] = flow
    if not payload:
        return jsonify({"error": "Не передано ни одной команды"}), 400
    result = _valve.apply_command("set_valve", payload)
    app.logger.info(f"Управление клапаном: {result}")
    return jsonify({"status": "ok", "result": result, "new_telemetry": _valve.read_telemetry()})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)