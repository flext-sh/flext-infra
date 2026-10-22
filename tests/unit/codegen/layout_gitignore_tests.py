"""Tests for layout gitignore, tracked-file moves, and the canonical render.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, c, config, infra, m
from flext_infra.codegen.layout import FlextInfraCodegenLayout
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from tests import t, tm, u
from tests.unit.codegen.layout_fixture import (
    archive_root,
    build_loose_project,
    layout_engine,
)


class TestsFlextInfraCodegenLayoutGitignore:
    """Test suite for layout gitignore, tracked-file moves, and canonical render."""

    @staticmethod
    def _declare_layout_override(root: Path, project_name: str) -> None:
        """Declare the fixture's own policy through the production YAML boundary."""
        artifact = f"{project_name}.local.json"
        override = m.Infra.LayoutProjectOverrideSpec(
            archive_names=(artifact,),
            gitignore_additions=(artifact,),
        )
        _, declaration, _ = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        declaration.parent.mkdir(parents=True, exist_ok=True)
        payload: t.JsonMapping = {
            "Infra": {
                "codegen": {
                    "layout": {
                        "project_overrides": {
                            project_name: override.model_dump(mode="json"),
                        },
                    },
                },
            },
        }
        tm.ok(u.Cli.yaml_dump(declaration, payload))

    @classmethod
    def test_apply_adds_gitignore_entries_exactly_once(
        cls,
        tmp_path: Path,
    ) -> None:
        """Gitignore additions from the SSOT are appended once across applies."""
        project = build_loose_project(tmp_path)
        cls._declare_layout_override(project, project.name)
        codegen = tm.ok(u.Infra.load_codegen_inputs(project)).spec
        override = codegen.layout.project_overrides[project.name]
        artifact = project / override.archive_names[0]
        original = b'{"preserved": true}\n'
        artifact.write_bytes(original)
        tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "add", "--", artifact.name],
                cwd=project,
            ),
        )
        engine = layout_engine(tmp_path, apply_changes=True)

        first = engine.execute()
        tm.ok(first)
        second = engine.execute()
        tm.ok(second)

        gitignore = (project / c.Infra.GITIGNORE).read_text(encoding="utf-8")
        entries = gitignore.splitlines()
        for pattern in override.gitignore_additions:
            tm.that(entries.count(pattern), eq=1)
        tm.that(entries.count(f"{codegen.layout.archive_root}/"), eq=1)
        tm.that(
            (
                project / codegen.layout.archive_root / project.name / artifact.name
            ).read_bytes(),
            eq=original,
        )

    @staticmethod
    def test_apply_uses_git_mv_for_tracked_files(tmp_path: Path) -> None:
        """Tracked sources move through git so history follows the rename."""
        project = build_loose_project(tmp_path)
        engine = layout_engine(tmp_path, apply_changes=True)

        result = engine.execute()

        tm.ok(result)
        tracked = u.Cli.capture([c.Infra.GIT, "ls-files"], cwd=project)
        tm.ok(tracked)
        tracked_names = set(tracked.value.split())
        tm.ok("docs/guides/intro.md" in tracked_names)
        tm.fail("guides/intro.md" in tracked_names)
        tm.that(
            f"{archive_root()}/{project.name}/output.log" in tracked_names,
            eq=False,
        )

    @classmethod
    def test_managed_gitignore_render_includes_layout_additions(
        cls,
        tmp_path: Path,
    ) -> None:
        """The canonical gitignore render owns the layout SSOT additions."""
        project = build_loose_project(tmp_path)
        cls._declare_layout_override(project, project.name)
        codegen = tm.ok(u.Infra.load_codegen_inputs(project)).spec
        override = codegen.layout.project_overrides[project.name]
        rendered = u.Infra.render_project_gitignore(
            codegen,
            profile=c.Infra.MakeProfile.STANDALONE,
            project_name=project.name,
            project_dir=project,
        )

        entries = tm.ok(rendered).splitlines()
        for pattern in override.gitignore_additions:
            tm.that(entries.count(pattern), eq=1)
        tm.that(entries.count(f"{codegen.layout.archive_root}/"), eq=1)

    @staticmethod
    def test_rendered_gitignore_keeps_backup_named_python_sources(
        tmp_path: Path,
    ) -> None:
        """A backup module is source code even when its name contains backup."""
        rendered = u.Infra.render_project_gitignore(
            config.Infra.codegen,
            profile=c.Infra.MakeProfile.STANDALONE,
            project_name="flext-cli",
        )
        tm.ok(rendered)
        (tmp_path / ".gitignore").write_text(rendered.value, encoding="utf-8")
        tm.ok(u.Cli.capture([c.Infra.GIT, "init"], cwd=tmp_path))
        source = tmp_path / "src" / "dc_backup" / "workspace_backup_request.py"
        source.parent.mkdir(parents=True)
        source.write_text("pass\n", encoding="utf-8")
        tracked = u.Cli.capture(
            [c.Infra.GIT, "check-ignore", str(source.relative_to(tmp_path))],
            cwd=tmp_path,
        )
        tm.ok(tracked.failure)

    @classmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("directory_suffix", ["", "-lane"])
    def test_rendered_gitignore_satisfies_layout_additions(
        cls,
        tmp_path: Path,
        directory_suffix: str,
    ) -> None:
        """The public gitignore renderer satisfies the layout consumer.

        The planner used to render ``base/gitignore.j2`` from its own section list
        without the layout override, so ``make gen`` never satisfied the layout gate
        and a governed member ended up hand-editing the projection. One owner now
        derives the sections for every renderer: after conform, the layout engine
        finds no missing gitignore pattern for a project declared in the SSOT.

        The override is keyed by the declared ``[project].name``, never by the
        checkout directory: a linked worktree named after its lane renders the same
        additions (conform used ``repository_root.name`` and dropped them there).
        """
        repository = u.Tests.repository_ref(config.Infra.name)
        owner = f"{repository.name}-layout-consumer"
        root = tmp_path / f"{owner}{directory_suffix}"
        cls._declare_layout_override(root, owner)
        codegen = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        override = codegen.layout.project_overrides[owner]
        project = u.Tests.project_spec(config.Infra.name)
        tm.ok(
            infra.codegen_new(
                FlextInfraCodegenProjectNew(
                    repository_root=Path.cwd(),
                    flext_source=u.Tests.flext_source(),
                    name=owner,
                    kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                    output_root=root,
                    provider=repository.provider,
                    repository_url=(
                        f"{repository.url.rsplit('/', maxsplit=1)[0]}/{owner}.git"
                    ),
                    repository_branch=u.Tests.provider_branch(),
                    flext_repository_url=u.Tests.repository_ref(config.Infra.name).url,
                    flext_repository_ref=u.Tests.provider_branch(),
                    license=project.license,
                    author_name=project.author_name,
                    author_email=project.author_email,
                    upstream=project.upstream,
                    year=project.year,
                    apply_changes=True,
                ),
            ),
        )
        entries = (root / c.Infra.GITIGNORE).read_text(encoding="utf-8").splitlines()
        missing = tuple(
            pattern
            for pattern in override.gitignore_additions
            if entries.count(pattern) != 1
        )
        tm.that(missing, eq=())
        report = FlextInfraCodegenLayout(repository_root=root).check_project(root)
        tm.that(report.project, eq=owner)
        tm.that(
            tuple(
                finding for finding in report.findings if finding.rule == "gitignore"
            ),
            eq=(),
        )

    @staticmethod
    def test_layout_preserves_tracked_ignored_files_and_ignores_local_artifacts(
        tmp_path: Path,
    ) -> None:
        """Local ignored files are not layout inputs; tracked files stay."""
        project = build_loose_project(tmp_path)
        local = project / "local-artifact"
        tracked = project / "tracked-artifact"
        local.write_text("local\n", encoding="utf-8")
        tracked.write_text("tracked\n", encoding="utf-8")
        ignore = project / c.Infra.GITIGNORE
        content = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
        ignore.write_text(
            f"{content}\n{local.name}\n{tracked.name}\n",
            encoding="utf-8",
        )
        tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "add", "--force", "--", tracked.name],
                cwd=project,
            ),
        )

        report = layout_engine(tmp_path, apply_changes=False).plan_project(project)

        paths = {finding.path for finding in report.findings}
        tm.fail(local.name in paths)
        tm.ok(tracked.name in paths)
