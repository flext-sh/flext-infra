"""Artifact projections validated against the typed production SSOT.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, tm, u


class TestsFlextInfraCodegenArtifactSsot:
    """Property contracts that remain valid for arbitrary configured artifacts."""

    @staticmethod
    def test_testmon_policy_cannot_invent_missing_configuration() -> None:
        """The public boundary rejects absent policy instead of supplying one."""
        with pytest.raises(c.ValidationError):
            m.Infra.TestmonCachePolicySpec.model_validate({})

    @staticmethod
    @pytest.fixture(scope="module")
    def codegen() -> m.Infra.CodegenConfigSpec:
        """Return the production configuration consumed by every projection.

        Returns:
            The production configuration consumed by every projection.

        """
        return config.Infra.codegen

    @staticmethod
    @pytest.mark.parametrize(
        ("dependencies", "error"),
        [
            pytest.param("cycle", "cyclic dependency graph:", id="cycle"),
            pytest.param("unknown", "outside the graph:", id="unknown"),
        ],
    )
    def test_template_artifact_dependencies_form_a_closed_dag(
        codegen: m.Infra.CodegenConfigSpec,
        dependencies: str,
        error: str,
    ) -> None:
        """A cyclic or undeclared artifact dependency rejects the catalog."""
        payload = codegen.templates.model_dump(
            mode="json", by_alias=True, exclude_computed_fields=True
        )
        first, second = sorted(payload["entries"])[:2]
        payload["entries"][first]["requires_artifacts"] = [second]
        payload["entries"][second]["requires_artifacts"] = (
            [first] if dependencies == "cycle" else [f"{second}.undeclared"]
        )
        with pytest.raises(c.ValidationError, match=error):
            m.Infra.TemplatesSpec.model_validate(payload)

    @staticmethod
    def test_artifact_names_are_unique(codegen: m.Infra.CodegenConfigSpec) -> None:
        """Reject ambiguous projection keys at the typed owner."""
        names = tuple(artifact.name for artifact in codegen.artifacts)
        tm.ok(bool(names))
        tm.that(len(names), eq=len(set(names)))
        tm.ok(all(names))

    @staticmethod
    def test_template_entries_keep_every_declared_field(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Each derived entry carries its declaration verbatim plus its key."""
        catalog = codegen.templates.catalog
        entries = codegen.templates.entries
        tm.that(len(entries), eq=len(catalog))
        for entry in entries:
            declaration = catalog[entry.destination]
            for name in type(declaration).model_fields:
                tm.that(getattr(entry, name), eq=getattr(declaration, name))

    @staticmethod
    def test_vscode_maps_are_exact_projections(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Derive every expected mapping from the same typed artifact records."""
        expected_files = {
            f"**/{artifact.name}": True
            for artifact in codegen.artifacts
            if artifact.vscode_exclude
        }
        expected_watchers = {
            (
                f"**/{artifact.name}/**" if artifact.is_dir else f"**/{artifact.name}"
            ): True
            for artifact in codegen.artifacts
            if artifact.watch_exclude
        }
        tm.that(dict(codegen.vscode_files_exclude_map), eq=expected_files)
        tm.that(dict(codegen.vscode_search_exclude_map), eq=expected_files)
        tm.that(dict(codegen.vscode_watcher_exclude_map), eq=expected_watchers)

    @staticmethod
    def test_source_scan_is_exact_projection(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Derive ignored source names from their owner flags."""
        expected = tuple(
            artifact.name
            for artifact in codegen.artifacts
            if artifact.source_scan_ignore or artifact.generated_source
        )
        tm.that(codegen.source_scan_ignored, eq=expected)
        tm.that(len(expected), eq=len(set(expected)))

    @staticmethod
    def test_ignore_artifacts_are_exact_projection(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Preserve configured order while rendering directory suffixes."""
        expected = tuple(
            f"{artifact.name}/" if artifact.is_dir else artifact.name
            for artifact in codegen.artifacts
            if artifact.ignore and not artifact.generated_source
        )
        tm.that(codegen.ignore_artifact_patterns, eq=expected)
        tm.that(len(expected), eq=len(set(expected)))

    @staticmethod
    @pytest.mark.parametrize(
        "profile",
        [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE],
    )
    def test_generated_source_is_tracked_and_excluded_from_analysis(
        codegen: m.Infra.CodegenConfigSpec,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """One generated_source key keeps a tree tracked yet outside analysis.

        Premise (flext-gknfx): a generated tree that ``.ignore`` hides while
        Git tracks it loses every module a regeneration adds, and analyzers
        that ignore ``.ignore`` still check it. The key must therefore keep
        the tree trackable while every scan and analyzer exclusion derives it.
        """
        name = "wire_contracts"
        declared = codegen.model_copy(
            update={
                "artifacts": (
                    *codegen.artifacts,
                    m.Infra.CodegenArtifactSpec(name=name, generated_source=True),
                ),
            },
        )
        rendered = tm.ok(
            u.Infra.render_project_ignore(
                declared,
                profile=profile,
                project_name="fixture-project",
            ),
        )

        tm.that(declared.generated_sources, has=name)
        tm.that(declared.source_scan_ignored, has=name)
        tm.that(declared.generated_source_globs, has=f"**/{name}/**")
        tm.that(declared.ignore_artifact_patterns, lacks=f"{name}/")
        tm.that(
            u.Tests.is_tracked_under(rendered, f"src/fixture/{name}/wire_pb2.py"),
            eq=True,
        )

    @staticmethod
    def test_generated_source_must_be_a_directory() -> None:
        """A generated source names a package tree, never a single file."""
        with pytest.raises(c.ValidationError, match="must be a directory"):
            m.Infra.CodegenArtifactSpec(
                name="wire_pb2.py",
                is_dir=False,
                generated_source=True,
            )

    @staticmethod
    def test_ignore_sections_account_for_every_artifact(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Require every derived pattern to be governed or appended."""
        emitted = {
            pattern
            for section in codegen.ignore_sections
            for pattern in section.patterns
        }
        governed = {
            pattern.lstrip("!")
            for section in codegen.scaffold.ignore_sections
            for pattern in section.patterns
        }
        unaccounted = tuple(
            pattern
            for pattern in codegen.ignore_artifact_patterns
            if pattern not in emitted and pattern not in governed
        )
        tm.that(unaccounted, eq=())

    @staticmethod
    @pytest.mark.parametrize(
        "profile",
        [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE],
    )
    def test_ignore_tracks_governed_provider_projections(
        codegen: m.Infra.CodegenConfigSpec,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Track portable governance and exclude machine-owned provider settings."""
        rendered = tm.ok(
            u.Infra.render_project_ignore(
                codegen,
                profile=profile,
                project_name="fixture-project",
            ),
        )
        tracked = (
            ".agents/projection.json",
            ".agents/aihub-hooks/antigravity-preinvocation.py",
            ".agents/skills/flext-development/SKILL.md",
            ".claude/settings.json",
            ".claude/skills/flext-development/SKILL.md",
            ".codex/hooks.json",
            ".cursor/hooks.json",
            ".github/skills/flext-development/SKILL.md",
            ".gemini/settings.json",
            ".opencode/skills/flext-development/SKILL.md",
        )
        for relative_path in tracked:
            tm.that(
                u.Tests.is_tracked_under(rendered, relative_path),
                eq=True,
                msg=f"{profile.value}: {relative_path} must be trackable",
            )
        for relative_path in (".claude/settings.local.json",):
            tm.that(
                u.Tests.is_tracked_under(rendered, relative_path),
                eq=False,
                msg=f"{profile.value}: {relative_path} is machine-owned runtime state",
            )
        tm.that(
            u.Tests.is_tracked_under(
                rendered,
                ".agents/skills/flext-development/report.json",
            ),
            eq=False,
        )

    @staticmethod
    def test_makefile_has_one_owner_for_every_declared_profile(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Cover repository profiles through one generic template entry."""
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(entries, len=1)
        declared_profiles = {
            c.Infra.MakeProfile.WORKSPACE,
            c.Infra.MakeProfile.STANDALONE,
        }
        tm.that(set(entries[0].profiles), eq=declared_profiles)

    @staticmethod
    def test_hook_workflow_contexts_partition_mutation_and_validation(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Both hooks run incremental tests; pre-push adds full local checks."""
        workflow = codegen.make.workflow
        pre_commit = tuple(step for step in workflow if "pre_commit" in step.contexts)
        pre_push = tuple(step for step in workflow if "pre_push" in step.contexts)

        tm.ok(bool(pre_commit))
        tm.ok(bool(pre_push))
        commit_verbs = {step.verb for step in pre_commit}
        push_verbs = {step.verb for step in pre_push}
        tm.ok(bool(commit_verbs & push_verbs))
        tm.ok(commit_verbs < push_verbs)
        tm.ok(c.Infra.VERB_TEST in commit_verbs)
        tm.ok("test" in push_verbs)
        shared_steps = tuple(
            step
            for step in workflow
            if {"pre_commit", "pre_push"}.issubset(step.contexts)
        )

        # `apply` carries the declared mutation token, which every effecting
        # verb requires — `check` and `test` publish reports and require it too.
        # It is therefore not a classification of source rewriting, and a shared
        # step legitimately carries it. What the partition must prove is that
        # each hook owns work the other does not, and that both reach the same
        # validation verb.
        tm.ok(bool(shared_steps))
        tm.that(
            {step.verb for step in shared_steps}.issubset(commit_verbs & push_verbs),
            eq=True,
        )
        tm.ok(bool(push_verbs - commit_verbs))
        tm.that(
            push_verbs.issubset({verb.name for verb in codegen.make.verbs}),
            eq=True,
        )

    @staticmethod
    def test_rendered_vscode_document_consumes_projection_maps(
        tmp_path: Path,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Validate the public renderer output instead of private implementation."""
        project = u.Tests.mk_project(
            tmp_path,
            "artifact-ssot",
            pyproject='[project]\nname = "artifact-ssot"\nversion = "0.1.0"\n',
            with_src=True,
        )
        u.Tests.write_project_beads_config(project, "artifact-ssot")
        u.Tests.initialize_git_repo(
            project,
            origin_url=u.Tests.repository_ref("artifact-ssot").url,
        )
        rendered: str = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(project)
        )
        settings = u.Cli.JSON_MAPPING_ADAPTER.validate_json(rendered)
        tm.that(settings["files.exclude"], eq=dict(codegen.vscode_files_exclude_map))
        tm.that(settings["search.exclude"], eq=dict(codegen.vscode_search_exclude_map))
        tm.that(
            settings["files.watcherExclude"],
            eq=dict(codegen.vscode_watcher_exclude_map),
        )
