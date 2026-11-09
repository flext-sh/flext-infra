"""Native governance classification follows project facts, without declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, infra, m, t, tm, u


class TestsFlextInfraDetectedProjectKind:
    """Exercise the public configuration boundary against real project inputs."""

    @staticmethod
    def test_dependency_change_updates_kind_without_yaml_changes(
        tmp_path: Path,
    ) -> None:
        """A YAML memo cannot freeze facts owned by native package metadata."""
        u.Tests.write_native_resolution_project(tmp_path, "ordinary-project")
        before = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        tm.that(before.kind, eq=c.Infra.ProjectKind.INTERNAL)
        u.Tests.write_native_resolution_project(
            tmp_path, "ordinary-project", dependencies=(c.Infra.PKG_CORE,)
        )
        after = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        tm.that(after.kind, eq=c.Infra.ProjectKind.INTERNAL_FLEXT)
        tm.that(after.sources, eq=before.sources)

    @staticmethod
    def test_native_imports_identify_a_flext_consumer(tmp_path: Path) -> None:
        """Native source imports establish consumption independently of metadata."""
        u.Tests.write_native_resolution_project(tmp_path, "import-consumer")
        source = tmp_path / "src" / "import_consumer" / "__init__.py"
        source.write_text("from flext_core import m\n", encoding=c.DEFAULT_ENCODING)
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.INTERNAL_FLEXT,
        )

    @staticmethod
    def test_composition_uses_child_dependency_facts(tmp_path: Path) -> None:
        """An ordinary workspace is governed when its composed child uses FLEXT."""
        u.Tests.write_native_resolution_project(tmp_path, "ordinary-workspace")
        child = tmp_path / "member"
        u.Tests.write_native_resolution_project(
            child, "member", dependencies=(c.Infra.PKG_CORE,)
        )
        (tmp_path / c.Infra.GITMODULES).write_text(
            '[submodule "member"]\n'
            "\tpath = member\n"
            "\turl = https://github.example/owner/member.git\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.INTERNAL_FLEXT,
        )

    @staticmethod
    def test_distinct_native_upstream_preserves_fork_governance(tmp_path: Path) -> None:
        """A third-party fork is proven by its actual native upstream identity."""
        u.Tests.write_native_resolution_project(tmp_path, "upstream-project")
        u.Tests.git_bootstrap(tmp_path, ("init",))
        for name, owner in (("origin", "consumer"), ("upstream", "upstream")):
            u.Tests.git_bootstrap(
                tmp_path,
                ("remote", "add", name, f"https://github.example/{owner}/project.git"),
            )
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.THIRD_PARTY_FORK,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("kind", tuple(c.Infra.ProjectKind))
    @c.Tests.MARK.parametrize("policy_key", ["kind", "unrelated_invalid"])
    def test_write_containment_retains_native_kind_and_strict_policy_loading(
        tmp_path: Path,
        kind: c.Infra.ProjectKind,
        policy_key: str,
    ) -> None:
        """Native authority survives an obsolete key; policy reads reject it."""
        root = tmp_path / "project"
        dependencies = (
            (c.Infra.PKG_CORE,) if kind is c.Infra.ProjectKind.INTERNAL_FLEXT else ()
        )
        u.Tests.write_native_resolution_project(
            root, "admission-project", dependencies=dependencies
        )
        if kind is c.Infra.ProjectKind.THIRD_PARTY_FORK:
            u.Tests.git_bootstrap(root, ("init",))
            for name, owner in (("origin", "consumer"), ("upstream", "upstream")):
                u.Tests.git_bootstrap(
                    root,
                    (
                        "remote",
                        "add",
                        name,
                        f"https://github.example/{owner}/project.git",
                    ),
                )
        target = root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        for obsolete in (False, True):
            if obsolete:
                tm.ok(
                    u.Cli.yaml_dump(
                        target,
                        {
                            "Infra": {
                                "codegen": {"repository": {policy_key: kind.value}}
                            }
                        },
                    ),
                )
            tm.that(u.Infra.detected_project_kind(root), eq=kind)
            ordinary = u.Infra.load_codegen_inputs(root)
            with infra.rope_workspace(root) as workspace:
                tm.that(
                    u.Infra.detected_project_kind(
                        root, source_project=workspace.rope_project
                    ),
                    eq=kind,
                )
                captured = u.Infra.load_codegen_inputs(
                    root, source_project=workspace.rope_project
                )
                if obsolete:
                    tm.fail(ordinary, has=f"repository.{policy_key}")
                    tm.fail(captured, has=f"repository.{policy_key}")
                else:
                    tm.that(tm.ok(ordinary).kind, eq=kind)
                    tm.that(tm.ok(captured).kind, eq=kind)
        if kind is c.Infra.ProjectKind.THIRD_PARTY_FORK:
            with u.Tests.raises(ValueError, match="third-party fork"):
                u.Infra.contained_write_targets(root, (target,), authority=root)
            return
        tm.that(
            u.Infra.contained_write_targets(root, (target,), authority=root),
            eq=(target.resolve(),),
        )
        foreign = tmp_path / "different-authority"
        if kind is c.Infra.ProjectKind.INTERNAL:
            with u.Tests.raises(ValueError, match="outside the selected root"):
                u.Infra.contained_write_targets(root, (target,), authority=foreign)
        else:
            tm.that(
                u.Infra.contained_write_targets(root, (target,), authority=foreign),
                eq=(target.resolve(),),
            )
        outside = tmp_path / "outside.yaml"
        outside.write_text("external\n", encoding=c.DEFAULT_ENCODING)
        alias = root / "escape.yaml"
        alias.symlink_to(outside)
        with u.Tests.raises(ValueError, match="escapes its declared project root"):
            u.Infra.contained_write_targets(root, (alias,), authority=root)
        tm.that(outside.read_text(encoding=c.DEFAULT_ENCODING), eq="external\n")

    @staticmethod
    def test_native_text_retirement_publishes_once_and_preserves_other_fields(
        tmp_path: Path,
    ) -> None:
        """The public migration removes only kind and its repeat writes nothing."""
        u.Tests.write_native_resolution_project(
            tmp_path, "kind-migration", dependencies=(c.Infra.PKG_CORE,)
        )
        u.Tests.git_bootstrap(tmp_path, ("init",))
        path = tmp_path / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        integration: t.JsonDict = {"provider": "local", "branch": "integration"}
        document: t.JsonDict = {
            "Infra": {
                "codegen": {
                    "repository": {
                        "kind": c.Infra.ProjectKind.INTERNAL_FLEXT.value,
                        "integration": integration,
                    }
                }
            },
            "Unrelated": {"retained": "foreign declaration"},
        }
        tm.ok(u.Cli.yaml_dump(path, document))
        request = m.Infra.ModTextCommand(
            repository_root=tmp_path,
            apply=True,
            rule_ids=("retire-repository-kind-declaration",),
        )
        tm.ok(infra.mod_text(request))
        tm.that(
            tm.ok(u.Cli.yaml_safe_load(path)),
            eq={
                "Infra": {"codegen": {"repository": {"integration": integration}}},
                "Unrelated": {"retained": "foreign declaration"},
            },
        )
        tm.that(
            tm.ok(u.Infra.load_codegen_inputs(tmp_path)).kind,
            eq=c.Infra.ProjectKind.INTERNAL_FLEXT,
        )
        before, content = path.stat(), path.read_bytes()
        tm.ok(infra.mod_text(request))
        after = path.stat()
        tm.that(path.read_bytes(), eq=content)
        tm.that(
            (after.st_ino, after.st_mtime_ns),
            eq=(before.st_ino, before.st_mtime_ns),
        )
