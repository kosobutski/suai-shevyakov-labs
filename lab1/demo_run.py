"""
Демонстрация работы спроектированных классов.
"""

from lab1.greenhouse_system import (
    ClimateSensor,
    GreenhouseCoordinator,
    GreenhouseDatabase,
    IrrigationValve,
    SoilMoistureSensor,
)


def main() -> None:
    db = GreenhouseDatabase()
    sensors: list = [
        ClimateSensor(name="climate-A1", zone_id="A", temperature_c=21.3, humidity_percent=58.0),
        SoilMoistureSensor(name="soil-A1", zone_id="A", moisture_percent=38.0),
    ]
    valve = IrrigationValve(name="valve-A", zone_id="A", is_open=False, flow_l_per_min=0.0)
    hub = GreenhouseCoordinator(sensors=sensors, actuators=[valve], database=db)

    print("Снимок телеметрии (координатор + запись в БД)")
    snap = hub.snapshot()
    print(snap)

    print("\nКоманда на клапан")
    print(hub.dispatch("valve-A", "set_valve", {"open": True, "flow_l_per_min": 2.5}))

    print("\nПоследняя пачка показаний в «БД» (in-memory)")
    print(db.last_sensor_batch())

    print("\nИстория команд")
    for row in db.command_history():
        print(row)


if __name__ == "__main__":
    main()
