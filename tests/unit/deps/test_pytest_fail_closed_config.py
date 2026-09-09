"""Fail-closed pytest configuration contract."""

from __future__ import annotations

import asyncio

import pytest
from flext_tests import tm

from flext_infra import config
from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from tests import u


class TestsFlextInfraPytestFailClosedConfig:
    """Prove canonical pytest settings replace local bypasses deterministically."""

    @pytest.mark.asyncio
    async def test_declared_async_provider_executes_coroutines(self) -> None:
        """Exercise the installed provider rather than merely registering a marker."""
        await asyncio.sleep(0)
        tm.that(asyncio.current_task() is not None, eq=True)

    def test_phase_replaces_stale_collection_and_warning_policy(self) -> None:
        """Replace ignored roots and warning filters without second-apply drift."""
        document = u.Tests.toml_doc(
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
        rendered = u.Cli.toml_dumps(document)

        tm.that(first_changes, empty=False)
        second_change_summary = "\n".join(second_changes)
        tm.that(second_change_summary, lacks="filterwarnings")
        tm.that(second_change_summary, lacks="testpaths")
        tm.that(
            rendered,
            has=(
                "filterwarnings = [\n"
                '    "error",\n'
                '    "module::flext_core._constants.enforcement.FlextMroViolation",\n'
                "]"
            ),
        )
        tm.that(rendered, has="testpaths = [")
        tm.that(
            rendered,
            has=(
                "asyncio_default_fixture_loop_scope = "
                f'"{config.Infra.tooling.tools.pytest.asyncio_default_fixture_loop_scope}"'
            ),
        )
        for test_path in config.Infra.tooling.tools.pytest.test_paths:
            tm.that(rendered, has=f'    "{test_path}",')
        for preserved_value in ("custom: stale local marker", "Spec*", "spec_*.py"):
            tm.that(rendered, has=preserved_value)
        for stale_value in (
            "--ignore-glob",
            "architecture",
            "guides",
            "ignore:legacy warning suppression",
            "--maxfail=1",
            "--cov=.",
        ):
            tm.that(rendered, lacks=stale_value)
        tm.that(rendered, has="--markdown-docs")
