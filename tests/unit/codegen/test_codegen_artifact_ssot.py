"""Artifact projections validated against the typed production SSOT.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodegenArtifactSsot:
    """Property contracts that remain valid for arbitrary configured artifacts."""

    @staticmethod
    def test_testmon_policy_cannot_invent_missing_configuration() -> None:
        """The public boundary rejects absent policy instead of supplying one."""
        with u.Tests.raises(c.ValidationError):
            m.Infra.TestmonCachePolicySpec.model_validate({})

    @u.Tests.fixture(scope="module")
    @staticmethod
    def codegen() -> p.Infra.CodegenConfigSpec:
        """Return the production configuration consumed by every projection.

        Returns:
            The production configuration consumed by every projection.

        """
        return config.Infra.codegen

    @staticmethod
    def _linked_catalog(
        codegen: p.Infra.CodegenConfigSpec, *, cycle: bool
    ) -> t.JsonDict:
        """Link the first two production entries into a cycle or a dangling edge.

        Returns:
            The production catalog payload with the two linked entries.

        """
        payload = u.json_dict_adapter().validate_python(
            codegen.templates.model_dump(
                mode="json", by_alias=True, exclude_computed_fields=True
            )
        )
        entries = u.json_dict_adapter().validate_python(payload["entries"])
        first, second = sorted(entries)[:2]
        first_entry = u.json_dict_adapter().validate_python(entries[first])
        second_entry = u.json_dict_adapter().validate_python(entries[second])
        first_entry["requires_artifacts"] = [second]
        second_entry["requires_artifacts"] = (
            [first] if cycle else [f"{second}.undeclared"]
        )
        entries[first] = first_entry
        entries[second] = second_entry
        payload["entries"] = entries
        return payload

    @classmethod
    def test_undeclared_artifact_dependency_rejects_the_catalog(
        cls, codegen: p.Infra.CodegenConfigSpec
    ) -> None:
        """A dependency on an undeclared artifact fails while the catalog validates."""
        with u.Tests.raises(c.ValidationError, match="outside the graph:"):
            m.Infra.TemplatesSpec.model_validate(
                cls._linked_catalog(codegen, cycle=False)
            )

    @classmethod
    def test_cyclic_artifact_dependencies_fail_every_graph_query(
        cls, codegen: p.Infra.CodegenConfigSpec
    ) -> None:
        """A cycle fails the first order or closure query that generation runs."""
        catalog = m.Infra.TemplatesSpec.model_validate(
            cls._linked_catalog(codegen, cycle=True)
        )
        first = min(catalog.catalog)
        with u.Tests.raises(ValueError, match="cyclic dependency graph:"):
            _ = catalog.artifact_order
        with u.Tests.raises(ValueError, match="cyclic dependency graph:"):
            catalog.artifact_closure(frozenset({first}))

    @staticmethod
    def test_configuration_load_never_starts_the_graph_engine() -> None:
        """A fresh process validates the whole configuration without NetworkX."""
        loaded = tm.ok(
            u.Cli.capture([
                sys.executable,
                "-I",
                "-c",
                (
                    "import sys\n"
                    "from flext_infra import config\n"
                    "config.Infra.codegen.templates.entries\n"
                    "print('networkx' in sys.modules)"
                ),
            ])
        )
        tm.that(loaded, eq="False")

    @staticmethod
    def test_artifact_order_puts_every_dependency_first(
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Each artifact follows everything it requires, and closures stay closed."""
        templates = codegen.templates
        position = {name: index for index, name in enumerate(templates.artifact_order)}
        tm.that(set(position), eq=set(templates.catalog))
        for name, requirements in templates.artifact_requirements.items():
            tm.ok(
                all(
                    position[dependency] < position[name] for dependency in requirements
                )
            )
            closure = templates.artifact_closure(frozenset({name}))
            tm.ok(set(requirements) <= closure)

    @staticmethod
    def test_artifact_names_are_unique(codegen: p.Infra.CodegenConfigSpec) -> None:
        """Reject ambiguous projection keys at the typed owner."""
        names = tuple(artifact.name for artifact in codegen.artifacts)
        tm.ok(bool(names))
        tm.that(len(names), eq=len(set(names)))
        tm.ok(all(names))

    @staticmethod
    def test_template_entries_keep_every_declared_field(
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Each derived entry carries its declaration verbatim plus its key."""
        catalog = codegen.templates.catalog
        entries = codegen.templates.entries
        tm.that(len(entries), eq=len(catalog))
        for entry in entries:
            declaration = m.Infra.TemplateDeclarationSpec.model_validate(
                catalog[entry.destination]
            )
            for name in type(declaration).model_fields:
                tm.that(getattr(entry, name), eq=getattr(declaration, name))

    @staticmethod
    def test_vscode_maps_are_exact_projections(
        codegen: p.Infra.CodegenConfigSpec,
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
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Derive ignored source names from their owner flag only.

        Generated sources are owned Python and stay in native discovery.
        """
        expected = tuple(
            artifact.name
            for artifact in codegen.artifacts
            if artifact.source_scan_ignore
        )
        tm.that(codegen.source_scan_ignored, eq=expected)
        tm.that(len(expected), eq=len(set(expected)))

    @staticmethod
    def test_ignore_artifacts_are_exact_projection(
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Preserve configured order, then ignore the executor's state directory.

        Setup keeps the executor environment and its publication and lifecycle
        locks in one runtime state directory; none of it is source.
        """
        state = codegen.make.executor_environment.directory.parent.as_posix()
        expected = (
            *(
                f"{artifact.name}/" if artifact.is_dir else artifact.name
                for artifact in codegen.artifacts
                if artifact.gitignore and not artifact.generated_source
            ),
            f"/{state}/",
        )
        tm.that(codegen.gitignore_artifact_patterns, eq=expected)
        tm.that(len(expected), eq=len(set(expected)))

    @staticmethod
    @c.Tests.MARK.parametrize(
        "profile",
        [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE],
    )
    def test_generated_source_is_tracked_and_analyzed(
        codegen: p.Infra.CodegenConfigSpec,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """One generated_source key keeps a tree tracked and inside analysis.

        The flag owns tracked generation and the package initializer only;
        owned generated Python stays in native discovery and analysis.
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
            u.Infra.render_project_gitignore(
                declared,
                profile=profile,
                project_name="fixture-project",
            ),
        )

        tm.that(declared.generated_sources, has=name)
        tm.that(declared.source_scan_ignored, lacks=name)
        tm.that(declared.generated_source_globs, has=f"**/{name}/**")
        tm.that(declared.gitignore_artifact_patterns, lacks=f"{name}/")
        tm.that(
            u.Tests.is_tracked_under(rendered, f"src/fixture/{name}/wire_pb2.py"),
            eq=True,
        )

    @staticmethod
    def test_generated_source_must_be_a_directory() -> None:
        """A generated source names a package tree, never a single file."""
        with u.Tests.raises(c.ValidationError, match="must be a directory"):
            m.Infra.CodegenArtifactSpec(
                name="wire_pb2.py",
                is_dir=False,
                generated_source=True,
            )

    @staticmethod
    def test_ignore_sections_account_for_every_artifact(
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Require every derived pattern to be governed or appended."""
        emitted = {
            pattern
            for section in codegen.gitignore_sections
            for pattern in section.patterns
        }
        governed = {
            pattern.lstrip("!")
            for section in codegen.scaffold.gitignore_sections
            for pattern in section.patterns
        }
        unaccounted = tuple(
            pattern
            for pattern in codegen.gitignore_artifact_patterns
            if pattern not in emitted and pattern not in governed
        )
        tm.that(unaccounted, eq=())

    @staticmethod
    @c.Tests.MARK.parametrize(
        "profile",
        [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE],
    )
    def test_ignore_tracks_governed_provider_projections(
        codegen: p.Infra.CodegenConfigSpec,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Track portable governance and exclude machine-owned provider settings."""
        rendered = tm.ok(
            u.Infra.render_project_gitignore(
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
        codegen: p.Infra.CodegenConfigSpec,
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
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """The commit hook provisions then checks; pre-push adds the tests.

        Operator order 2026-11-12: the commit hook is (setup, check), so a fresh
        lane commits against its own locked toolchain; tests run on push.
        """
        workflow = codegen.make.workflow
        pre_commit = tuple(step for step in workflow if "pre_commit" in step.contexts)
        pre_push = tuple(step for step in workflow if "pre_push" in step.contexts)

        commit_verbs = tuple(step.verb for step in pre_commit)
        push_verbs = {step.verb for step in pre_push}
        tm.that(commit_verbs, eq=(c.Infra.VERB_SETUP, c.Infra.VERB_CHECK))
        tm.ok(c.Infra.VERB_CHECK in push_verbs)
        tm.ok(c.Infra.VERB_TEST in push_verbs)
        tm.ok(c.Infra.VERB_TEST not in commit_verbs)
        tm.that(
            push_verbs.issubset({verb.name for verb in codegen.make.verbs}),
            eq=True,
        )

    @staticmethod
    def test_rendered_vscode_document_consumes_projection_maps(
        tmp_path: Path,
        codegen: p.Infra.CodegenConfigSpec,
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
