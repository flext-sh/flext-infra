"""Runtime census selection and blocking behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import m, p, t

from flext_infra.gates.runtime_census import FlextInfraRuntimeCensusGate
from flext_infra.validate.runtime_census import FlextInfraRuntimeCensusValidator
from tests import c, r, tm, u

if TYPE_CHECKING:
    from collections.abc import Iterator


_MIXED_SOURCES: t.MappingKV[str, str] = {
    c.PYPROJECT_FILENAME: '[project]\nname = "fixturecensusmixed"\nversion = "0.1.0"\n',
    "src/fixturecensusmixed/__init__.py": (
        '"""Fixture package tripping several census rule families."""\n'
        "\n"
        "from typing import ClassVar\n"
        "\n"
        "\n"
        "class Plain:\n"
        '    """Missing the project class prefix."""\n'
        "\n"
        "\n"
        "class Holder:\n"
        '    """Missing prefix plus a constant outside _constants."""\n'
        "\n"
        '    LABEL: ClassVar[str] = "x"\n'
    ),
}
_GENUINE_SOURCES: t.MappingKV[str, str] = {
    c.PYPROJECT_FILENAME: (
        '[project]\nname = "fixturecensusgenuine"\nversion = "0.1.0"\n'
    ),
    "src/fixturecensusgenuine/__init__.py": (
        '"""Fixture package whose only census violation is a genuine rule."""\n'
        "\n"
        "from typing import ClassVar\n"
        "\n"
        "\n"
        "class FixturecensusgenuineHolder:\n"
        '    """Correctly prefixed class with a constant outside _constants."""\n'
        "\n"
        '    LABEL: ClassVar[str] = "x"\n'
    ),
}


def _write_project(root: Path, sources: t.MappingKV[str, str]) -> Path:
    """Materialize one fixture project and return its repository root.

    Returns:
        The resulting ``Path``.

    """
    for relative, text in sources.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def mixed_project(tmp_path: Path) -> Iterator[Path]:
    """Importable project tripping several census rule families at once.

    Yields:
        Each ``Path``.

    """
    root = _write_project(tmp_path / "mixed", _MIXED_SOURCES)
    yield from _importable_project(root)


@pytest.fixture
def broken_export_project(tmp_path: Path) -> Iterator[Path]:
    """Real lazy and eager import failures alongside an enforceable class.

    Yields:
        Each ``Path``.

    """
    sources = {
        c.PYPROJECT_FILENAME: (
            '[project]\nname = "fixturecensusbroken"\nversion = "0.1.0"\n'
        ),
        "src/fixturecensusbroken/__init__.py": (
            "def __dir__():\n"
            '    return ["BrokenExport"]\n'
            "\n"
            "def __getattr__(name):\n"
            "    try:\n"
            '        raise AttributeError("missing fixture adapter")\n'
            "    except AttributeError as exc:\n"
            '        raise ImportError("fixture lazy export failed") from exc\n'
        ),
        "src/fixturecensusbroken/broken.py": (
            'raise RuntimeError("fixture eager import failed")\n'
        ),
        "src/fixturecensusbroken/healthy.py": (
            "from typing import ClassVar\n"
            "\n"
            "class FixturecensusbrokenHolder:\n"
            '    """Correct prefix with a constant outside _constants."""\n'
            '    LABEL: ClassVar[str] = "x"\n'
        ),
    }
    root = _write_project(tmp_path / "broken", sources)
    yield from _importable_project(root)


@pytest.fixture
def genuine_project(tmp_path: Path) -> Iterator[Path]:
    """Importable project tripping exactly one genuine census rule.

    Yields:
        Each ``Path``.

    """
    root = _write_project(tmp_path / "genuine", _GENUINE_SOURCES)
    yield from _importable_project(root)


def _importable_project(root: Path) -> Iterator[Path]:
    """Expose one fixture ``src`` tree to the import system for the census.

    Yields:
        Each ``Path``.

    """
    src = str(root / "src")
    sys.path.insert(0, src)
    importlib.invalidate_caches()
    try:
        yield root
    finally:
        sys.path.remove(src)
        importlib.invalidate_caches()


class TestRuntimeCensusSelection:
    """Empty discovery is a broken invocation, not evidence of conformance."""

    @staticmethod
    @pytest.mark.parametrize("candidate", ["VALUE = 1\n", "class Plain: pass\n"])
    def test_sealed_census_does_not_import_cached_live_source(
        tmp_path: Path,
        candidate: str,
    ) -> None:
        """The existing isolated consumer reports the sealed candidate's rules."""
        root = u.Tests.git_repository(tmp_path / "sealed")
        _write_project(
            root,
            {
                c.PYPROJECT_FILENAME: (
                    '[project]\nname = "fixturecensussealed"\nversion = "0.1.0"\n'
                ),
                "src/fixturecensussealed/__init__.py": (
                    "def __dir__():\n    "
                    'raise RuntimeError("cached live census imported")\n'
                ),
            },
        )
        target = root / "src/fixturecensussealed/__init__.py"
        runtime_root = u.Infra.runtime_environment_dir(
            Path(__file__).resolve().parents[3]
        ).parent
        plan = tm.ok(FlextInfraStagedPackage.plan_sources(root, {target: candidate}))

        def consume(view: Path) -> p.Result[bool]:
            observed = FlextInfraCodegenTransaction.consume_source_runtime(
                plan,
                view,
                runtime_root,
                project_root=root,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            context = m.Infra.GateContext(
                repository_root=view,
                reports_dir=tmp_path / "reports",
                runtime_root=runtime_root,
                candidate_runtime_report=observed.value,
            )
            result = FlextInfraRuntimeCensusGate(repository_root=view).check(
                view, context
            )
            tm.that(result.result.passed, eq=observed.value.passed)
            tm.that(result.result.passed, eq=candidate == "VALUE = 1\n")
            return r[bool].ok(value=True)

        for _project in _importable_project(root):
            importlib.import_module("fixturecensussealed")
            tm.ok(FlextInfraStagedPackage.consume_sources(plan, consume))

    @staticmethod
    def test_sealed_gate_requires_observed_runtime_report(tmp_path: Path) -> None:
        """A missing native receipt cannot select live imports or imply success."""
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path,
            runtime_root=tmp_path,
        )
        result = FlextInfraRuntimeCensusGate(repository_root=tmp_path).check(
            tmp_path, context
        )
        tm.fail(result.result.passed)
        tm.that(
            " | ".join(result.result.errors),
            has="sealed runtime census report is required",
        )

    @staticmethod
    def test_empty_checkout_fails_the_gate(tmp_path: Path) -> None:
        """Test empty checkout fails the gate."""
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / ".reports",
        )
        gate = FlextInfraRuntimeCensusGate(repository_root=tmp_path)
        result = gate.check(tmp_path, context).result
        tm.fail(result.passed)
        tm.that(" | ".join(result.errors), has="no projects")


class TestsRuntimeCensusBlocking:
    """Every census violation blocks; no rule family is set aside."""

    @staticmethod
    def test_import_discovery_failures_remain_blocking_findings(
        broken_export_project: Path,
    ) -> None:
        """Preserve lazy causes and eager failures without losing later classes."""
        report = tm.ok(
            FlextInfraRuntimeCensusValidator(
                repository_root=broken_export_project,
            ).build_report(),
        )
        tm.fail(report.passed)
        violations = "\n".join(report.violations)
        tm.that(violations, has="fixturecensusbroken: Traceback")
        tm.that(violations, has="AttributeError: missing fixture adapter")
        tm.that(violations, has="ImportError: fixture lazy export failed")
        tm.that(violations, has="fixturecensusbroken.broken: Traceback")
        tm.that(violations, has="RuntimeError: fixture eager import failed")
        healthy_class = importlib.import_module(
            "fixturecensusbroken.healthy",
        ).FixturecensusbrokenHolder
        expected = tuple(
            (f"{violation.file_path}:" if violation.file_path else "")
            + (f"{violation.line_number}:" if violation.line_number else "")
            + healthy_class.__qualname__
            + (f" [{violation.rule_id}]" if violation.rule_id else "")
            + f": {violation.message}"
            for violation in u.check(healthy_class).violations
        )
        retained = tuple(
            violation
            for violation in report.violations
            if healthy_class.__qualname__ in violation
        )
        tm.that(retained, eq=expected)
        context = m.Infra.GateContext(
            repository_root=broken_export_project,
            reports_dir=broken_export_project / ".reports",
        )
        result = (
            FlextInfraRuntimeCensusGate(
                repository_root=broken_export_project,
            )
            .check(broken_export_project, context)
            .result
        )
        tm.fail(result.passed)
        tm.ok(len(result.errors) > 0)
        tm.that("\n".join(result.errors), has="missing fixture adapter")
        tm.that("\n".join(result.errors), has="fixture lazy export failed")

    @staticmethod
    def test_every_rule_family_in_the_project_blocks(
        mixed_project: Path,
        genuine_project: Path,
    ) -> None:
        """Prefix and constant violations belong to runtime census.

        The parameter-count smell belongs to the smell owner (qlty through
        make smells, flext-core ea8d16d26), so the census never reports it:
        each finding has exactly one gate.
        """
        mixed = tm.ok(
            FlextInfraRuntimeCensusValidator(
                repository_root=mixed_project,
            ).build_report(),
        )
        genuine = tm.ok(
            FlextInfraRuntimeCensusValidator(
                repository_root=genuine_project,
            ).build_report(),
        )
        tm.fail(mixed.passed)
        tm.that("\n".join(mixed.violations), has="[ENFORCE-079]")
        tm.that("\n".join(mixed.violations), has="[class_prefix]")
        tm.that("\n".join(mixed.violations), lacks="[smell_function_parameters]")
        tm.ok(len(mixed.violations) > len(genuine.violations))
        tm.that(
            mixed.summary,
            eq=f"runtime census found {len(mixed.violations)} violation(s)",
        )
        context = m.Infra.GateContext(
            repository_root=mixed_project,
            reports_dir=mixed_project / ".reports",
        )
        gate = FlextInfraRuntimeCensusGate(repository_root=mixed_project)
        result = gate.check(mixed_project, context).result
        tm.fail(result.passed)
        tm.that("\n".join(result.errors), has="[ENFORCE-079]")
        tm.that("\n".join(result.errors), has="[class_prefix]")

    @staticmethod
    def test_single_violation_reports_verbatim(
        genuine_project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """One genuine finding is one violation, reported exactly once."""
        report = tm.ok(
            FlextInfraRuntimeCensusValidator(
                repository_root=genuine_project,
            ).build_report(),
        )
        output = capsys.readouterr().out
        tm.fail(report.passed)
        tm.that(report.violations, length=1)
        tm.that("\n".join(report.violations), has="[ENFORCE-079]")
        tm.that(report.summary, eq="runtime census found 1 violation(s)")
        tm.that(output, eq="")
