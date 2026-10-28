"""Public docs publication settles authorial presentation metadata atomically.

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

from pathlib import Path
from typing import Never

import pytest

from flext_infra import FlextInfraCli, docs
from tests import c, m, tm, u


class TestsFlextInfraPresentationWorkflow:
    """Exercise real metadata preparation, docs rendering and guarded publication."""

    @staticmethod
    def _declaration(root: Path, language: str) -> None:
        """Write only the real local project declaration in an isolated fixture."""
        payload = u.Tests.project_spec(root.name).model_dump(
            mode="json", exclude_none=True
        )
        payload["documentation_language"] = language
        directory = root / "config"
        directory.mkdir(exist_ok=True)
        (directory / "codegen.yaml").write_text(
            tm.ok(
                u.Cli.json_dumps({
                    "Infra": {"codegen": {"repository": {"project": payload}}}
                })
            ),
            encoding=c.DEFAULT_ENCODING,
        )

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path, docs.FlextInfraDocGenerator]:
        """Create the existing real docs fixture and a project-only generator.

        Returns:
            The workspace, selected project and public generator.

        """
        workspace = u.Tests.create_docs_workspace(
            tmp_path, project_names=("flext-a", "flext-b")
        )
        generator = docs.FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a", "flext-b"],
            include_root=False,
        )
        return workspace, workspace / "flext-a", generator

    @staticmethod
    def _unused_planner() -> Never:
        """Reject selecting an unrelated code-generation capability."""
        msg = "documentation selected a Python generation factory"
        tm.reject(msg)

    @pytest.mark.parametrize("projection", [None, "en", "pt-BR"])
    def test_generate_projects_metadata_and_portuguese_docs_in_one_publication(
        self, tmp_path: Path, projection: str | None
    ) -> None:
        """Repair missing/stale metadata without full conformance or Python planning."""
        workspace, project, generator = self._workspace(tmp_path)
        self._declaration(project, "pt-BR")
        path = project / c.PYPROJECT_FILENAME
        document = tm.not_none(u.Cli.toml_parse_text(path.read_text()))
        docs = u.Cli.toml_ensure_path(document, ("tool", "flext", "docs"))
        docs["site_title"] = "Portal autoral"
        docs["exclude_docs"] = ["private/**"]
        if projection is not None:
            docs["documentation_language"] = projection
        path.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
        sibling = workspace / "flext-b" / c.PYPROJECT_FILENAME
        english_before = sibling.read_bytes()
        for name in ("initializer", "facade", "protocol", "dependency-planner"):
            generator.container.factory(name, self._unused_planner)
        request = m.Infra.DocsGenerateRequest(
            repository_root=workspace,
            projects=["flext-a", "flext-b"],
            include_root=False,
        )
        reports = tm.ok(generator.generate(request))
        metadata = u.Tests.toml_table_at(path.read_text(), "tool", "flext", "docs")
        tm.that(metadata["documentation_language"], eq="pt-BR")
        tm.that(metadata["site_title"], eq="Portal autoral")
        tm.that(metadata["exclude_docs"], eq=["private/**"])
        tm.that((project / "README.md").read_text(), has="## Finalidade")
        tm.that((project / "docs/index.md").read_text(), has="Comece aqui")
        tm.that(sibling.read_bytes(), eq=english_before)
        tm.that(
            any(item.path == str(path) for report in reports for item in report.items),
            eq=True,
        )
        project_report = next(report for report in reports if report.scope == "flext-a")
        metadata_item = next(
            item for item in project_report.items if item.path == str(path)
        )
        tm.that(metadata_item.written, eq=projection != "pt-BR")
        tm.that(
            project_report.changed_files,
            eq=sum(item.written for item in project_report.items),
        )
        first = path.read_bytes(), (project / "README.md").read_bytes()
        second = tm.ok(generator.generate(request))
        tm.that((path.read_bytes(), (project / "README.md").read_bytes()), eq=first)
        tm.that(sum(report.changed_files for report in second), eq=0)

    @pytest.mark.parametrize(
        "invalid", ["authorial", "projection", "namespace", "custom"]
    )
    @pytest.mark.parametrize("selected", ["flext-a", "flext-b"])
    def test_invalid_metadata_fails_before_any_selected_project_write(
        self, tmp_path: Path, invalid: str, selected: str
    ) -> None:
        """Reject unknown language and invalid Core fields before publication."""
        workspace, _project, generator = self._workspace(tmp_path)
        project = workspace / selected
        self._declaration(project, "fr" if invalid == "authorial" else "pt-BR")
        path = project / c.PYPROJECT_FILENAME
        if invalid != "authorial":
            document = tm.not_none(u.Cli.toml_parse_text(path.read_text()))
            if invalid in {"projection", "custom"}:
                docs = u.Cli.toml_ensure_path(document, ("tool", "flext", "docs"))
                if invalid == "projection":
                    docs["documentation_language"] = "fr"
                else:
                    docs["unknown_custom_field"] = True
            else:
                namespace = u.Cli.toml_ensure_path(
                    document, c.Infra.CONFORM_NAMESPACE_TABLE
                )
                namespace["unknown_owned_field"] = True
            path.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
        targets = tuple(
            workspace / name / filename
            for name in ("flext-a", "flext-b")
            for filename in (c.PYPROJECT_FILENAME, "README.md")
        )
        before = tuple(target.read_bytes() for target in targets)
        result = generator.generate(
            m.Infra.DocsGenerateRequest(
                repository_root=workspace,
                projects=["flext-a", "flext-b"],
                include_root=False,
            )
        )
        tm.fail(result)
        tm.that(tuple(target.read_bytes() for target in targets), eq=before)

    def test_render_failure_does_not_publish_prepared_metadata(
        self, tmp_path: Path
    ) -> None:
        """A source-render failure cannot leave a serial metadata side effect."""
        workspace, project, generator = self._workspace(tmp_path)
        self._declaration(project, "pt-BR")
        path = project / c.PYPROJECT_FILENAME
        readme = project / "README.md"
        before = path.read_bytes(), readme.read_bytes()
        (project / "src/flext_a/__init__.py").write_text(
            "def broken(\n", encoding=c.DEFAULT_ENCODING
        )
        result = generator.generate(
            m.Infra.DocsGenerateRequest(
                repository_root=workspace, projects=["flext-a"], include_root=False
            )
        )
        tm.fail(result)
        tm.that((path.read_bytes(), readme.read_bytes()), eq=before)

    def test_standalone_public_docs_settle_local_language_without_conformance(
        self, tmp_path: Path
    ) -> None:
        """Exercise the same standalone topology used by the Algar docs verb."""
        project = u.Tests.create_docs_workspace(tmp_path)
        package = project / "src/workspace"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            '"""Standalone documentation fixture."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        self._declaration(project, "pt-BR")
        generator = docs.FlextInfraDocGenerator(repository_root=project)
        request = m.Infra.DocsGenerateRequest(repository_root=project)
        reports = tm.ok(generator.generate(request))
        tm.that((project / "README.md").read_text(), has="## Finalidade")
        tm.that((project / "mkdocs.yml").read_text(), has="language: pt-BR")
        path = project / c.PYPROJECT_FILENAME
        tm.that(
            u.Tests.toml_table_at(path.read_text(), "tool", "flext", "docs")[
                "documentation_language"
            ],
            eq="pt-BR",
        )
        tm.that(
            any(item.written for report in reports for item in report.items), eq=True
        )
        tm.that(
            sum(report.changed_files for report in tm.ok(generator.generate(request))),
            eq=0,
        )

    def test_public_cli_json_includes_written_metadata_without_source_content(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The unchanged public route emits its committed typed report, not bool."""
        _workspace, project, _generator = self._workspace(tmp_path)
        self._declaration(project, "pt-BR")
        package = project / "src/flext_a/__init__.py"
        package.write_text(
            '"""private-source-sentinel-not-a-receipt"""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        capsys.readouterr()
        tm.that(
            FlextInfraCli.infra_main([
                "docs",
                "generate",
                "--repository-root",
                str(project),
            ]),
            eq=0,
        )
        captured = capsys.readouterr()
        payload = tm.ok(u.Cli.json_loads(captured.out))
        if not isinstance(payload, list):
            pytest.fail("docs generate must emit a JSON report collection")
        reports = tuple(
            m.Infra.DocsPhaseReport.model_validate(item) for item in payload
        )
        tm.that(
            any(
                item.path == str(project / c.PYPROJECT_FILENAME) and item.written
                for report in reports
                for item in report.items
            ),
            eq=True,
        )
        tm.that(captured.out, lacks="private-source-sentinel-not-a-receipt")
        tm.that(captured.out, lacks='"desired_content"')
        tm.that(captured.out, lacks='"source_states"')

    @pytest.mark.parametrize("entry", ["generate", c.ContextScope.REQUEST, "execute"])
    @pytest.mark.parametrize("failed_project", ["flext-a", "flext-b"])
    def test_terminal_failure_retains_only_preceding_committed_effects(
        self, tmp_path: Path, entry: str, failed_project: str
    ) -> None:
        """Keep terminal failure without promoting or rolling back another batch."""
        workspace, project, generator = self._workspace(tmp_path)
        for name in ("flext-a", "flext-b"):
            self._declaration(workspace / name, "pt-BR")
        failed = workspace / failed_project
        module = failed / "src" / failed_project.replace("-", "_") / "__init__.py"
        module.write_text(
            "def private_source_sentinel_not_a_receipt(\n", encoding=c.DEFAULT_ENCODING
        )
        untouched = {
            failed / c.PYPROJECT_FILENAME: (failed / c.PYPROJECT_FILENAME).read_bytes(),
            failed / "README.md": (failed / "README.md").read_bytes(),
        }
        request = m.Infra.DocsGenerateRequest(
            repository_root=workspace,
            projects=["flext-a", "flext-b"],
            include_root=False,
        )
        if entry == c.ContextScope.REQUEST:
            result = docs.FlextInfraDocGenerator.execute_request(request)
        elif entry == "execute":
            result = generator.execute()
        else:
            result = generator.generate(request)
        tm.fail(result)
        tm.that(isinstance(result.exception, SyntaxError), eq=True)
        tm.that(
            result.error,
            eq=(
                f"cannot render documentation source for {failed_project}: "
                f"{result.exception}"
            ),
        )
        data = tm.not_none(result.error_data)
        committed = data["committed_reports"]
        if not isinstance(committed, list):
            pytest.fail("failed generation must carry structured committed reports")
        tm.that(len(committed), eq=0 if failed_project == "flext-a" else 1)
        for payload in committed:
            report = m.Infra.DocsPhaseReport.model_validate(payload)
            tm.that(report.scope, eq="flext-a")
            tm.that(report.applied, eq=True)
            tm.that(report.passed, eq=True)
            tm.that(
                any(
                    item.path == str(project / c.PYPROJECT_FILENAME) and item.written
                    for item in report.items
                ),
                eq=True,
            )
        if failed_project == "flext-b":
            tm.that((project / "README.md").read_text(), has="## Finalidade")
            tm.that(
                u.Tests.toml_table_at(
                    (project / c.PYPROJECT_FILENAME).read_text(),
                    "tool",
                    "flext",
                    "docs",
                )["documentation_language"],
                eq="pt-BR",
            )
        for path, content in untouched.items():
            tm.that(path.read_bytes(), eq=content)
        encoded = tm.ok(u.Cli.json_dumps(dict(data)))
        tm.that(encoded, lacks="private_source_sentinel_not_a_receipt")
        tm.that(encoded, lacks='"desired_content"')
        tm.that(encoded, lacks='"source_states"')

    @pytest.mark.parametrize("entry", [c.ContextScope.REQUEST, "execute"])
    def test_service_success_retains_the_existing_report_collection(
        self, tmp_path: Path, entry: str
    ) -> None:
        """The model-valued service contract carries reports rather than status bool."""
        workspace, project, generator = self._workspace(tmp_path)
        self._declaration(project, "pt-BR")
        request = m.Infra.DocsGenerateRequest(
            repository_root=workspace,
            projects=["flext-a", "flext-b"],
            include_root=False,
        )
        result = (
            docs.FlextInfraDocGenerator.execute_request(request)
            if entry == c.ContextScope.REQUEST
            else generator.execute()
        )
        reports = tm.ok(result).root
        tm.that(tuple(report.scope for report in reports), eq=("flext-a", "flext-b"))
        tm.that(
            any(
                item.path == str(project / c.PYPROJECT_FILENAME) and item.written
                for report in reports
                for item in report.items
            ),
            eq=True,
        )
