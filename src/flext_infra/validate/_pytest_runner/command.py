"""Canonical pytest argv for persistent testmon execution."""

from __future__ import annotations

import hashlib
import sys
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
from typing import Final

from flext_infra import c, config, t

from .base import FlextInfraPytestRunnerBase

_NO_COVERAGE: Final[t.VariadicTuple[str]] = ("--no-cov",)
_TOOLCHAIN_PACKAGES: Final[t.StrTuple] = (
    "flext-infra",
    "flext-tests",
    "pytest",
    "pytest-testmon",
)


@lru_cache(maxsize=1)
def _toolchain_testmon_environment() -> str:
    """Return the toolchain-fingerprinted testmon environment name.

    The environment name digests the exact runner toolchain versions, so a
    runner or plugin upgrade can never read a database written by an older
    toolchain as a hot cache: the new environment starts cold and the first
    run executes the whole suite for real (no false green).
    """
    fingerprint = ";".join(
        f"{package}={version(package)}" for package in _TOOLCHAIN_PACKAGES
    )
    digest = hashlib.sha256(fingerprint.encode()).hexdigest()[:12]
    return f"toolchain-{digest}"


class FlextInfraPytestRunnerCommand(FlextInfraPytestRunnerBase):
    """Build the single supported pytest command family.

    One suite builder owns every flag; the testmon and coverage verbs are two
    selections over it (testmon 2.x refuses branch coverage through the cov
    plugin, so the two never share a process).
    """

    def ci_excluded_markers(self) -> t.StrTuple:
        """Use the same CI token as generated workflows and pre-commit hooks."""
        if self.ci_context:
            return config.Infra.tooling.tools.pytest.ci_excluded_markers
        return ()

    def _plugin_policy_args(self) -> t.VariadicTuple[str]:
        """Apply the same configured plugin contract to collection and execution."""
        pytest = config.Infra.tooling.tools.pytest
        # External-token gates (SSOT external-gate-markers) are deselected in
        # both the selection pass and the suite so xdist workers collect the
        # same set; direct invocation selects them outside this runner.
        return (
            "-p",
            pytest.enforcement_plugin,
            "-p",
            "no:metadata",
            "-o",
            f"{c.Infra.ASYNCIO_DEFAULT_FIXTURE_LOOP_SCOPE}={pytest.asyncio_default_fixture_loop_scope}",
            "-m",
            f"not ({' or '.join((*pytest.external_gate_markers, *self.ci_excluded_markers()))})",
        )

    def build_selection_command(
        self, *, complete: bool = False
    ) -> t.VariadicTuple[str]:
        """Resolve selection and register the collected inventory before workers.

        Every xdist worker otherwise resolves the selection itself, and two
        workers reading the database while a third writes it collect different
        sets, which xdist aborts with "Different tests were collected".
        The collection pass records testmon's unexecuted placeholders for new
        node IDs. Without those rows, worker startup can race with controller
        synchronization and reorder renamed or added tests differently. No
        test outcome or executed coverage is claimed by this pass.
        """
        return (
            sys.executable,
            "-m",
            "pytest",
            str(self.target),
            "--testmon",
            # Why: the external-gate deselection is a ``-m`` expression, and
            # testmon deactivates its selection whenever ``-m`` is present;
            # ``--testmon-forceselect`` is testmon's declared override for
            # exactly that case (never combined with ``--testmon-noselect``).
            *(("--testmon-noselect",) if complete else ("--testmon-forceselect",)),
            "--testmon-env",
            f"'{_toolchain_testmon_environment()}'",
            "--collect-only",
            "-q",
            *self._plugin_policy_args(),
            "-o",
            "addopts=--benchmark-disable --strict-markers --timeout=10",
            "-o",
            "filterwarnings=",
            "-p",
            "no:randomly",
            "-n",
            "0",
            "--no-cov",
        )

    def build_command(
        self,
        report_dir: Path,
        selected_node_ids: t.StrSequence | None = None,
        *,
        serialize: bool = False,
    ) -> t.VariadicTuple[str]:
        """Build the testmon suite argv (never the cov plugin)."""
        pytest = config.Infra.tooling.tools.pytest
        selection = selected_node_ids or None
        # Nothing selected means nothing to distribute across workers; a cold
        # cache serializes the seeding run so every worker would otherwise see
        # a different testmon set.
        workers = (
            "0"
            if serialize or selected_node_ids == ()
            else str(self.parallel_worker_budget(pytest))
        )
        return self._suite_argv(
            report_dir,
            targets=(tuple(selection) if selection else (str(self.target),)),
            workers=workers,
            trailing=(
                "--testmon",
                *(("--testmon-noselect",) if selection else ("--testmon-forceselect",)),
                "--testmon-env",
                f"'{_toolchain_testmon_environment()}'",
                *_NO_COVERAGE,
            ),
        )

    def build_coverage_command(
        self, report_dir: Path, *, serialize: bool = False
    ) -> t.VariadicTuple[str]:
        """Build the whole-suite coverage argv (never the testmon plugin).

        The measurement source is the declared package source directory — the
        same boundary every fleet coverage config declares — so imported
        third-party/Cython modules can never emit parse warnings.
        """
        pytest = config.Infra.tooling.tools.pytest
        workers = "0" if serialize else str(self.parallel_worker_budget(pytest))
        return self._suite_argv(
            report_dir,
            targets=(str(self.target),),
            workers=workers,
            trailing=(
                f"--cov={self.root / c.Infra.DEFAULT_SRC_DIR}",
                f"--cov-report=xml:{report_dir / 'coverage.xml'}",
                "--no-cov-on-fail",
            ),
        )

    def _suite_argv(
        self,
        report_dir: Path,
        *,
        targets: t.StrSequence,
        workers: str,
        trailing: t.StrSequence,
    ) -> t.VariadicTuple[str]:
        """Assemble one suite invocation; ``trailing`` owns the plugin split."""
        pytest = config.Infra.tooling.tools.pytest
        return (
            sys.executable,
            "-m",
            "pytest",
            *targets,
            *pytest.progress_args,
            *pytest.report_args,
            *self._plugin_policy_args(),
            f"--timeout={pytest.case_timeout_seconds}",
            f"--maxfail={pytest.max_failures}",
            f"--junitxml={report_dir / 'junit.xml'}",
            f"--report-log={report_dir / 'events.jsonl'}",
            *trailing,
            "-n",
            workers,
            "--dist",
            pytest.parallel_distribution,
            "--benchmark-disable",
        )


__all__: list[str] = ["FlextInfraPytestRunnerCommand"]
