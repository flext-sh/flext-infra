"""Public contract for CI static analysis and container source visibility.

Copyright (c) 2025 FLEXT Team. All rights reserved.
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

import shutil
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, tm, u
from tests.unit.codegen.ci_matrix_support import TestsFlextInfraCodegenCiMatrixSupport
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


@pytest.mark.slow
class TestsFlextInfraCodegenCiMatrixAnalysis(TestsFlextInfraCodegenCiMatrixSupport):
    """Prove static analysis and container source visibility contracts."""

    @staticmethod
    def _assert_sonarcloud_scope(rendered: str) -> None:
        """Assert one rendered .sonarcloud.properties against the codegen SSOT."""
        tests_dir = c.Infra.DIR_TESTS
        codegen = config.Infra.codegen
        entry = next(
            item
            for item in codegen.templates.entries
            if item.destination == c.Infra.SONARCLOUD_PROPERTIES_FILENAME
        )
        header = rendered.split("\n\n", 1)[0]
        tm.ok(header.startswith("# @flext-regenerate: make gen\n"))
        tm.that(header, has=tm.not_none(entry.source).as_posix())
        properties = {
            key: value
            for key, _, value in (
                line.partition("=")
                for line in rendered.splitlines()
                if line and not line.startswith("#")
            )
        }
        tm.that(properties["sonar.sources"], eq=".")
        # Main and test sets must be disjoint: sonar.exclusions narrows only
        # the main set, so the tests root that sonar.tests declares is excluded.
        tm.that(
            properties["sonar.exclusions"].split(","),
            eq=[
                *codegen.sonarcloud.exclusions,
                *codegen.generated_source_globs,
                f"{tests_dir}/**",
            ],
        )
        tm.that(
            properties["sonar.cpd.exclusions"].split(","),
            eq=list(codegen.sonarcloud.cpd_exclusions),
        )
        tm.that(properties["sonar.tests"], eq=tests_dir)
        tm.that(properties["sonar.test.inclusions"], has=tests_dir)
        tm.that(
            any(key.startswith("sonar.issue.ignore") for key in properties),
            eq=False,
        )
        comments = "\n".join(
            line for line in rendered.splitlines() if line.startswith("#")
        )
        for exclusion in codegen.sonarcloud.issue_exclusions:
            tm.that(comments, has=exclusion.rule_key)
            tm.that(comments, has=exclusion.resource_key)

    def test_sonarcloud_properties_projects_ssot_scope(
        self,
        rendered_project: Path,
    ) -> None:
        """A generated project carries the SSOT SonarCloud scope and its tests root."""
        root = rendered_project
        rendered = (root / c.Infra.SONARCLOUD_PROPERTIES_FILENAME).read_text(
            encoding="utf-8",
        )
        tm.ok((root / c.Infra.DIR_TESTS).is_dir())
        self._assert_sonarcloud_scope(rendered)

    def test_sonarcloud_tests_root_is_always_materialized_by_conform(
        self,
        infra_git_repo: Path,
    ) -> None:
        """sonar.tests always names a real directory, even from a checkout without one.

        Automatic analysis aborts when sonar.tests names an absent directory. The
        file declares tests/ unconditionally because conform itself projects the
        managed tests/ artifacts into every profile: starting from a
        provider-governed clone with no tests/, the plan still materializes them.
        """
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        u.Tests.write_standalone_workspace_manifest(root, config.Infra.name)
        # The seed ships a tests package; this case starts from a checkout without one.
        shutil.rmtree(root / c.Infra.DIR_TESTS)
        tm.fail((root / c.Infra.DIR_TESTS).exists())
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        plan = tm.ok(
            FlextInfraCodegenConform.Generate(repository_root=root).plan(request),
        )
        managed_tests_files = [
            item.path.as_posix()
            for item in config.Infra.codegen.managed_file_specs
            if item.path.parts[0] == c.Infra.DIR_TESTS
        ]
        tm.that(managed_tests_files, empty=False)
        for relative in managed_tests_files:
            tm.not_none(u.Tests.planned_text(plan, relative))
        rendered = tm.not_none(
            u.Tests.planned_text(plan, c.Infra.SONARCLOUD_PROPERTIES_FILENAME),
        )
        self._assert_sonarcloud_scope(rendered)

    @staticmethod
    def test_root_dockerignore_reincludes_bootstrap_surface() -> None:
        """Hand-maintained root .dockerignore admits clean-machine bootstrap files."""
        root = Path(__file__).resolve().parents[3]
        dockerignore = root / ".dockerignore"
        tm.ok(dockerignore.is_file())
        content = dockerignore.read_text(encoding="utf-8")
        for marker in (
            "!Makefile",
            "!*.mk",
            "!pyproject.toml",
            "!README.md",
            "!uv.lock",
            "!.mise.toml",
            "!mise.lock",
            "!bin/",
            "!bin/mise",
            "!bin/mise.cmd",
            "!.python-version",
            "!config/",
            "!scripts/dispatch.py",
            "!tests/fixtures/ci/docker/",
        ):
            tm.that(content, has=marker)


__all__: list[str] = ["TestsFlextInfraCodegenCiMatrixAnalysis"]
