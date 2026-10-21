"""Public docs publication settles authorial presentation metadata atomically.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flext_infra.docs.generator import FlextInfraDocGenerator
from tests import c, m, p, tm, u


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
            json.dumps({"Infra": {"codegen": {"repository": {"project": payload}}}}),
            encoding=c.DEFAULT_ENCODING,
        )

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path, FlextInfraDocGenerator]:
        """Create the existing real docs fixture and a project-only generator.

        Returns:
            The workspace, selected project and public generator.

        """
        workspace = u.Tests.create_docs_workspace(
            tmp_path, project_names=("flext-a", "flext-b")
        )
        generator = FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a", "flext-b"],
            include_root=False,
        )
        return workspace, workspace / "flext-a", generator

    @staticmethod
    def _unused_planner() -> p.RegisterableService:
        """Reject selecting an unrelated code-generation capability.

        Raises:
            AssertionError: Always, because docs must not select this factory.

        """
        msg = "documentation selected a Python generation factory"
        raise AssertionError(msg)

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

    def test_projection_source_race_prevents_metadata_and_document_publication(
        self, tmp_path: Path
    ) -> None:
        """A stale metadata plan cannot publish either participant of the batch."""
        _workspace, project, generator = self._workspace(tmp_path)
        self._declaration(project, "pt-BR")
        bundle = tm.ok(next(generator.prepare_batches()))
        tm.that(
            all(
                state.path.suffix in {".yaml", ".toml"}
                for plan in bundle.metadata_files
                for state in plan.source_states
            ),
            eq=True,
        )
        path = project / c.PYPROJECT_FILENAME
        concurrent = path.read_bytes() + b"\n# concurrent metadata edit\n"
        path.write_bytes(concurrent)
        readme = (project / "README.md").read_bytes()
        tm.fail(generator.publish_batch(bundle))
        tm.that(path.read_bytes(), eq=concurrent)
        tm.that((project / "README.md").read_bytes(), eq=readme)

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
