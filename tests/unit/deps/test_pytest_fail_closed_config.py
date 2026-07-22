"""Fail-closed pytest configuration contract."""

from __future__ import annotations

import tomlkit
from flext_tests import tm

from flext_infra import config
from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase


class TestsFlextInfraPytestFailClosedConfig:
    """Prove canonical pytest settings replace local bypasses deterministically."""

    def test_phase_replaces_stale_collection_and_warning_policy(self) -> None:
        """Replace ignored roots and warning filters without second-apply drift."""
        document = tomlkit.parse(
            """
[tool.pytest.ini_options]
addopts = ["--maxfail=1", "--cov=.", "--markdown-docs"]
filterwarnings = ["ignore:legacy warning suppression"]
markers = ["custom: stale local marker"]
python_classes = ["Spec*"]
python_files = ["spec_*.py"]
testpaths = ["architecture", "guides", "tests"]
"""
        )
        phase = FlextInfraEnsurePytestConfigPhase(config.Infra.tooling)

        first_changes = phase.apply(document)
        second_changes = phase.apply(document)
        rendered = tomlkit.dumps(document)

        tm.that(first_changes, empty=False)
        second_change_summary = "\n".join(second_changes)
        tm.that(second_change_summary, lacks="filterwarnings")
        tm.that(second_change_summary, lacks="testpaths")
        tm.that(
            rendered,
            has=(
                'filterwarnings = [\n'
                '    "error",\n'
                '    "module::flext_core._constants.enforcement.FlextMroViolation",\n'
                ']'
            ),
        )
        tm.that(rendered, has='testpaths = [\n    "tests",\n]')
        for preserved_value in ("custom: stale local marker", "Spec*", "spec_*.py"):
            tm.that(rendered, has=preserved_value)
        for stale_value in (
            "--ignore-glob",
            "architecture",
            "guides",
            "ignore:legacy warning suppression",
            "--maxfail=1",
            "--cov=.",
            "--markdown-docs",
        ):
            tm.that(rendered, lacks=stale_value)
