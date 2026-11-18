"""Known scope names survive non-package roots without hiding invalid layouts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraLayoutScopeIngress:
    """Exercise layout admission with native filesystem and repository snapshots."""

    @staticmethod
    def test_empty_source_directory_is_an_absent_layout(tmp_path: Path) -> None:
        """The empty ``src`` a deleted package leaves is no source tree at all."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.PYPROJECT_FILENAME,
                '[project]\nname = "scope-consumer"\nversion = "1.0.0"\n'
                'dependencies = ["flext-core"]\n[tool.uv]\npackage = false\n',
            )
        )
        u.Tests.initialize_git_repo(tmp_path)
        tm.ok(u.Cli.ensure_dir(tmp_path / c.Infra.DEFAULT_SRC_DIR / "retired"))
        with u.Infra.workspace_snapshot(tmp_path, (tmp_path,)) as snapshot:
            scopes = u.Infra.codemod_layout_scopes(snapshot, tmp_path)
            tm.that(scopes[c.Infra.CODEMOD_COMPOSITION_ROOT_SCOPE], empty=True)
            tm.that(
                set(u.Infra.codemod_alias_utilities(snapshot, tmp_path)),
                eq={"local-alias", "runtime-alias"},
            )

    @staticmethod
    @c.Tests.MARK.parametrize("source_directory", [False, True])
    def test_nonpackage_root_preserves_scope_admission(
        tmp_path: Path, *, source_directory: bool
    ) -> None:
        """Absent source is supported; sources without a package stay red."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.PYPROJECT_FILENAME,
                '[project]\nname = "scope-consumer"\nversion = "1.0.0"\n'
                'dependencies = ["flext-core"]\n[tool.uv]\npackage = false\n',
            )
        )
        u.Tests.initialize_git_repo(tmp_path)
        if source_directory:
            tm.ok(u.Cli.ensure_dir(tmp_path / c.Infra.DEFAULT_SRC_DIR))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    tmp_path / c.Infra.DEFAULT_SRC_DIR / "stray.py", "VALUE = 1\n"
                )
            )
        with u.Infra.workspace_snapshot(tmp_path, (tmp_path,)) as snapshot:
            if source_directory:
                with u.Tests.raises(ValueError, match="project layout is unresolved"):
                    u.Infra.codemod_layout_scopes(snapshot, tmp_path)
                with u.Tests.raises(ValueError, match="project layout is unresolved"):
                    u.Infra.codemod_alias_utilities(snapshot, tmp_path)
                return
            scopes = u.Infra.codemod_layout_scopes(snapshot, tmp_path)
            utilities = u.Infra.native_utilities(
                snapshot, tmp_path, ("codemod_alias_utilities",)
            )
            tm.that(scopes[c.Infra.CODEMOD_COMPOSITION_ROOT_SCOPE], empty=True)
            with u.Tests.raises(ValueError, match="unknown file scope selectors"):
                u.Infra.codemod_scoped_document(
                    {
                        "id": "scope-consumer",
                        "language": "Python",
                        "rule": {"kind": "class_definition"},
                        "metadata": {"scope": {"in": ["unregistered-scope"]}},
                    },
                    scopes,
                    "scope-consumer",
                )
        catalog = tmp_path / "catalog"
        for identity, document in utilities.items():
            tm.ok(u.Cli.yaml_dump(catalog / "utils" / f"{identity}.yml", document))
        rule = catalog / "rules" / "probe.yml"
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        source = tmp_path / "consumer.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "from example import candidate\n"))
        for identity in (*utilities, "unregistered-alias"):
            tm.ok(
                u.Cli.yaml_dump(
                    rule,
                    {
                        "id": "probe",
                        "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                        "severity": "hint",
                        "rule": {"kind": "identifier", "matches": identity},
                    },
                )
            )
            outcome = u.Cli.capture([
                c.Infra.SG,
                "scan",
                "-c",
                str(catalog / "sgconfig.yml"),
                "--json=compact",
                str(source),
            ])
            if identity in utilities:
                tm.that(tm.ok(outcome), eq="[]")
            else:
                tm.fail(outcome, has="is not defined")
