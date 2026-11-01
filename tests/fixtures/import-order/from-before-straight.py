from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from enum import Enum


def run() -> str:
    threading.current_thread()
    return json.dumps([str(datetime.now(UTC)), Enum.__name__])
