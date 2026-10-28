"""Typed renderer for canonical focused cProfile artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import io
import os
import pstats
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Self, override

from flext_infra import c, config, m, r, s, u

if TYPE_CHECKING:
    from flext_infra import p


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

    def _run_profiles(self) -> tuple[Path, ...]:
        """Validate run identity and artifact digests without consulting latest.

        Returns:
            The resulting ``tuple[Path, ...],``.

        Raises:
            ValueError: If the lease was unacquired yet carries execution artifacts,
                or the selection plan is absent after a successful suite.

        """
        if self.run_receipt is None:
            return (self.profile,)
        parent = m.Infra.PytestRunContext.model_validate_json(
            self.run_receipt.read_text(encoding="utf-8"),
        )
        directory, context = self._recorded_context(parent)
        suite_outcome = directory / "suite-outcome.json"
        full_suite = self._is_full_suite(parent, directory, suite_outcome)
        policy = config.Infra.tooling.tools.pytest
        suite = directory / policy.profile_suite_filename
        suite_required = self._suite_required(suite_outcome)
        plan_path = directory / "selection-plan.json"
        process_profiles = self._process_profiles(directory)
        if parent.testmon_lease_acquired is False:
            context_path = directory / "run-context.json"
            if any(entry != context_path for entry in directory.iterdir()):
                msg = "unacquired Testmon lease carries execution artifacts"
                raise ValueError(msg)
            profiles = (self.profile,)
        elif plan_path.is_file():
            profiles = self._planned_profiles(
                directory,
                m.Infra.PytestSelectionPlan.model_validate_json(
                    plan_path.read_text(encoding="utf-8"),
                ),
                suite=suite,
                suite_required=suite_required,
                full_suite=full_suite,
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
                    *process_profiles,
                ))
            )
        else:
            profiles = self._unplanned_profiles(directory)
        self._verify_profile_receipts(profiles, parent, context)
        return profiles

    def _recorded_context(
        self, parent: m.Infra.PytestRunContext
    ) -> tuple[Path, m.Infra.PytestRunContext]:
        """Load the run context recorded beside the parent receipt.

        Returns:
            The report directory and its recorded run context.

        Raises:
            ValueError: If the receipt has no valid report directory or does not
                match the recorded run context.

        """
        directory = parent.report_directory
        if directory is None or not directory.resolve().is_relative_to(
            (self.repository_root / ".reports").resolve(),
        ):
            msg = "profile run receipt has no valid report directory"
            raise ValueError(msg)
        context = m.Infra.PytestRunContext.model_validate_json(
            (directory / "run-context.json").read_text(encoding="utf-8"),
        )
        if (
            context.report_directory != directory
            or context.profile_sha256 is not None
            or parent.model_copy(update={"profile_sha256": None}) != context
        ):
            msg = "profile run receipt does not match the recorded run context"
            raise ValueError(msg)
        return directory, context

    @staticmethod
    def _is_full_suite(
        parent: m.Infra.PytestRunContext,
        directory: Path,
        suite_outcome: Path,
    ) -> bool:
        """Report whether the leased run executed a whole-project FULL suite.

        Returns:
            True when the recorded intent selects the whole project.

        Raises:
            ValueError: If the suite intent does not match its run context.

        """
        if not (
            parent.testmon_lease_acquired
            and parent.execution_mode == c.Infra.PytestExecutionMode.FULL
            and (suite_outcome.exists() or suite_outcome.is_symlink())
        ):
            return False
        capture = m.Infra.GateCaptureStart.model_validate_json(
            (directory / c.Infra.GATE_CAPTURE_START_FILENAME).read_text(
                encoding="utf-8",
            ),
        )
        intent = capture.intent.test_selection
        if intent is None or intent.execution_mode != parent.execution_mode:
            msg = "profile suite intent does not match its run context"
            raise ValueError(msg)
        return intent.target_file is None

    @staticmethod
    def _suite_required(suite_outcome: Path) -> bool:
        """Report whether the suite profile must exist or was interrupted.

        Returns:
            False when the recorded suite process was interrupted.

        """
        if not (suite_outcome.exists() or suite_outcome.is_symlink()):
            return True
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
            return False
        return True

    def _planned_profiles(
        self,
        directory: Path,
        plan: m.Infra.PytestSelectionPlan,
        *,
        suite: Path,
        suite_required: bool,
        full_suite: bool,
    ) -> tuple[Path, ...]:
        """Elect the profile artifacts of a run that recorded a selection plan.

        Returns:
            The ordered, de-duplicated profile artifacts.

        Raises:
            ValueError: If the selection plan does not match its run directory.

        """
        if plan.manifest_path.parent.resolve() != directory.resolve():
            msg = "profile selection plan does not match its run directory"
            raise ValueError(msg)
        return tuple(
            dict.fromkeys((
                self.profile,
                *(() if full_suite else (plan.manifest_path.with_suffix(".pstats"),)),
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
                *self._process_profiles(directory),
            ))
        )

    @staticmethod
    def _process_profiles(directory: Path) -> tuple[Path, ...]:
        """List the per-process profile artifacts of one run directory.

        Returns:
            The sorted per-process ``.pstats`` artifacts.

        """
        policy = config.Infra.tooling.tools.pytest
        return tuple(
            sorted((directory / policy.profile_process_directory).glob("*.pstats"))
        )

    def _unplanned_profiles(self, directory: Path) -> tuple[Path, ...]:
        """Elect the profile artifacts of a run that failed before planning.

        Returns:
            The ordered, de-duplicated profile artifacts.

        Raises:
            ValueError: If the selection plan is absent after a successful process.

        """
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
        return tuple(
            dict.fromkeys((
                self.profile,
                directory
                / (
                    c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
                    if selection_outcome.is_file() and not inventory_outcome.is_file()
                    else c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME
                ),
            ))
        )

    def _verify_profile_receipts(
        self,
        profiles: tuple[Path, ...],
        parent: m.Infra.PytestRunContext,
        context: m.Infra.PytestRunContext,
    ) -> None:
        """Require every profile to carry its matching run receipt and digest.

        Raises:
            ValueError: If a profile run receipt is stale or mismatched.

        """
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
