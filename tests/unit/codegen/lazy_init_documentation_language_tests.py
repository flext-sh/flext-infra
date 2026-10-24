"""Project-local initializer presentation and guarded publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraLazyInitDocumentationLanguage:
    """Exercise declared locales through isolated real file plans."""

    @staticmethod
    def _assert_only_summary_changed(before: str, source: str) -> None:
        """Compare legal text, executable AST and every token except the docstring."""
        before_ast, after_ast = ast.parse(before), ast.parse(source)
        tm.that(
            tm.not_none(ast.get_docstring(after_ast)).partition("\n")[2],
            eq=tm.not_none(ast.get_docstring(before_ast)).partition("\n")[2],
        )
        before_ast.body.pop(0)
        after_ast.body.pop(0)
        tm.that(ast.dump(after_ast), eq=ast.dump(before_ast))
        tokens = [
            [
                (token.type, token.string)
                for token in tokenize.generate_tokens(io.StringIO(text).readline)
            ]
            for text in (before, source)
        ]
        for stream in tokens:
            stream.pop(
                next(
                    index
                    for index, token in enumerate(stream)
                    if token[0] == tokenize.STRING
                )
            )
        tm.that(tokens[0], eq=tokens[1])

    @staticmethod
    @pytest.mark.parametrize("bootstrap", [False, True])
    def test_project_locale_round_trip_changes_only_docstrings(
        tmp_path: Path, *, bootstrap: bool
    ) -> None:
        """Absent and explicit English stay identical across a Portuguese render."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            package_name=(
                c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE
                if bootstrap
                else "flext_test_project"
            ),
        )
        child = package / "nested"
        child.mkdir()
        (child / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        for directory in (package, child):
            (directory / "service.py").write_text(
                f"class Published{directory.name}: pass\n"
                f"__all__ = ['Published{directory.name}']\n",
                encoding=c.DEFAULT_ENCODING,
            )
        if bootstrap:
            package.joinpath("lazy.py").write_text(
                f"from {package.name}.nested.service import Publishednested\n",
                encoding=c.DEFAULT_ENCODING,
            )
        declaration = root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        declaration.parent.mkdir(exist_ok=True)
        service = u.Tests.create_lazy_init_service(root)
        baseline = tm.ok(service.plan_files())
        english = {
            file.path: tm.not_none(file.desired_content)
            for file in baseline
            if file.path in {package / c.Infra.INIT_PY, child / c.Infra.INIT_PY}
        }
        tm.that(len(english), eq=2)
        for language in (None, "en", "pt-BR", "en"):
            project = u.Tests.project_spec(root.name).model_dump(mode="json")
            if language is None:
                project.pop("documentation_language")
            else:
                project["documentation_language"] = language
            declaration.write_text(
                tm.ok(
                    u.Cli.json_dumps({
                        "Infra": {"codegen": {"repository": {"project": project}}}
                    })
                ),
                encoding=c.DEFAULT_ENCODING,
            )
            for file in tm.ok(service.plan_files()):
                if file.path not in english:
                    continue
                content = tm.not_none(file.desired_content)
                source = content.decode(c.DEFAULT_ENCODING)
                before = english[file.path].decode(c.DEFAULT_ENCODING)
                TestsFlextInfraLazyInitDocumentationLanguage._assert_only_summary_changed(
                    before, source
                )
                if language != "pt-BR":
                    tm.that(content, eq=english[file.path])
                else:
                    package_name = " ".join(
                        word.capitalize()
                        for word in file.path.parent
                        .relative_to(package.parent)
                        .as_posix()
                        .replace("/", ".")
                        .replace("_", " ")
                        .split()
                    )
                    tm.that(
                        tm.not_none(ast.get_docstring(ast.parse(source))).splitlines()[
                            0
                        ],
                        eq=c.Infra.DocumentationText.PACKAGE_DOCSTRING.localized(
                            "pt-BR"
                        ).format(package_name=package_name),
                    )
        tm.that((package / c.Infra.INIT_PY).read_bytes(), eq=b"")

    @staticmethod
    @pytest.mark.parametrize("invalid", ["yaml", "locale"])
    def test_invalid_declaration_fails_without_writes(
        tmp_path: Path, invalid: str
    ) -> None:
        """Malformed YAML and unsupported locales cannot publish initializers."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        (package / "service.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declaration = root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        declaration.parent.mkdir(exist_ok=True)
        project = u.Tests.project_spec(root.name).model_dump(mode="json")
        project["documentation_language"] = "fr"
        declaration.write_text(
            "[invalid"
            if invalid == "yaml"
            else tm.ok(
                u.Cli.json_dumps({
                    "Infra": {"codegen": {"repository": {"project": project}}}
                })
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        before = (package / c.Infra.INIT_PY).read_bytes()
        with pytest.raises(
            u.Yaml.YAMLError if invalid == "yaml" else c.ValidationError
        ):
            u.Tests.create_lazy_init_service(root).plan_files()
        tm.that((package / c.Infra.INIT_PY).read_bytes(), eq=before)

    @staticmethod
    @pytest.mark.parametrize("changed", [False, True])
    def test_publication_rejects_edited_destination_and_converges(
        tmp_path: Path, *, changed: bool
    ) -> None:
        """Reject a destination edited after planning; otherwise reach a fixed point."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        (package / "service.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declaration = root / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        declaration.parent.mkdir(exist_ok=True)
        project = u.Tests.project_spec(root.name).model_dump(mode="json")
        project["documentation_language"] = "pt-BR"
        declaration.write_text(
            tm.ok(
                u.Cli.json_dumps({
                    "Infra": {"codegen": {"repository": {"project": project}}}
                })
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        target = package / c.Infra.INIT_PY
        plans = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.ok(any(file.path == target for file in plans))
        if changed:
            edited = target.read_bytes() + b"# concurrent edit\n"
            target.write_bytes(edited)
            tm.fail(
                u.Infra.publish_codegen_plans(root, plans),
                has=f"atomic source changed: {target}",
            )
            tm.that(target.read_bytes(), eq=edited)
            return
        tm.ok(u.Infra.publish_codegen_plans(root, plans))
        second = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.fail(any(u.Infra.codegen_file_requires_effect(file) for file in second))
