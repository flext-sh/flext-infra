"""Observable checkout-local Testmon database contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, infra, validate
from tests import c, t, tm, u


class TestsFlextInfraPytestRunnerDatabase:
    """Testmon keeps its native database file at the checkout root."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        "mode",
        [
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL,
            c.Infra.PytestExecutionMode.FULL,
            c.Infra.PytestExecutionMode.COVERAGE,
        ],
    )
    def test_database_is_the_native_checkout_default(
        tmp_path: Path,
        monkeypatch: t.Tests.MonkeyPatch,
        *,
        mode: c.Infra.PytestExecutionMode,
    ) -> None:
        """Both runner entrypoints elect the checkout database for Testmon modes.

        A redirected ``HOME`` or ``XDG_CACHE_HOME`` never moves it.
        """
        repository = tmp_path / "project"
        u.Tests.WorktreeFixture.initialize_governed_project(
            repository,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture_database",
                issue_prefix="fixture",
            ),
        )
        cache = config.Infra.codegen.make.testmon_cache
        (repository / cache.target_directory).mkdir(parents=True, exist_ok=True)
        context = tm.ok(infra.project_context(repository))
        expected = (
            repository / cache.database_filename if mode.records_testmon else None
        )
        redirected = tmp_path / "redirected-home"
        monkeypatch.setenv("HOME", str(redirected))
        monkeypatch.setenv("XDG_CACHE_HOME", str(redirected / "cache"))
        runner = validate.FlextInfraPytestRunner.from_project_context(
            context,
            started_at_monotonic=1.0,
            execution_mode=mode,
        )
        tm.that(runner.testmon_db, eq=expected)

        monkeypatch.setenv(c.Infra.PYTEST_ENV_REPOSITORY_ROOT, str(repository))
        monkeypatch.setenv(c.Infra.PYTEST_ENV_TARGET, str(cache.target_directory))
        monkeypatch.setenv(c.Infra.PYTEST_ENV_REPORTS, str(cache.reports_directory))
        monkeypatch.delenv(c.Infra.PYTEST_ENV_TARGET_FILE, raising=False)
        from_make = validate.FlextInfraPytestRunner.from_environment(
            started_at_monotonic=1.0,
            execution_mode=mode,
        )
        tm.that(from_make.testmon_db, eq=expected)

    @staticmethod
    @c.Tests.MARK.slow
    def test_testmon_uses_checkout_database_with_nested_pytest_root(
        cached_runner_project: Path,
        monkeypatch: t.Tests.MonkeyPatch,
    ) -> None:
        """Native selection and execution share the database the runner inspects."""
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        database = tm.not_none(runner.testmon_db)
        nested_root = cached_runner_project / runner.target
        (nested_root / "pytest.ini").write_text(
            "[pytest]\n", encoding=c.DEFAULT_ENCODING
        )
        variable = c.Infra.PYTEST_ENV_TESTMON_DATAFILE
        (nested_root / "conftest.py").write_text(
            f"import os\n\nassert os.environ[{variable!r}] == {str(database)!r}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (nested_root / "test_runtime.py").write_text(
            "from pathlib import Path\n\n"
            "def test_nested_root(pytestconfig):\n"
            "    assert pytestconfig.rootpath == Path(__file__).parent\n",
            encoding=c.DEFAULT_ENCODING,
        )
        inherited = cached_runner_project.parent / database.name
        monkeypatch.setenv(variable, str(inherited))

        tm.that(tm.ok(runner.execute()), eq=0)

        tm.that(database.is_file(), truth=True)
        tm.that((nested_root / database.name).exists(), truth=False)
        tm.that(inherited.exists(), truth=False)
