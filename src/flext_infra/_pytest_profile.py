"""Pytest execution adapter imported after the entry activates cold-start profiling.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import importlib
import os
import sys
from pathlib import Path

from flext_infra import c, config, m, u


class FlextInfraPytestProfile:
    """Profile pytest imports and execution without replacing its exit handling."""

    def __init__(self, output: Path) -> None:
        """Keep the profile bound to only the context observed in this invocation."""
        self.output = output
        self.context: m.Infra.PytestRunContext | None = None

    def run_parent(
        self, *, started_at_monotonic: float, profile: cProfile.Profile
    ) -> int:
        """Retain the entry's profiler, including the adapter's own imports.

        Returns:
            The resulting ``int``.

        Raises:
            ValueError: If parent profile must stay under the repository reports
                directory.

        """
        if not self.output.resolve().is_relative_to(
            (Path.cwd() / ".reports").resolve(),
        ):
            msg = "parent profile must stay under the repository reports directory"
            raise ValueError(msg)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.context = None
        self.output.with_suffix(".pstats.json").unlink(missing_ok=True)
        try:
            return profile.runcall(self._run_parent, started_at_monotonic)
        finally:
            self._finish(profile)

    def _record_context(self, context: m.Infra.PytestRunContext) -> None:
        """Receive the runner's actual context, never a latest-run pointer."""
        self.context = context

    def _run_parent(self, started_at_monotonic: float) -> int:
        # The entry has already started profiling before importing this adapter.
        runner_cls = importlib.import_module(
            "flext_infra.validate.pytest_runner",
        ).FlextInfraPytestRunner
        runner = runner_cls.from_environment(
            started_at_monotonic=started_at_monotonic,
            collection_command_prefix=(
                sys.executable,
                "-c",
                c.Infra.PYTEST_PROFILE_LAUNCHER,
            ),
            profile_enabled=True,
        )
        # The runner publishes its run context before any child can fail; the
        # parent binds the profile to the receipt THIS invocation wrote, also
        # when the run fails (a blocked collection is a profiled run too). The
        # runner executes in this process and names its report directory with
        # this pid, so a concurrent run under the shared reports root (another
        # pid) and a receipt that predates this run are both excluded.
        reports_root = runner.root / runner.reports
        preexisting = frozenset(reports_root.glob("*/run-context.json"))

        def owned_receipts() -> list[Path]:
            return [
                receipt
                for receipt in reports_root.glob(f"*-{os.getpid()}/run-context.json")
                if receipt not in preexisting
            ]

        def bind(owned: list[Path]) -> None:
            if owned:
                self._record_context(
                    m.Infra.PytestRunContext.model_validate_json(
                        owned[0].read_text(encoding="utf-8"),
                    ),
                )

        directory_env = c.Infra.PYTEST_PROFILE_PROCESS_DIRECTORY_ENV
        previous = os.environ.get(directory_env)
        os.environ[directory_env] = (
            config.Infra.tooling.tools.pytest.profile_process_directory
        )
        try:
            outcome = runner.execute().unwrap()
        except BaseException as failure:
            owned = owned_receipts()
            if len(owned) > 1:
                # The original failure stays the one raised; the ambiguity
                # travels with it instead of replacing it.
                failure.add_note(f"profile left unbound: run contexts {owned}")
            else:
                bind(owned)
            raise
        finally:
            if previous is None:
                os.environ.pop(directory_env, None)
            else:
                os.environ[directory_env] = previous
        owned = owned_receipts()
        if len(owned) > 1:
            msg = f"profiled run published more than one run context: {owned}"
            raise RuntimeError(msg)
        bind(owned)
        if not isinstance(outcome, int):
            msg = f"profiled runner returned a non-integer exit status: {outcome!r}"
            raise TypeError(msg)
        return outcome

    def _finish(self, profile: cProfile.Profile) -> None:
        """Keep raw profiles on early failure, but publish only this run's receipt."""
        profile.dump_stats(str(self.output))

        policy = config.Infra.tooling.tools.pytest
        if self.output.name == policy.profile_suite_filename:
            process_dir = self.output.parent / policy.profile_process_directory
            process_dir.mkdir(parents=True, exist_ok=True)
            (process_dir / f"{os.getpid()}{self.output.suffix}").hardlink_to(
                self.output,
            )
        if self.context is not None:
            directory = self.context.report_directory
            if directory is not None:
                children = directory / policy.profile_process_directory
                profiles = sorted(children.glob("*.pstats"))
                suite = directory / policy.profile_suite_filename
                if suite.is_file():
                    profiles.append(suite)
                for child in profiles:
                    child_receipt = self.context.model_copy(
                        update={
                            "profile_sha256": u.Cli.sha256_bytes(child.read_bytes())
                        },
                    )
                    u.Cli.atomic_write_text_file(
                        child.with_suffix(".pstats.json"),
                        child_receipt.model_dump_json(indent=2) + "\n",
                    ).unwrap()
            receipt = self.context.model_copy(
                update={"profile_sha256": u.Cli.sha256_bytes(self.output.read_bytes())},
            )
            u.Cli.atomic_write_text_file(
                self.output.with_suffix(".pstats.json"),
                receipt.model_dump_json(indent=2) + "\n",
            ).unwrap()
