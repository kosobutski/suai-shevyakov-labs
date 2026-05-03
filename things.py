from __future__ import annotations

import abc
import random
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import pymongo


def _srv_log(label: str) -> None:
    print(f"[IoT-сервер] {label}")


class GreenhouseThing(abc.ABC):
    def __init__(self, name: str, zone_id: str) -> None:
        _srv_log(f"GreenhouseThing.__init__ -- {name}, зона {zone_id}")
        self.name = name
        self.zone_id = zone_id
        self._last_command_time = 0.0

    @abc.abstractmethod
    def read_telemetry(self) -> Dict[str, Any]:
        pass

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"GreenhouseThing.apply_command (базовая) — {self.name}, «{command}»")
        return f"{self.name}: команда «{command}» не поддерживается"

    def _is_emulation_frozen(self) -> bool:
        return (time.time() - self._last_command_time) < 2.0


class ClimateSensor(GreenhouseThing):
    def __init__(self, name: str, zone_id: str, temperature_c: float = 22.0, humidity_percent: float = 55.0) -> None:
        _srv_log("ClimateSensor.__init__")
        super().__init__(name, zone_id)
        self.temperature_c = temperature_c
        self.humidity_percent = humidity_percent

    def read_telemetry(self) -> Dict[str, Any]:
        return {
            "device": self.name,
            "zone": self.zone_id,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
        }

    def emulate(self) -> None:
        if self._is_emulation_frozen():
            _srv_log(f"ClimateSensor.emulate — {self.name} (пропущено)")
            return
        self.temperature_c = round(random.uniform(18.0, 30.0), 1)
        self.humidity_percent = round(random.uniform(40.0, 85.0), 1)

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"ClimateSensor.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"ClimateSensor.apply_command — {self.name}, «{command}»")
        if command != "set":
            return super().apply_command(command, payload)
        payload = payload or {}
        self._last_command_time = time.time()
        errors = []
        if "temperature_c" in payload:
            try:
                temp = float(payload["temperature_c"])
                if not (-10.0 <= temp <= 50.0):
                    errors.append(f"Температура {temp} вне диапазона [-10,50]")
                else:
                    self.temperature_c = temp
            except (ValueError, TypeError):
                errors.append(f"Некорректная температура: {payload['temperature_c']}")
        if "humidity_percent" in payload:
            try:
                hum = float(payload["humidity_percent"])
                if not (0.0 <= hum <= 100.0):
                    errors.append(f"Влажность {hum} вне диапазона [0,100]")
                else:
                    self.humidity_percent = hum
            except (ValueError, TypeError):
                errors.append(f"Некорректная влажность: {payload['humidity_percent']}")
        if "unit" in payload:
            unit_str = str(payload["unit"])
            if not re.fullmatch(r"^(celsius|fahrenheit)$", unit_str, re.IGNORECASE):
                errors.append(f"Недопустимая единица: {unit_str}")
            else:
                _srv_log(f"Единица измерения: {unit_str}")
        if errors:
            return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
        return f"{self.name}: T={self.temperature_c}°C, H={self.humidity_percent}%"


class SoilMoistureSensor(GreenhouseThing):
    def __init__(self, name: str, zone_id: str, moisture_percent: float = 40.0) -> None:
        _srv_log("SoilMoistureSensor.__init__")
        super().__init__(name, zone_id)
        self.moisture_percent = moisture_percent

    def read_telemetry(self) -> Dict[str, Any]:
        return {
            "device": self.name,
            "zone": self.zone_id,
            "moisture_percent": self.moisture_percent,
        }

    def emulate(self) -> None:
        if self._is_emulation_frozen():
            _srv_log(f"SoilMoistureSensor.emulate — {self.name} (пропущено)")
            return
        self.moisture_percent = round(random.uniform(25.0, 75.0), 1)

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"SoilMoistureSensor.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"SoilMoistureSensor.apply_command — {self.name}, «{command}»")
        if command != "set":
            return super().apply_command(command, payload)
        payload = payload or {}
        self._last_command_time = time.time()
        errors = []
        if "moisture_percent" in payload:
            try:
                moist = float(payload["moisture_percent"])
                if not (0.0 <= moist <= 100.0):
                    errors.append(f"Влажность {moist} вне диапазона [0,100]")
                else:
                    self.moisture_percent = moist
            except (ValueError, TypeError):
                errors.append(f"Некорректная влажность: {payload['moisture_percent']}")
        if "mode" in payload:
            mode_str = str(payload["mode"])
            if not re.fullmatch(r"^(auto|manual|off)$", mode_str, re.IGNORECASE):
                errors.append(f"Недопустимый режим: {mode_str}")
        if errors:
            return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
        return f"{self.name}: влажность = {self.moisture_percent}%"


class IrrigationValve(GreenhouseThing):
    """Клапан полива с автоматическим режимом"""

    def __init__(self, name: str, zone_id: str, is_open: bool = False, flow_l_per_min: float = 0.0) -> None:
        _srv_log("IrrigationValve.__init__")
        super().__init__(name, zone_id)
        self.is_open = is_open
        self.flow_l_per_min = flow_l_per_min
        self.auto_mode = False
        self.moisture_threshold = 30.0

    def read_telemetry(self) -> Dict[str, Any]:
        return {
            "device": self.name,
            "zone": self.zone_id,
            "is_open": self.is_open,
            "flow_l_per_min": self.flow_l_per_min,
            "auto_mode": self.auto_mode,
            "moisture_threshold": self.moisture_threshold,
        }

    def emulate(self) -> None:
        if self._is_emulation_frozen():
            _srv_log(f"IrrigationValve.emulate — {self.name} (пропущено)")
            return
        if not self.auto_mode:
            self.is_open = random.choice([True, False])
            self.flow_l_per_min = round(random.uniform(1.5, 3.5), 1) if self.is_open else 0.0
        else:
            _srv_log(f"IrrigationValve.emulate — авторежим, состояние не меняется случайно")

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"IrrigationValve.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()

    def auto_control(self, moisture: float) -> None:
        if not self.auto_mode:
            return
        was_open = self.is_open
        if moisture < self.moisture_threshold:
            self.is_open = True
            self.flow_l_per_min = 2.5
        else:
            self.is_open = False
            self.flow_l_per_min = 0.0
        if was_open != self.is_open:
            _srv_log(f"Автоуправление: влажность {moisture}% {'<' if moisture < self.moisture_threshold else '>='} порог {self.moisture_threshold}% → клапан {'открыт' if self.is_open else 'закрыт'}")

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"IrrigationValve.apply_command — {self.name}, «{command}»")
        if command == "set_valve":
            payload = payload or {}
            self._last_command_time = time.time()
            errors = []
            if "open" in payload:
                open_val = payload["open"]
                if isinstance(open_val, str):
                    if open_val.lower() == "true":
                        open_val = True
                    elif open_val.lower() == "false":
                        open_val = False
                    else:
                        errors.append(f"Некорректное open: {open_val}")
                try:
                    self.is_open = bool(open_val)
                    if self.auto_mode:
                        self.auto_mode = False
                        _srv_log(f"Авторежим отключён вручную")
                except Exception:
                    errors.append(f"Не удалось преобразовать open: {open_val}")
            if "flow_l_per_min" in payload:
                try:
                    flow = float(payload["flow_l_per_min"])
                    if not (0.0 <= flow <= 10.0):
                        errors.append(f"Расход {flow} вне диапазона [0,10]")
                    else:
                        self.flow_l_per_min = flow
                except (ValueError, TypeError):
                    errors.append(f"Некорректный расход: {payload['flow_l_per_min']}")
            if errors:
                return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
            return f"{self.name}: клапан {'открыт' if self.is_open else 'закрыт'}, расход {self.flow_l_per_min} л/мин"

        elif command == "set_auto":
            payload = payload or {}
            self._last_command_time = time.time()
            errors = []
            if "auto_mode" in payload:
                try:
                    mode = payload["auto_mode"]
                    if isinstance(mode, str):
                        mode = mode.lower() == "true"
                    self.auto_mode = bool(mode)
                    _srv_log(f"Авторежим {'включён' if self.auto_mode else 'выключен'}")
                except Exception:
                    errors.append(f"Некорректное auto_mode: {payload['auto_mode']}")
            if "moisture_threshold" in payload:
                try:
                    thr = float(payload["moisture_threshold"])
                    if not (0.0 <= thr <= 100.0):
                        errors.append(f"Порог {thr} вне диапазона [0,100]")
                    else:
                        self.moisture_threshold = thr
                except (ValueError, TypeError):
                    errors.append(f"Некорректный порог: {payload['moisture_threshold']}")
            if errors:
                return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
            return f"{self.name}: авторежим = {'вкл' if self.auto_mode else 'выкл'}, порог = {self.moisture_threshold}%"

        else:
            return super().apply_command(command, payload)


class GreenhouseCoordinator:
    def __init__(self, sensors: List[GreenhouseThing], actuators: List[GreenhouseThing], database: "GreenhouseDatabase") -> None:
        _srv_log("GreenhouseCoordinator.__init__")
        self._sensors = sensors
        self._actuators = {a.name: a for a in actuators}
        self._database = database

    def snapshot(self) -> Dict[str, Any]:
        _srv_log("GreenhouseCoordinator.snapshot")
        readings = [s.read_telemetry() for s in self._sensors]
        self._database.log_sensor_readings(readings)
        return {"timestamp": datetime.now().isoformat(timespec="seconds"), "readings": readings}

    def dispatch(self, device_name: str, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"GreenhouseCoordinator.dispatch -- {device_name} / {command}")
        actuator = self._actuators.get(device_name)
        if actuator is None:
            msg = f"Устройство «{device_name}» не найдено"
            self._database.log_system_event("error", msg)
            return msg
        result = actuator.apply_command(command, payload)
        self._database.log_actuator_command(device_name, command, payload or {}, result)
        return result


class GreenhouseDatabase:
    def __init__(self) -> None:
        _srv_log("GreenhouseDatabase.__init__")
        self._sensor_log: List[Dict[str, Any]] = []
        self._command_log: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []

    def log_sensor_readings(self, readings: List[Dict[str, Any]]) -> None:
        _srv_log("GreenhouseDatabase.log_sensor_readings")
        self._sensor_log.append({"ts": datetime.now().isoformat(timespec="seconds"), "readings": readings})

    def log_actuator_command(self, device_name: str, command: str, payload: Dict[str, Any], result: str) -> None:
        _srv_log("GreenhouseDatabase.log_actuator_command")
        self._command_log.append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "device": device_name,
            "command": command,
            "payload": payload,
            "result": result,
        })

    def log_system_event(self, level: str, message: str) -> None:
        _srv_log("GreenhouseDatabase.log_system_event")
        self._events.append({"ts": datetime.now().isoformat(timespec="seconds"), "level": level, "message": message})

    def last_sensor_batch(self) -> Optional[Dict[str, Any]]:
        return self._sensor_log[-1] if self._sensor_log else None

    def command_history(self) -> List[Dict[str, Any]]:
        return list(self._command_log)


class Logger:
    """
    ЛР7: логгер долгосрочного хранения в MongoDB.
    Содержит подключение к БД и последние записанные значения
    для исключения дублей.
    """

    def __init__(self, db_name: str, uri: str = "mongodb://localhost:27017/") -> None:
        _srv_log(f"Logger.__init__ -- DB: {db_name}")
        self._last_climate: Optional[Dict[str, Any]] = None
        self._last_soil: Optional[Dict[str, Any]] = None
        self._last_valve: Optional[Dict[str, Any]] = None
        self._enabled = True
        try:
            self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command("ping")
            self.db = self.client[db_name]
            _srv_log("Logger: MongoDB connection OK")
        except Exception as exc:
            self._enabled = False
            self.client = None
            self.db = None
            _srv_log(f"Logger: MongoDB недоступна ({exc})")

    def _insert_if_changed(self, collection: str, payload: Dict[str, Any], last_value: Optional[Dict[str, Any]]) -> Optional[Any]:
        if payload == last_value:
            _srv_log(f"Logger.{collection}: значение не изменилось, запись пропущена")
            return None
        if not self._enabled or self.db is None:
            _srv_log(f"Logger.{collection}: MongoDB недоступна, запись пропущена")
            return None
        doc = {"timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **payload}
        try:
            return self.db[collection].insert_one(doc)
        except Exception as exc:
            _srv_log(f"Logger.{collection}: ошибка записи ({exc})")
            return None

    def insert_climate_reading(self, data: Dict[str, Any]) -> Optional[Any]:
        payload = {
            "device": data.get("device"),
            "zone": data.get("zone"),
            "temperature_c": data.get("temperature_c"),
            "humidity_percent": data.get("humidity_percent"),
        }
        result = self._insert_if_changed("ClimateReadings", payload, self._last_climate)
        if result is not None:
            self._last_climate = payload
        return result

    def insert_soil_reading(self, data: Dict[str, Any]) -> Optional[Any]:
        payload = {
            "device": data.get("device"),
            "zone": data.get("zone"),
            "moisture_percent": data.get("moisture_percent"),
        }
        result = self._insert_if_changed("SoilReadings", payload, self._last_soil)
        if result is not None:
            self._last_soil = payload
        return result

    def insert_valve_state(self, data: Dict[str, Any]) -> Optional[Any]:
        payload = {
            "device": data.get("device"),
            "zone": data.get("zone"),
            "is_open": data.get("is_open"),
            "flow_l_per_min": data.get("flow_l_per_min"),
            "auto_mode": data.get("auto_mode"),
            "moisture_threshold": data.get("moisture_threshold"),
        }
        result = self._insert_if_changed("ValveStates", payload, self._last_valve)
        if result is not None:
            self._last_valve = payload
        return result


__all__ = [
    "GreenhouseThing",
    "ClimateSensor",
    "SoilMoistureSensor",
    "IrrigationValve",
    "GreenhouseCoordinator",
    "GreenhouseDatabase",
    "Logger",
]