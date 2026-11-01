import json
import sys


def run(flag: bool, values: list[int]) -> str:
    return json.dumps(
        values
    ) if flag else sys.version
