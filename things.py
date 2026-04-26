"""
Классы IoT-системы «Умная теплица» (ЛР5 – валидация входящих данных)
"""

from __future__ import annotations

import abc
import random
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


def _srv_log(label: str) -> None:
    """Сообщение в лог сервера разработки."""
    print(f"[IoT-сервер] {label}")


class GreenhouseThing(abc.ABC):
    """Абстрактная «вещь» теплицы."""

    def __init__(self, name: str, zone_id: str) -> None:
        _srv_log(f"GreenhouseThing.__init__ -- устройство «{name}», зона {zone_id}")
        self.name = name
        self.zone_id = zone_id
        self._last_command_time = 0.0

    @abc.abstractmethod
    def read_telemetry(self) -> Dict[str, Any]:
        """Снимок состояния для мониторинга."""

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"GreenhouseThing.apply_command (базовая) — {self.name}, команда «{command}»")
        return f"{self.name}: команда «{command}» не поддерживается"

    def _is_emulation_frozen(self) -> bool:
        return (time.time() - self._last_command_time) < 2.0


class ClimateSensor(GreenhouseThing):
    """Датчик температуры и влажности воздуха."""

    def __init__(self, name: str, zone_id: str, temperature_c: float = 22.0, humidity_percent: float = 55.0) -> None:
        _srv_log("ClimateSensor.__init__")
        super().__init__(name, zone_id)
        self.temperature_c = temperature_c
        self.humidity_percent = humidity_percent

    def read_telemetry(self) -> Dict[str, Any]:
        _srv_log(f"ClimateSensor.read_telemetry — {self.name}")
        return {
            "device": self.name,
            "zone": self.zone_id,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
        }

    def emulate(self) -> None:
        if self._is_emulation_frozen():
            _srv_log(f"ClimateSensor.emulate — {self.name} (пропущено, заморозка 2 сек)")
            return
        _srv_log(f"ClimateSensor.emulate — {self.name}")
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

        # --- Проверка температуры (число, диапазон) ---
        if "temperature_c" in payload:
            try:
                temp = float(payload["temperature_c"])
                if not (-10.0 <= temp <= 50.0):
                    errors.append(f"Температура {temp} вне допустимого диапазона [-10, 50]")
                else:
                    self.temperature_c = temp
            except (ValueError, TypeError):
                errors.append(f"Некорректное значение температуры: {payload['temperature_c']} (должно быть число)")

        # --- Проверка влажности (число, диапазон) ---
        if "humidity_percent" in payload:
            try:
                hum = float(payload["humidity_percent"])
                if not (0.0 <= hum <= 100.0):
                    errors.append(f"Влажность {hum} вне допустимого диапазона [0,100]")
                else:
                    self.humidity_percent = hum
            except (ValueError, TypeError):
                errors.append(f"Некорректное значение влажности: {payload['humidity_percent']} (должно быть число)")

        # --- Проверка строкового параметра "unit" через регулярное выражение ---
        if "unit" in payload:
            unit_str = str(payload["unit"])
            # Регулярное выражение: только celsius или fahrenheit
            if not re.fullmatch(r"^(celsius|fahrenheit)$", unit_str, re.IGNORECASE):
                errors.append(f"Недопустимая единица измерения: {unit_str} (допустимо: celsius, fahrenheit)")
            else:
                _srv_log(f"Принята единица измерения: {unit_str}")

        if errors:
            return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
        return f"{self.name}: значения установлены (T={self.temperature_c}°C, H={self.humidity_percent}%)"


class SoilMoistureSensor(GreenhouseThing):
    """Датчик влажности почвы."""

    def __init__(self, name: str, zone_id: str, moisture_percent: float = 40.0) -> None:
        _srv_log("SoilMoistureSensor.__init__")
        super().__init__(name, zone_id)
        self.moisture_percent = moisture_percent

    def read_telemetry(self) -> Dict[str, Any]:
        _srv_log(f"SoilMoistureSensor.read_telemetry — {self.name}")
        return {
            "device": self.name,
            "zone": self.zone_id,
            "moisture_percent": self.moisture_percent,
        }

    def emulate(self) -> None:
        if self._is_emulation_frozen():
            _srv_log(f"SoilMoistureSensor.emulate — {self.name} (пропущено, заморозка 2 сек)")
            return
        _srv_log(f"SoilMoistureSensor.emulate — {self.name}")
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

        # --- Проверка влажности почвы ---
        if "moisture_percent" in payload:
            try:
                moist = float(payload["moisture_percent"])
                if not (0.0 <= moist <= 100.0):
                    errors.append(f"Влажность {moist} вне диапазона [0,100]")
                else:
                    self.moisture_percent = moist
            except (ValueError, TypeError):
                errors.append(f"Некорректное значение влажности: {payload['moisture_percent']} (должно быть число)")

        # --- Проверка строкового режима через регулярное выражение ---
        if "mode" in payload:
            mode_str = str(payload["mode"])
            if not re.fullmatch(r"^(auto|manual|off)$", mode_str, re.IGNORECASE):
                errors.append(f"Недопустимый режим: {mode_str} (допустимо: auto, manual, off)")
            else:
                _srv_log(f"Установлен режим полива: {mode_str}")

        if errors:
            return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
        return f"{self.name}: влажность почвы = {self.moisture_percent}%"


class IrrigationValve(GreenhouseThing):
    """Исполнительный механизм полива."""

    def __init__(self, name: str, zone_id: str, is_open: bool = False, flow_l_per_min: float = 0.0) -> None:
        _srv_log("IrrigationValve.__init__")
        super().__init__(name, zone_id)
        self.is_open = is_open
        self.flow_l_per_min = flow_l_per_min

    def read_telemetry(self) -> Dict[str, Any]:
        _srv_log(f"IrrigationValve.read_telemetry — {self.name}")
        return {
            "device": self.name,
            "zone": self.zone_id,
            "is_open": self.is_open,
            "flow_l_per_min": self.flow_l_per_min,
        }

    def emulate(self) -> None:
        if self._is_emulation_frozen():
            _srv_log(f"IrrigationValve.emulate — {self.name} (пропущено, заморозка 2 сек)")
            return
        _srv_log(f"IrrigationValve.emulate — {self.name}")
        self.is_open = random.choice([True, False])
        self.flow_l_per_min = round(random.uniform(1.5, 3.5), 1) if self.is_open else 0.0

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"IrrigationValve.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"IrrigationValve.apply_command — {self.name}, «{command}»")
        if command != "set_valve":
            return super().apply_command(command, payload)

        payload = payload or {}
        self._last_command_time = time.time()
        errors = []

        # --- Проверка команды открытия (может быть bool или строка) ---
        if "open" in payload:
            open_val = payload["open"]
            # Преобразуем строки "true"/"false" в bool
            if isinstance(open_val, str):
                if open_val.lower() == "true":
                    open_val = True
                elif open_val.lower() == "false":
                    open_val = False
                else:
                    errors.append(f"Некорректное значение open: {open_val} (допустимо: true/false, 1/0)")
            try:
                is_open_bool = bool(open_val)
                self.is_open = is_open_bool
            except Exception:
                errors.append(f"Не удалось преобразовать open: {open_val}")

        # --- Проверка расхода (число, диапазон) ---
        if "flow_l_per_min" in payload:
            try:
                flow = float(payload["flow_l_per_min"])
                if not (0.0 <= flow <= 10.0):
                    errors.append(f"Расход {flow} вне диапазона [0,10] л/мин")
                else:
                    self.flow_l_per_min = flow
            except (ValueError, TypeError):
                errors.append(f"Некорректное значение расхода: {payload['flow_l_per_min']} (должно быть число)")

        # --- Проверка строкового действия через регулярное выражение ---
        if "action" in payload:
            action_str = str(payload["action"])
            if not re.fullmatch(r"^(open|close|setflow|toggle)$", action_str, re.IGNORECASE):
                errors.append(f"Недопустимое действие: {action_str} (допустимо: open, close, setflow, toggle)")
            else:
                if action_str.lower() == "open":
                    self.is_open = True
                elif action_str.lower() == "close":
                    self.is_open = False
                elif action_str.lower() == "toggle":
                    self.is_open = not self.is_open
                # setflow – требует отдельного параметра flow_l_per_min
                _srv_log(f"Выполнено действие: {action_str}")

        if errors:
            return f"{self.name}: ошибка валидации: {'; '.join(errors)}"
        return f"{self.name}: клапан {'открыт' if self.is_open else 'закрыт'}, расход {self.flow_l_per_min} л/мин"


class GreenhouseCoordinator:
    """Координатор без отдельного физического устройства."""

    def __init__(
        self,
        sensors: List[GreenhouseThing],
        actuators: List[GreenhouseThing],
        database: "GreenhouseDatabase",
    ) -> None:
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
    """Сущность хранилища данных (in-memory)"""

    def __init__(self) -> None:
        _srv_log("GreenhouseDatabase.__init__")
        self._sensor_log: List[Dict[str, Any]] = []
        self._command_log: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []

    def log_sensor_readings(self, readings: List[Dict[str, Any]]) -> None:
        _srv_log("GreenhouseDatabase.log_sensor_readings")
        self._sensor_log.append({"ts": datetime.now().isoformat(timespec="seconds"), "readings": readings})

    def log_actuator_command(
        self,
        device_name: str,
        command: str,
        payload: Dict[str, Any],
        result: str,
    ) -> None:
        _srv_log("GreenhouseDatabase.log_actuator_command")
        self._command_log.append(
            {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "device": device_name,
                "command": command,
                "payload": payload,
                "result": result,
            }
        )

    def log_system_event(self, level: str, message: str) -> None:
        _srv_log("GreenhouseDatabase.log_system_event")
        self._events.append({"ts": datetime.now().isoformat(timespec="seconds"), "level": level, "message": message})

    def last_sensor_batch(self) -> Optional[Dict[str, Any]]:
        return self._sensor_log[-1] if self._sensor_log else None

    def command_history(self) -> List[Dict[str, Any]]:
        return list(self._command_log)


__all__ = [
    "GreenhouseThing",
    "ClimateSensor",
    "SoilMoistureSensor",
    "IrrigationValve",
    "GreenhouseCoordinator",
    "GreenhouseDatabase",
]