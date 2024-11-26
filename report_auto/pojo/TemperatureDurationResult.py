__coding__ = "utf-8"

from collections import defaultdict
from typing import Dict, Any


class TemperatureDurationResult:
    def __init__(self):
        self.tecut = defaultdict(float)
        self.x3 = defaultdict(float)
        self.x2 = defaultdict(float)
        self.total_minutes_tecut = 0.0
        self.total_minutes_x3 = 0.0
        self.total_minutes_x2 = 0.0

    def add_durations(self, durations: Dict[str, float], category: str):
        if category == 'TECU_T':
            self.add_tecut(durations)
        elif category == 'X3':
            self.add_x3(durations)
        elif category == 'X2':
            self.add_x2(durations)

    def add_tecut(self, durations: Dict[str, float]):
        for k, v in durations.items():
            self.tecut[k] += v
        self.total_minutes_tecut = round(sum(self.tecut.values()), 2)

    def add_x3(self, durations: Dict[str, float]):
        for k, v in durations.items():
            self.x3[k] += v
        self.total_minutes_x3 = round(sum(self.x3.values()), 2)

    def add_x2(self, durations: Dict[str, float]):
        for k, v in durations.items():
            self.x2[k] += v
        self.total_minutes_x2 = round(sum(self.x2.values()), 2)

    def get_result(self) -> Dict[str, Any]:
        return {
            'tecut': dict(self.tecut),
            'x3': dict(self.x3),
            'x2': dict(self.x2),
            'total_minutes_tecut': self.total_minutes_tecut,
            'total_minutes_x3': self.total_minutes_x3,
            'total_minutes_x2': self.total_minutes_x2
        }
