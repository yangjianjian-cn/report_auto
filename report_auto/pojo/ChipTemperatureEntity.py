from datetime import datetime


class ChipTemperatureEntity:
    def __init__(self, id, chip_id, temperature, measure_time, source, is_valid):
        self.id = int(id)
        self.chip_id = str(chip_id)
        self.temperature = float(temperature)
        self.measure_time = datetime.fromtimestamp(float(measure_time))  # 使用datetime对象
        self.source = str(source)
        self.is_valid = chr(is_valid)

    def __repr__(self):
        return (f"ChipTemperatureEntity(id={self.id}, "
                f"chip_id='{self.chip_id}', "
                f"temperature={self.temperature}, "
                f"measure_time={self.measure_time.isoformat()}, "
                f"source='{self.source}', "
                f"is_valid='{self.is_valid}')")
