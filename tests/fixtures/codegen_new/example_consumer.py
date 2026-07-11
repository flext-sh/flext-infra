"""Example consumer executed against a freshly scaffolded FLEXT project.

This is an *example* program (a fixture), not a test: it is run as a real
subprocess by ``project_new_tests.py`` so the scaffold is proven functionally in
an isolated interpreter, exactly as a downstream user would consume it. The
generated ``src`` directory arrives on ``PYTHONPATH`` (set by the parent
process), so imports stay at the top of the module and there is no ``sys.path``
mutation.

It imports the generated ``flext_demo`` package, reaches domain concerns through
the canonical facades and direct config/settings singletons, asserts public
behavior, writes ``OK`` and exits ``0``. Failures propagate as a non-zero exit.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.14 / agent: codegen): example code lives here as a
# fixture (operator live order) — not inline Python inside the test body.
from __future__ import annotations

import sys

from flext_demo import c, config, demo, m, settings


def main() -> int:
    """Import the scaffolded package and assert its facade/namespace contract."""
    assert config.Demo.name == c.Demo.NAME
    assert config.Demo.version == c.Demo.VERSION
    outcome = demo.ping(m.Demo.PingInput())
    assert outcome.success
    expected = (
        config.Demo.ping_reply
        if settings.Demo.enabled
        else config.Demo.disabled_reply
    )
    assert outcome.value.message == expected
    sys.stdout.write("OK\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ImportError, AttributeError) as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        raise SystemExit(1) from exc
