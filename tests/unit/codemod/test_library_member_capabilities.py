"""Domain capabilities are exempt from the library-named facade member ban.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, config, p, tm, u


class TestsFlextInfraCodemodLibraryMemberCapabilities:
    """A distribution the project itself names is a capability, not a leak."""

    IMPORTS = "import jinja2\nimport rope\nimport typing_extensions\n"

    @staticmethod
    def prefixes(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        subpackage: str | None = None,
        declared: str | None = None,
        tier_directory: str | None = None,
    ) -> tuple[str, ...]:
        """Return the library prefixes of a project importing three libraries.

        Returns:
            The normalized library prefixes the rule would ban.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owner = TestsFlextInfraCodemodLibraryMemberCapabilities
        (package / "consumer.py").write_text(owner.IMPORTS, encoding=c.DEFAULT_ENCODING)
        if subpackage is not None:
            (package / subpackage).mkdir()
            (package / subpackage / c.Infra.INIT_PY).write_text(
                "", encoding=c.DEFAULT_ENCODING
            )
        if tier_directory is not None:
            tier = repository / tier_directory
            tier.mkdir(parents=True)
            (tier / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        if declared is not None:
            directory = repository / "config"
            directory.mkdir(exist_ok=True)
            (directory / c.Infra.CODEGEN_CONFIG_FILENAME).write_text(
                "Infra:\n  codegen:\n    repository:\n"
                f"      domain_capabilities: [{declared}]\n",
                encoding=c.DEFAULT_ENCODING,
            )
        # Installed metadata is read from the target's own runtime, so the
        # fixture repository owns a provisioned environment.
        tm.ok(
            u.Tests.provision_scan_workspace(
                repository, session_runtime=session_runtime
            )
        )
        with u.Infra.codemod_workspace_snapshot(repository) as snapshot:
            return tuple(u.Infra.facade_library_prefixes(snapshot, repository))

    def test_undeclared_libraries_are_prefixes(
        self, tmp_path: Path, session_runtime: p.Tests.SessionRuntime
    ) -> None:
        """Neither an own package nor a declaration keeps the library prefixes."""
        found = self.prefixes(tmp_path, session_runtime)
        tm.that("jinja2" in found and "rope" in found, eq=True)

    def test_own_subpackage_is_a_capability(
        self, tmp_path: Path, session_runtime: p.Tests.SessionRuntime
    ) -> None:
        """An own subpackage named like a distribution exempts that prefix."""
        found = self.prefixes(tmp_path, session_runtime, subpackage="jinja2")
        tm.that("jinja2" in found, eq=False)
        tm.that("rope" in found, eq=True)

    def test_fixture_directory_is_not_a_capability(
        self, tmp_path: Path, session_runtime: p.Tests.SessionRuntime
    ) -> None:
        """A tests-tier directory named like a distribution exempts nothing."""
        found = self.prefixes(
            tmp_path, session_runtime, tier_directory="tests/fixtures/ci/jinja2"
        )
        tm.that("jinja2" in found, eq=True)

    def test_declared_capability_is_exempt(
        self, tmp_path: Path, session_runtime: p.Tests.SessionRuntime
    ) -> None:
        """A repository ``domain_capabilities`` name exempts that prefix."""
        found = self.prefixes(tmp_path, session_runtime, declared="Rope")
        tm.that("rope" in found, eq=False)
        tm.that("jinja2" in found, eq=True)

    def test_stdlib_backports_are_never_prefixes(
        self, tmp_path: Path, session_runtime: p.Tests.SessionRuntime
    ) -> None:
        """A declared stdlib backport is never a library prefix."""
        found = self.prefixes(tmp_path, session_runtime)
        for backport in config.Infra.tooling.lazy_init.stdlib_backports:
            tm.that(backport in found, eq=False)
