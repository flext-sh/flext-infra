from __future__ import annotations

from datetime import UTC, datetime
import json
import threading
from enum import Enum


def run() -> str:
    threading.current_thread()
    return json.dumps([str(datetime.now(UTC)), Enum.__name__])
