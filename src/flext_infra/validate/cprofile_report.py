"""Typed renderer for canonical focused cProfile artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import io
import os
import pstats
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Self, override

from flext_infra import c, config, m, r, s, u

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCProfileReport(s[bool]):
    """Render one bounded human-readable report from a pstats artifact."""

    profile: Annotated[Path, m.Field(description="Input cProfile pstats path")]
    output: Annotated[Path, m.Field(description="Output text report path")]
    sort: Annotated[
        Literal[
            "calls",
            "cumulative",
            "filename",
            "line",
            "name",
            "nfl",
            "pcalls",
            "stdname",
            "time",
        ],
        m.Field(description="Validated pstats sort key"),
    ]
    limit: Annotated[int, m.Field(gt=0, le=1000, description="Maximum rows to print")]
    run_receipt: Annotated[
        Path | None,
        m.Field(
            description="Native pytest parent profile receipt",
        ),
    ] = None

    @m.model_validator(mode="after")
    def _validate_report_paths(self) -> Self:
        """Confine report paths to their repository or authenticated Git owner.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If cProfile path must stay under.

        """
        report_root = (self.repository_root / c.Infra.REPORTS_DIR_NAME).resolve()
        for path in (
            self.output,
            *((self.run_receipt,) if self.run_receipt is not None else ()),
        ):
            try:
                path.resolve().relative_to(report_root)
            except ValueError as exc:
                msg = f"cProfile path must stay under {report_root}: {path}"
                raise ValueError(msg) from exc
        if not self.profile.resolve().is_relative_to(report_root):
            storage = u.Infra.refactor_report_evidence_root(
                self.repository_root
            ).unwrap()
            profile_root = (storage / c.Infra.REPORTS_DIR_NAME).resolve()
            try:
                self.profile.resolve().relative_to(profile_root)
            except ValueError as exc:
                msg = f"cProfile input must stay under {profile_root}: {self.profile}"
                raise ValueError(msg) from exc
        return self

    def _run_profiles(self) -> t.VariadicTuple[Path]:
        """Validate run identity and artifact digests without consulting latest.

        Returns:
            The resulting ``t.VariadicTuple[Path]``.

        Raises:
            ValueError: If profile run receipt has no valid report directory; or if
                profile run receipt does not match the recorded run context; or if
                profile selection plan does not match its run directory; or if stale or
                mismatched profile run receipt.

        """
        if self.run_receipt is None:
            return (self.profile,)
        parent = m.Infra.PytestRunContext.model_validate_json(
            self.run_receipt.read_text(encoding="utf-8"),
        )
        directory = parent.report_directory
        if directory is None or not directory.resolve().is_relative_to(
            (self.repository_root / ".reports").resolve(),
        ):
            msg = "profile run receipt has no valid report directory"
            raise ValueError(msg)
        context_path = directory / "run-context.json"
        context = m.Infra.PytestRunContext.model_validate_json(
            context_path.read_text(encoding="utf-8"),
        )
        if (
            context.report_directory != directory
            or context.profile_sha256 is not None
            or parent.model_copy(update={"profile_sha256": None}) != context
        ):
            msg = "profile run receipt does not match the recorded run context"
            raise ValueError(msg)
        suite_outcome = directory / "suite-outcome.json"
        full_suite = False
        if (
            parent.testmon_lease_acquired
            and parent.execution_mode == c.Infra.PytestExecutionMode.FULL
            and (suite_outcome.exists() or suite_outcome.is_symlink())
        ):
            capture = m.Infra.GateCaptureStart.model_validate_json(
                (directory / c.Infra.GATE_CAPTURE_START_FILENAME).read_text(
                    encoding="utf-8",
                ),
            )
            intent = capture.intent.test_selection
            if intent is None or intent.execution_mode != parent.execution_mode:
                msg = "profile suite intent does not match its run context"
                raise ValueError(msg)
            full_suite = intent.target_file is None
        policy = config.Infra.tooling.tools.pytest
        suite = directory / policy.profile_suite_filename
        suite_required = True
        if suite_outcome.exists() or suite_outcome.is_symlink():
            outcome = m.Cli.ProcessOutcome.model_validate_json(
                suite_outcome.read_text(encoding="utf-8"),
            )
            if (
                outcome.timed_out
                or outcome.forwarded_signal is not None
                or outcome.raw_return_code < 0
            ):
                sys.stderr.write(
                    "profiled suite interrupted: "
                    f"raw_return_code={outcome.raw_return_code} "
                    f"timed_out={outcome.timed_out} "
                    f"forwarded_signal={outcome.forwarded_signal}; "
                    f"receipt={suite_outcome}\n"
                )
                suite_required = False
        plan_path = directory / "selection-plan.json"
        if parent.testmon_lease_acquired is False:
            if any(entry != context_path for entry in directory.iterdir()):
                msg = "unacquired Testmon lease carries execution artifacts"
                raise ValueError(msg)
            profiles = (self.profile,)
        elif plan_path.is_file():
            plan = m.Infra.PytestSelectionPlan.model_validate_json(
                plan_path.read_text(encoding="utf-8"),
            )
            if plan.manifest_path.parent.resolve() != directory.resolve():
                msg = "profile selection plan does not match its run directory"
                raise ValueError(msg)
            profiles = tuple(
                dict.fromkeys((
                    self.profile,
                    *(
                        ()
                        if full_suite
                        else (plan.manifest_path.with_suffix(".pstats"),)
                    ),
                    *(
                        (directory / c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME,)
                        if plan.inventory_collected and not full_suite
                        else ()
                    ),
                    *(
                        (suite,)
                        if (plan.node_ids and suite_required) or suite.is_file()
                        else ()
                    ),
                    *sorted(
                        (directory / policy.profile_process_directory).glob("*.pstats")
                    ),
                ))
            )
        elif full_suite:
            outcome = m.Cli.ProcessOutcome.model_validate_json(
                suite_outcome.read_text(encoding="utf-8"),
            )
            if u.Cli.process_succeeded(outcome):
                msg = "profile selection plan is absent after a successful suite"
                raise ValueError(msg)
            profiles = tuple(
                dict.fromkeys((
                    self.profile,
                    *((suite,) if suite_required or suite.is_file() else ()),
                    *sorted(
                        (directory / policy.profile_process_directory).glob("*.pstats")
                    ),
                ))
            )
        else:
            inventory_outcome = directory / "inventory-outcome.json"
            selection_outcome = directory / "selection-outcome.json"
            outcome = m.Cli.ProcessOutcome.model_validate_json(
                (
                    inventory_outcome
                    if inventory_outcome.is_file()
                    else selection_outcome
                    if selection_outcome.is_file()
                    else directory / "suite-outcome.json"
                ).read_text(encoding="utf-8"),
            )
            if u.Cli.process_succeeded(outcome):
                msg = "profile selection plan is absent after a successful process"
                raise ValueError(msg)
            profiles = tuple(
                dict.fromkeys((
                    self.profile,
                    directory
                    / (
                        c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
                        if selection_outcome.is_file()
                        and not inventory_outcome.is_file()
                        else c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME
                    ),
                ))
            )
        for profile in profiles:
            receipt = (
                parent
                if profile == self.profile
                else m.Infra.PytestRunContext.model_validate_json(
                    profile.with_suffix(".pstats.json").read_text(encoding="utf-8"),
                )
            )
            if receipt.model_copy(
                update={"profile_sha256": None},
            ) != context or receipt.profile_sha256 != u.Cli.sha256_bytes(
                profile.read_bytes(),
            ):
                msg = f"stale or mismatched profile run receipt: {profile}"
                raise ValueError(msg)
        return profiles

    @override
    def execute(self) -> p.Result[bool]:
        """Load, sort, and render the profile without executing user code.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not self.profile.is_file():
            return r[bool].fail(f"cProfile artifact does not exist: {self.profile}")
        try:
            stream = io.StringIO()
            self._render_profiles(stream)
            self.output.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, ValueError, TypeError) as exc:
            return r[bool].fail(f"render cProfile report failed: {exc}", exception=exc)
        written = u.Cli.atomic_write_text_file(self.output, stream.getvalue())
        if written.failure:
            return r[bool].from_failure(written)
        return r[bool].ok(value=True)

    def _render_profiles(self, stream: io.StringIO) -> None:
        """Render every cProfile artifact into the shared stream."""
        root = self.repository_root.resolve()
        root_prefix = re.escape(str(root) + os.sep)
        source_prefixes = tuple(
            re.escape(str(root / name) + os.sep)
            for name in config.Infra.source_scan.roots
        )
        root_module = root_prefix + rf"[^{re.escape(os.sep)}]+\.py:"
        source_filter = "^(?:" + "|".join((*source_prefixes, root_module)) + ")"
        for profile in self._run_profiles():
            stream.write(f"Profile: {profile}\n")
            stream.write(f"Profile SHA-256 at report: {u.Cli.sha256_file(profile)}\n")
            stream.write(f"Project scope: {root}\n")
            stream.write(f"Capture-time receipt: {self.run_receipt}\n")
            stats = pstats.Stats(str(profile), stream=stream)
            stats.sort_stats(self.sort).print_stats(self.limit)
            stream.write("Native hot-path callers:\n")
            stats.print_callers(self.limit)
            stream.write("Repository source functions:\n")
            stats.print_stats(source_filter, self.limit)
            stream.write("Repository source callers:\n")
            stats.print_callers(source_filter, self.limit)


__all__: list[str] = ["FlextInfraCProfileReport"]
