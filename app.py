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
_logger = things.Logger("IOT_logger_db")


# ---------- Мониторинг (ЛР3) с логированием в MongoDB ----------
@app.route("/connect/climate")
def connect_climate():
    app.logger.info("GET /connect/climate")
    data = _climate.connect()
    _logger.insert_climate_reading(data)
    return jsonify(data)


@app.route("/connect/soil")
def connect_soil():
    app.logger.info("GET /connect/soil")
    data = _soil.connect()
    _valve.auto_control(_soil.moisture_percent)
    _logger.insert_soil_reading(data)
    _logger.insert_valve_state(_valve.read_telemetry())
    return jsonify(data)


@app.route("/connect/valve")
def connect_valve():
    app.logger.info("GET /connect/valve")
    data = _valve.connect()
    _logger.insert_valve_state(data)
    return jsonify(data)


# ---------- Управление устройствами (ЛР4, ЛР5, ЛР6) ----------
@app.route("/control/climate")
def control_climate():
    payload = {}
    if 'temperature_c' in request.args:
        payload['temperature_c'] = request.args.get('temperature_c')
    if 'humidity_percent' in request.args:
        payload['humidity_percent'] = request.args.get('humidity_percent')
    if 'unit' in request.args:
        payload['unit'] = request.args.get('unit')
    result = _climate.apply_command("set", payload)
    return jsonify({"status": "ok", "result": result, "new_telemetry": _climate.read_telemetry()})


@app.route("/control/soil")
def control_soil():
    payload = {}
    if 'moisture_percent' in request.args:
        payload['moisture_percent'] = request.args.get('moisture_percent')
    if 'mode' in request.args:
        payload['mode'] = request.args.get('mode')
    result = _soil.apply_command("set", payload)
    return jsonify({"status": "ok", "result": result, "new_telemetry": _soil.read_telemetry()})


@app.route("/control/valve")
def control_valve():
    payload = {}
    if 'open' in request.args:
        payload['open'] = request.args.get('open')
    if 'flow_l_per_min' in request.args:
        payload['flow_l_per_min'] = request.args.get('flow_l_per_min')
    if payload:
        result = _valve.apply_command("set_valve", payload)
        return jsonify({"status": "ok", "result": result, "new_telemetry": _valve.read_telemetry()})

    auto_payload = {}
    if 'auto_mode' in request.args:
        auto_payload['auto_mode'] = request.args.get('auto_mode')
    if 'moisture_threshold' in request.args:
        auto_payload['moisture_threshold'] = request.args.get('moisture_threshold')
    if auto_payload:
        result = _valve.apply_command("set_auto", auto_payload)
        return jsonify({"status": "ok", "result": result, "new_telemetry": _valve.read_telemetry()})

    return jsonify({"status": "error", "result": "Нет команд"})


# ---------- Статистика (ЛР8) ----------
@app.route("/stats/climate")
def stats_climate():
    stats = _logger.get_climate_stats()
    return jsonify(stats)


@app.route("/stats/soil")
def stats_soil():
    stats = _logger.get_soil_stats()
    return jsonify(stats)

@app.route("/api/climate-data")
def climate_data():
    """Возвращает последние N записей температуры и влажности для построения графика."""
    limit = request.args.get('limit', default=30, type=int)
    if not _logger._enabled or _logger.db is None:
        return jsonify({"error": "MongoDB недоступна"}), 500

    collection = _logger.db["ClimateReadings"]
    cursor = collection.find({}, {"_id": 0, "timeStamp": 1, "temperature_c": 1, "humidity_percent": 1}).sort("timeStamp", 1).limit(limit)
    data = list(cursor)

    labels = [item.get("timeStamp", "") for item in data]
    temperatures = [item.get("temperature_c") for item in data if item.get("temperature_c") is not None]
    humidities = [item.get("humidity_percent") for item in data if item.get("humidity_percent") is not None]

    return jsonify({
        "labels": labels,
        "temperatures": temperatures,
        "humidities": humidities
    })


# ---------- Главная страница ----------
@app.route("/")
def index():
    return render_template("lab3_emulator.html")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)