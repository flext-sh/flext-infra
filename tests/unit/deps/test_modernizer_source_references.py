"""Migrate explicit Git refs through the public modernizer without changing sources."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import main
from tests import c, tm, u


class TestsFlextInfraModernizerSourceReferences:
    """External consumers retain their backend, branch and dependency semantics."""

    @staticmethod
    @pytest.mark.parametrize("transport", ["https://", "ssh://git@"])
    def test_public_source_migration_preserves_external_contract(
        tmp_path: Path,
        transport: str,
    ) -> None:
        """Only matching Git references change; a second invocation converges."""
        prefix = "https://github.com/reference-owner/"
        old_ref, new_ref = "retired-reference", "next-reference"
        remote = f"{transport}github.com/reference-owner/sample-kit.git"
        requirement = (
            f"sample-kit[feature] @ git+{remote}@{old_ref}"
            '#subdirectory=python ; python_version >= "3.13"'
        )
        unrelated = f"other-kit @ git+https://github.com/other-owner/kit.git@{old_ref}"
        project = tmp_path / c.PYPROJECT_FILENAME
        project.write_text(
            "# Authored consumer metadata\n"
            "[project]\n"
            'name = "external-consumer"\n'
            'version = "1.0.0"\n'
            "dependencies = [\n"
            f"  '{requirement}', # selected runtime dependency\n"
            "  'requests>=2,<3', # retain registry constraint\n"
            f"  '{unrelated}', # retain unrelated source\n"
            "]\n"
            "[project.optional-dependencies]\n"
            f"feature = ['{requirement}']\n"
            "[dependency-groups]\n"
            f"dev = ['{requirement}']\n"
            "[build-system]\n"
            "requires = ['external-builder']\n"
            "build-backend = 'external.build'\n"
            "[tool.uv]\n"
            "override-dependencies = [\n"
            f"  '{requirement}', # explicit override source\n"
            "  'requests<3', # override constraint\n"
            "]\n"
            "constraint-dependencies = [\n"
            f"  '{requirement}', # explicit constraint source\n"
            "]\n"
            "[tool.uv.sources]\n"
            f"table-kit = {{ git = '{remote}', branch = '{old_ref}', "
            "marker = 'sys_platform == \"linux\"' }\n"
            "[tool.poetry.dependencies]\n"
            f"poetry-kit = {{ git = '{remote}', rev = '{old_ref}', "
            "optional = true, extras = ['feature'] }\n"
            "[tool.consumer]\n"
            "integration_branch = 'dev'\n",
            encoding="utf-8",
        )
        arguments = [
            "deps",
            "modernize",
            "--repository-root",
            str(tmp_path),
            "--projects",
            ".",
            "--apply",
            "--git-source-url-prefix",
            prefix,
            "--git-source-ref-from",
            old_ref,
            "--git-source-ref-to",
            new_ref,
        ]
        tm.that(main(arguments), eq=0)
        published = project.read_text(encoding="utf-8")
        for comment in (
            "selected runtime dependency",
            "retain registry constraint",
            "retain unrelated source",
            "explicit override source",
            "override constraint",
            "explicit constraint source",
        ):
            tm.that(published, has=f"# {comment}\n")
        tm.that(published, has="dependencies = [\n")
        tm.that(published, has="override-dependencies = [\n")
        tm.that(published, has="constraint-dependencies = [\n")
        payload = u.Tests.toml_payload(published)
        declared = u.Tests.toml_mapping(payload["project"])
        tm.that(
            declared["dependencies"],
            eq=[
                requirement.replace(f"@{old_ref}", f"@{new_ref}"),
                "requests>=2,<3",
                unrelated,
            ],
        )
        optional = u.Tests.toml_mapping(declared["optional-dependencies"])
        groups = u.Tests.toml_mapping(payload["dependency-groups"])
        tm.that(
            optional["feature"], eq=[requirement.replace(f"@{old_ref}", f"@{new_ref}")]
        )
        tm.that(groups["dev"], eq=[requirement.replace(f"@{old_ref}", f"@{new_ref}")])
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["uv"])
        tm.that(
            uv["override-dependencies"],
            eq=[requirement.replace(f"@{old_ref}", f"@{new_ref}"), "requests<3"],
        )
        tm.that(
            uv["constraint-dependencies"],
            eq=[requirement.replace(f"@{old_ref}", f"@{new_ref}")],
        )
        uv_source = u.Tests.toml_mapping(
            u.Tests.toml_mapping(uv["sources"])["table-kit"]
        )
        tm.that(uv_source["git"], eq=remote)
        tm.that(uv_source["branch"], eq=new_ref)
        tm.that(uv_source["marker"], eq='sys_platform == "linux"')
        poetry = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["poetry"])
        poetry_source = u.Tests.toml_mapping(
            u.Tests.toml_mapping(poetry["dependencies"])["poetry-kit"],
        )
        tm.that(poetry_source["git"], eq=remote)
        tm.that(poetry_source["rev"], eq=new_ref)
        tm.that(poetry_source["optional"], eq=True)
        tm.that(poetry_source["extras"], eq=["feature"])
        tm.that(
            u.Tests.toml_mapping(payload["build-system"])["build-backend"],
            eq="external.build",
        )
        tm.that(
            u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["consumer"])[
                "integration_branch"
            ],
            eq="dev",
        )
        tm.that(published, has="# Authored consumer metadata")
        tm.that(main(arguments), eq=0)
        tm.that(project.read_text(encoding="utf-8"), eq=published)

    @staticmethod
    def test_partial_source_request_fails_before_any_write(tmp_path: Path) -> None:
        """An incomplete transition cannot trigger unrelated modernization."""
        project = tmp_path / c.PYPROJECT_FILENAME
        original = "[project]\nname='external-consumer'\nversion='1.0.0'\n"
        project.write_text(original, encoding="utf-8")
        tm.that(
            main([
                "deps",
                "modernize",
                "--repository-root",
                str(tmp_path),
                "--projects",
                ".",
                "--apply",
                "--git-source-ref-to",
                "next-reference",
            ])
            != 0,
            eq=True,
        )
        tm.that(project.read_text(encoding="utf-8"), eq=original)
