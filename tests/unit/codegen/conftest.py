"""Native lifecycle template fixtures.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from tests import c, m, p, tm, u


class NativeLifecycle:
    """Own real Make children and their isolated physical UV environment."""

    def __init__(self, root: Path, owner: Path) -> None:
        """Render the production lease around actual lock/sync commands."""
        self.root = root
        self.children: list[p.Cli.ManagedProcess] = []
        self.make = shutil.which("make")
        tm.that(self.make is not None)
        uv = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, owner))
        python = Path(sys.executable).resolve()
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "FLEXT_NATIVE_LIFECYCLE_LEASES",
                "LEASE_BARRIER",
                "LEASE_REENTER",
                "LEASE_CLOSE_FD",
                "VIRTUAL_ENV",
                "UV_PROJECT_ENVIRONMENT",
            }
        }
        self.environment["UV_CACHE_DIR"] = str(root / "uv-cache")
        (root / "pyproject.toml").write_text(
            '[project]\nname="native-lifecycle-proof"\nversion="0.0.0"\n'
            f'requires-python="=={sys.version_info.major}.{sys.version_info.minor}.*"\n'
            "dependencies=[]\n[tool.uv]\npackage=false\n",
            encoding="utf-8",
        )
        templates = (
            Path(__file__).resolve().parents[3]
            / "src/flext_infra/templates/project/base"
        )
        renderer = Environment(
            loader=FileSystemLoader(str(templates)), autoescape=select_autoescape()
        )
        lease = renderer.from_string(
            '{% import "lifecycle_lock_recipe.j2" as lease %}'
            "{{ lease.lifecycle_lock_recipe(target) }}",
        )
        lines = [
            "SHELL := /bin/sh",
            f"override RUNTIME_ROOT := {root}",
            "RUNTIME_VENV := $(RUNTIME_ROOT)/.venv",
            "FLEXT_INFRA_EXECUTOR_VENV := $(RUNTIME_ROOT)/.state/executor",
            (
                f"SELF_MAKE := {self.make} --no-print-directory "
                "-f $(RUNTIME_ROOT)/Makefile"
            ),
            "override export UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)",
            "export UV_OFFLINE := true",
            "export UV_NO_PROGRESS := true",
            ".PHONY: setup upg fail _setup_locked _upg_locked _failing_locked",
        ]
        for public, private in (
            ("setup", "_setup_locked"),
            ("upg", "_upg_locked"),
            ("fail", "_failing_locked"),
        ):
            lines.extend((f"{public}:", "\t+@" + lease.render(target=private)))
        arguments = (
            f'--project "$(RUNTIME_ROOT)" --python "{python}" --no-python-downloads'
        )
        sync = f'"{uv}" sync --frozen {arguments}'
        upgrade = f'"{uv}" lock --upgrade {arguments}'
        for target in ("setup", "upg"):
            lines.extend((f"_{target}_locked:", self.event("begin")))
            if target == "upg":
                lines.append("\t@" + upgrade)
            lines.append("\t@" + sync)
            if target == "setup":
                lines.extend((
                    (
                        '\t@if [ -n "$${LEASE_BARRIER:-}" ]; then '
                        ': > "$${LEASE_BARRIER}.ready"; '
                        'read release < "$${LEASE_BARRIER}"; fi'
                    ),
                    (
                        '\t+@if [ "$${LEASE_REENTER:-}" = yes ]; then '
                        'LEASE_REENTER= LEASE_LABEL="$${LEASE_LABEL}.nested" '
                        "$(SELF_MAKE) upg; fi"
                    ),
                    '\t+@if [ "$${LEASE_CLOSE_FD:-}" = yes ]; then "'
                    + str(python)
                    + '" -c \'import os,subprocess; raise SystemExit(subprocess.call(["'
                    + str(self.make)
                    + '","--no-print-directory","upg"],'
                    + "env=os.environ,close_fds=True))'; fi",
                ))
            lines.append(self.event("end"))
        lines.extend((
            "_failing_locked:",
            self.event("begin"),
            "\t@" + upgrade,
            "\t@"
            + sync.replace('"$(RUNTIME_ROOT)"', '"$(RUNTIME_ROOT)/missing-project"'),
            self.event("end"),
        ))
        (root / "Makefile").write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def event(action: str) -> str:
        """Record actual entry and completion inside the native lease.

        Returns:
            The Make recipe writing one receipt.

        """
        return (
            f'\t@printf "%s {action}\\n" "$${{LEASE_LABEL}}" '
            '>> "$(RUNTIME_ROOT)/events"'
        )

    def launch(self, goal: str, label: str, **extra: str) -> p.Cli.ManagedProcess:
        """Start a real workflow in an owned process group.

        Returns:
            The managed native child.

        """
        process = tm.ok(
            u.Cli.process_start(
                (str(self.make), "--no-print-directory", goal),
                cwd=self.root,
                options=m.Cli.ProcessOptions(
                    env={**self.environment, "LEASE_LABEL": label, **extra},
                    inherit_environment=False,
                ),
                start_new_session=True,
            )
        )
        self.children.append(process)
        return process

    @staticmethod
    def finish(process: p.Cli.ManagedProcess, *, failure: bool = False) -> str:
        """Require the expected real outcome and bounded completion.

        Returns:
            The complete native command diagnostic.

        """
        code = tm.ok(process.wait(timeout=20))
        output = process.stdout + process.stderr
        tm.that((code != 0) == failure, msg=output)
        tm.that("warning:" not in output.lower(), msg=output)
        return output

    @staticmethod
    def wait_ready(barrier: Path, process: p.Cli.ManagedProcess) -> None:
        """Bound the wait for the first workflow's actual synchronization point."""
        deadline = time.monotonic() + 10
        while not barrier.with_suffix(".ready").exists():
            tm.that(process.poll() is None)
            tm.that(time.monotonic() < deadline)
            time.sleep(0.01)

    def close(self) -> None:
        """Release only owned process groups, even after a failed assertion."""
        for process in self.children:
            if process.poll() is None:
                tm.ok(process.terminate())
                tm.ok(process.wait(timeout=5))


@pytest.fixture
def native_lifecycle(
    tmp_path: Path, suite_runtime_root: Path
) -> Iterator[NativeLifecycle]:
    """Provide a real UV environment and always retire owned children.

    Yields:
        The seeded isolated native lifecycle.

    """
    lifecycle = NativeLifecycle(tmp_path, suite_runtime_root)
    try:
        lifecycle.finish(lifecycle.launch("upg", "seed"))
        (tmp_path / "events").write_text("", encoding="utf-8")
        yield lifecycle
    finally:
        lifecycle.close()
