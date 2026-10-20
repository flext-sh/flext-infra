"""Pytest execution adapter loaded through the public lazy export.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import os
import signal
import sys
import traceback
from pathlib import Path
from types import FrameType

from flext_infra import c, config, m, p, r, u
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
    ) -> p.Result[bool]:
        """Bind only the context produced by this profiling invocation.

        Args:
            reports_root: The runner's declared report tree.
            preexisting: Context receipts observed before the runner started.

        Returns:
            The binding result, retaining native read or validation failures.

        """
        try:
            owned = [
                receipt
                for receipt in reports_root.glob(f"*-{os.getpid()}/run-context.json")
                if receipt not in preexisting
            ]
            content = owned[0].read_bytes() if len(owned) == 1 else None
        except OSError as read_failure:
            return r[bool].fail(str(read_failure), exception=read_failure)
        if len(owned) > 1:
            msg = f"profiled run published more than one run context: {owned}"
            return r[bool].fail(msg, exception=RuntimeError(msg))
        if content is not None:
            try:
                self.context = m.Infra.PytestRunContext.model_validate_json(content)
            except c.ValidationError as validation_failure:
                return r[bool].fail(
                    str(validation_failure), exception=validation_failure
                )
        return r[bool].ok(value=True)

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
            (runner.repository_root / runner.reports.parent).resolve(),
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
        reports_root = runner.repository_root / runner.reports
        preexisting = frozenset(reports_root.glob("*/run-context.json"))

        outcome: int | None = None

        def terminate(signum: int, _frame: FrameType | None) -> None:
            """Unwind through receipt publication between owned child lifetimes."""
            if _frame is None:
                pass
            raise SystemExit(outcome or 128 + signum)

        previous = signal.getsignal(signal.SIGTERM)
        # Child transports temporarily own forwarding and cleanup; this handler
        # covers the parent work between them without bypassing finalization.
        signal.signal(signal.SIGTERM, terminate)
        try:
            outcome = runner.execute().unwrap()
            return outcome
        finally:
            failure = sys.exception()
            try:
                try:
                    binding = self._record_context(reports_root, preexisting)
                finally:
                    finished = self._finish(profile)
                publication_failure = self._publication_failure(binding, finished)
                if publication_failure is not None:
                    self._settle_publication_failure(
                        publication_failure, failure, outcome
                    )
            finally:
                signal.signal(signal.SIGTERM, previous)

    @staticmethod
    def _publication_failure(
        binding: p.Result[bool], finished: p.Result[bool]
    ) -> BaseException | None:
        """Compose the receipt-binding and profile-finalization failures.

        Returns:
            The binding failure carrying the finalization failure as a note, the
            single failure that occurred, or None when both succeeded.

        """
        binding_failure = (
            binding.exception or RuntimeError(binding.error)
            if binding.failure
            else None
        )
        if not finished.failure:
            return binding_failure
        finish_failure = finished.exception or RuntimeError(finished.error)
        if binding_failure is None:
            return finish_failure
        binding_failure.add_note(
            "profile finalization failed:\n"
            + "".join(traceback.format_exception(finish_failure)),
        )
        return binding_failure

    @staticmethod
    def _settle_publication_failure(
        publication_failure: BaseException,
        failure: BaseException | None,
        outcome: int | None,
    ) -> None:
        """Raise a publication failure of a clean run; attach it to a failed one."""
        if failure is None and outcome in {None, 0}:
            raise publication_failure
        if failure is not None:
            failure.add_note(
                "profile publication failed:\n"
                + "".join(traceback.format_exception(publication_failure)),
            )
            return
        try:
            traceback.print_exception(publication_failure)
        except (OSError, ValueError) as diagnostic_failure:
            # A closed diagnostic stream cannot replace the failed child's status.
            raise SystemExit(outcome) from diagnostic_failure

    def _finish(self, profile: cProfile.Profile) -> p.Result[bool]:
        """Keep raw profiles on early failure, but publish only this run's receipt.

        Returns:
            The publication result, retaining native profile I/O failures.

        """
        try:
            return self._publish_profile(profile)
        except OSError as publication_failure:
            return r[bool].fail(str(publication_failure), exception=publication_failure)

    def _publish_profile(self, profile: cProfile.Profile) -> p.Result[bool]:
        """Publish raw stats before the associated run and child receipts.

        Returns:
            The first receipt publication failure or successful publication.

        """
        policy = config.Infra.tooling.tools.pytest
        process_dir = self.output.parent / policy.profile_process_directory
        process_dir.mkdir(parents=True, exist_ok=True)
        process_profile = process_dir / f"{os.getpid()}{self.output.suffix}"
        FlextInfraPytestClock.publish_profile(
            profile,
            self.output,
            immutable_output=process_profile,
        )
        context = self.context
        if context is None:
            return r[bool].ok(value=True)
        receipt_json = (
            context.model_copy(
                update={
                    "profile_sha256": u.Cli.sha256_bytes(process_profile.read_bytes())
                },
            ).model_dump_json(indent=2)
            + "\n"
        )
        for destination in (process_profile, self.output):
            written = u.Cli.atomic_write_text_file(
                destination.with_suffix(".pstats.json"),
                receipt_json,
            )
            if written.failure:
                return written
        if context.report_directory is None:
            return r[bool].ok(value=True)
        return self._publish_child_receipts(context, context.report_directory)

    @staticmethod
    def _publish_child_receipts(
        context: m.Infra.PytestRunContext, directory: Path
    ) -> p.Result[bool]:
        """Bind every child, selection, inventory and suite profile to the run.

        Returns:
            The first receipt publication failure or successful publication.

        """
        policy = config.Infra.tooling.tools.pytest
        profiles = sorted(
            (directory / policy.profile_process_directory).glob("*.pstats")
        )
        profiles.extend(
            artifact
            for artifact in (
                directory / c.Infra.PYTEST_SELECTION_PROFILE_FILENAME,
                directory / c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME,
                directory / policy.profile_suite_filename,
            )
            if artifact.is_file()
        )
        for child in profiles:
            child_receipt = context.model_copy(
                update={"profile_sha256": u.Cli.sha256_bytes(child.read_bytes())},
            )
            written = u.Cli.atomic_write_text_file(
                child.with_suffix(".pstats.json"),
                child_receipt.model_dump_json(indent=2) + "\n",
            )
            if written.failure:
                return written
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraPytestProfile"]
