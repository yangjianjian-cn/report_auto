__coding__ = "utf-8"
level1: set[str] = {"failed"}
level2: set[str] = set()
level3: set[str] = set()
level4: set[str] = set()

level_map: map = {
    "level1": "passed",
    "level2": "passed",
    "level3": "passed",
    "level4": "passed",
}

levels = {
    "level1": {"failed"},
    "level2": set(),
    "level3": set(),
    "level4": set(),
}

for level, status_set in levels.items():
    if "failed" in status_set:
        level_map[level] = "failed"

level_map: map = {
    "level1": "passed",
    "level2": "passed",
    "level3": "passed",
    "level4": "passed",
}