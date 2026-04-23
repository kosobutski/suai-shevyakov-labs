"""
Классы IoT-системы «Умная теплица»
"""

from __future__ import annotations

import abc
import random
from datetime import datetime
from typing import Any, Dict, List, Optional


def _srv_log(label: str) -> None:
    """Сообщение в лог сервера разработки."""
    print(f"[IoT-сервер] Метод запущен: {label}")


class GreenhouseThing(abc.ABC):
    """Абстрактная «вещь» теплицы."""

    def __init__(self, name: str, zone_id: str) -> None:
        _srv_log(f"GreenhouseThing.__init__ -- устройство «{name}», зона {zone_id}")
        self.name = name
        self.zone_id = zone_id

    @abc.abstractmethod
    def read_telemetry(self) -> Dict[str, Any]:
        """Снимок состояния для мониторинга."""

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"GreenhouseThing.apply_command (базовая реализация) — {self.name}, команда «{command}»")
        return f"{self.name}: команда «{command}» не поддерживается"


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
        _srv_log(f"ClimateSensor.emulate — {self.name}")
        self.temperature_c = round(random.uniform(18.0, 30.0), 1)
        self.humidity_percent = round(random.uniform(40.0, 85.0), 1)

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"ClimateSensor.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()


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
        _srv_log(f"SoilMoistureSensor.emulate — {self.name}")
        self.moisture_percent = round(random.uniform(25.0, 75.0), 1)

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"SoilMoistureSensor.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()


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
        _srv_log(f"IrrigationValve.emulate — {self.name}")
        self.is_open = random.choice([True, False])
        self.flow_l_per_min = round(random.uniform(1.5, 3.5), 1) if self.is_open else 0.0

    def connect(self) -> Dict[str, Any]:
        _srv_log(f"IrrigationValve.connect — {self.name}")
        self.emulate()
        return self.read_telemetry()

    def apply_command(self, command: str, payload: Optional[Dict[str, Any]] = None) -> str:
        _srv_log(f"IrrigationValve.apply_command — {self.name}, «{command}»")
        payload = payload or {}
        if command == "set_valve":
            self.is_open = bool(payload.get("open", False))
            self.flow_l_per_min = float(payload.get("flow_l_per_min", 2.5 if self.is_open else 0.0))
            return f"{self.name}: клапан {'открыт' if self.is_open else 'закрыт'}"
        return super().apply_command(command, payload)


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
