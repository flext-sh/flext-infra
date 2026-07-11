"""Example consumer executed against a freshly scaffolded FLEXT project.

This is an *example* program (a fixture), not a test: it is run as a real
subprocess by ``project_new_tests.py`` so the scaffold is proven functionally in
an isolated interpreter, exactly as a downstream user would consume it. The
generated ``src`` directory arrives on ``PYTHONPATH`` (set by the parent
process), so imports stay at the top of the module and there is no ``sys.path``
mutation.

It imports the generated ``flext_demo`` package, reaches domain concerns through
the canonical facades and namespaces (``c.Demo`` / ``u.Demo`` /
``config.FlextDemo`` / ``settings.FlextDemo``), asserts the scaffold contract,
emits a single JSON line (``{"status": "OK", ...}``) and exits ``0``. On any
failure it emits ``{"status": "FAIL", ...}`` and exits ``1``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.14 / agent: codegen): example code lives here as a
# fixture (operator live order) — not inline Python inside the test body.
from __future__ import annotations

import json
import sys

from flext_demo import c, config, settings, u


def main() -> int:
    """Import the scaffolded package and assert its facade/namespace contract."""
    facts: dict[str, str | bool] = {
        "c_demo_name": c.Demo.NAME,
        "config_namespace": type(config.Demo).__name__,
        "settings_namespace": type(settings.Demo).__name__,
        "config_has_demo": hasattr(config, "Demo"),
        "settings_has_demo": hasattr(settings, "Demo"),
        "u_has_demo": hasattr(u, "Demo"),
    }
    assert facts["c_demo_name"] == "flext-demo", facts
    assert facts["config_namespace"] == "_DemoNamespace", facts
    assert facts["settings_namespace"] == "DemoSettings", facts
    assert facts["config_has_demo"] is True, facts
    assert facts["settings_has_demo"] is True, facts
    assert facts["u_has_demo"] is True, facts
    sys.stdout.write(json.dumps({"status": "OK", "facts": facts}) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ImportError, AttributeError) as exc:
        failure = {
            "status": "FAIL",
            "error": type(exc).__name__,
            "msg": str(exc),
        }
        sys.stdout.write(json.dumps(failure) + "\n")
        raise SystemExit(1) from exc
