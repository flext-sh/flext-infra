"""Pytest execution adapter loaded through the public lazy export.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import os
import sys
import traceback
from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra._pytest_clock import FlextInfraPytestClock
from flext_infra.validate import FlextInfraPytestRunner


class FlextInfraPytestProfile:
    """Profile pytest imports and execution without replacing its exit handling."""

    def __init__(self, output: Path) -> None:
        """Keep the profile bound to only the context observed in this invocation."""
        self.output = output
        self.context: m.Infra.PytestRunContext | None = None

    def _record_context(
        self, reports_root: Path, preexisting: frozenset[Path]
    ) -> None:
        """Bind only the context produced by this profiling invocation.

        Args:
            reports_root: The runner's declared report tree.
            preexisting: Context receipts observed before the runner started.

        Raises:
            RuntimeError: The invocation produced more than one matching context.

        """
        owned = [
            receipt
            for receipt in reports_root.glob(f"*-{os.getpid()}/run-context.json")
            if receipt not in preexisting
        ]
        if len(owned) > 1:
            msg = f"profiled run published more than one run context: {owned}"
            raise RuntimeError(msg)
        if owned:
            self.context = m.Infra.PytestRunContext.model_validate_json(
                owned[0].read_text(encoding=c.DEFAULT_ENCODING),
            )

    def run_parent(
        self, *, started_at_monotonic: float, profile: cProfile.Profile
    ) -> int:
        """Bind the profile to the typed runner's repository, never the caller cwd.

        Returns:
            The native runner exit status.

        Raises:
            ValueError: If the profile destination escapes the runner's reports tree.

        """
        # The entry has already started profiling before importing this adapter.
        runner = FlextInfraPytestRunner.from_environment(
            started_at_monotonic=started_at_monotonic,
            collection_command_prefix=(
                sys.executable,
                "-c",
                c.Infra.PYTEST_PROFILE_LAUNCHER,
            ),
            profile_enabled=True,
        )
        if not self.output.resolve().is_relative_to(
            (runner.root / runner.reports.parent).resolve(),
        ):
            msg = "parent profile must stay under the repository reports directory"
            raise ValueError(msg)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.context = None
        self.output.with_suffix(".pstats.json").unlink(missing_ok=True)
        # The runner publishes its run context before any child can fail; the
        # parent binds the profile to the receipt THIS invocation wrote, also
        # when the run fails (a blocked collection is a profiled run too). The
        # runner executes in this process and names its report directory with
        # this pid, so a concurrent run under the shared reports root (another
        # pid) and a receipt that predates this run are both excluded.
        reports_root = runner.root / runner.reports
        preexisting = frozenset(reports_root.glob("*/run-context.json"))

        outcome: int | None = None
        try:
            outcome = runner.execute().unwrap()
            return outcome
        finally:
            failure = sys.exception()
            publication_failure: BaseException | None = None
            try:
                self._record_context(reports_root, preexisting)
            except BaseException as binding_failure:
                publication_failure = binding_failure
            try:
                self._finish(profile)
            except BaseException as finish_failure:
                if publication_failure is None:
                    publication_failure = finish_failure
                else:
                    publication_failure.add_note(
                        "profile finalization failed:\n"
                        + "".join(traceback.format_exception(finish_failure)),
                    )
            if publication_failure is not None:
                if failure is None and outcome in {None, 0}:
                    raise publication_failure
                if failure is not None:
                    failure.add_note(
                        "profile publication failed:\n"
                        + "".join(traceback.format_exception(publication_failure)),
                    )
                else:
                    try:
                        traceback.print_exception(publication_failure)
                    except (OSError, ValueError) as diagnostic_failure:
                        publication_failure.add_note(
                            f"profile diagnostic emission failed: {diagnostic_failure}",
                        )

    def _finish(self, profile: cProfile.Profile) -> None:
        """Keep raw profiles on early failure, but publish only this run's receipt."""
        policy = config.Infra.tooling.tools.pytest
        process_dir = self.output.parent / policy.profile_process_directory
        process_dir.mkdir(parents=True, exist_ok=True)
        process_profile = process_dir / f"{os.getpid()}{self.output.suffix}"
        FlextInfraPytestClock.publish_profile(
            profile,
            self.output,
            immutable_output=process_profile,
        )
        receipt_json: str | None = None
        if self.context is not None:
            receipt = self.context.model_copy(
                update={
                    "profile_sha256": u.Cli.sha256_bytes(process_profile.read_bytes())
                },
            )
            receipt_json = receipt.model_dump_json(indent=2) + "\n"
            u.Cli.atomic_write_text_file(
                process_profile.with_suffix(".pstats.json"),
                receipt_json,
            ).unwrap()
            u.Cli.atomic_write_text_file(
                self.output.with_suffix(".pstats.json"),
                receipt_json,
            ).unwrap()
        if self.context is not None:
            directory = self.context.report_directory
            if directory is not None:
                children = directory / policy.profile_process_directory
                profiles = sorted(children.glob("*.pstats"))
                profiles.extend(
                    artifact
                    for artifact in (
                        directory / c.Infra.PYTEST_SELECTION_PROFILE_FILENAME,
                        directory / c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME,
                    )
                    if artifact.is_file()
                )
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


__all__: list[str] = ["FlextInfraPytestProfile"]
