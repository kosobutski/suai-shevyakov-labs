"""
Адрес в браузере: http://127.0.0.1:5000/
"""

from __future__ import annotations

import json

from flask import Flask, jsonify, render_template
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
    """
    Главная страница: обращение к атрибутам объектов и вызов методов вещей
    (телеметрия, координатор, клапан) — в консоли сервера видны сообщения о запуске методов.
    """
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
    """Интерфейс ЛР №3: мониторинг данных от эмуляторов вещей."""
    app.logger.info("Маршрут GET / — интерфейс лабораторной работы №3")
    return render_template("lab3_emulator.html")


@app.route("/connect/climate")
def connect_climate():
    """Подключение к эмулятору датчика климата."""
    app.logger.info("GET /connect/climate")
    return jsonify(_climate.connect())


@app.route("/connect/soil")
def connect_soil():
    """Подключение к эмулятору датчика влажности почвы."""
    app.logger.info("GET /connect/soil")
    return jsonify(_soil.connect())


@app.route("/connect/valve")
def connect_valve():
    """Подключение к эмулятору клапана полива."""
    app.logger.info("GET /connect/valve")
    return jsonify(_valve.connect())


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
