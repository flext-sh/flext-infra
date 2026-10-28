"""Public examples dispatch uses the declared repository module, never a directory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u

pytestmark = pytest.mark.slow


class TestsFlextInfraCodegenMakeExamples:
    """Exercise the public Make route and the typed declaration boundary."""

    @staticmethod
    @pytest.mark.parametrize(
        "module",
        [
            "",
            ".runtime",
            "examples..runtime",
            "../runtime",
            "examples/runtime",
            "examples.runtime;touch effect",
            "$(shell touch effect)",
            "examples.runtime\n",
        ],
    )
    def test_malformed_declaration_is_rejected(module: str) -> None:
        """Module input cannot inject Make or shell source or traverse directories."""
        payload = u.Tests.repository_ref("fixture-project").model_dump()
        payload["examples_module"] = module
        with pytest.raises(m.ValidationError):
            _ = m.Infra.RepositoryRef.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_contract_is_public_even_when_examples_directory_exists(
        tmp_path: Path,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Contract mode never mistakes the examples directory for a Make target."""
        root, _ = u.Tests.render_make_environment(tmp_path, profile)
        (root / "examples").mkdir()
        (root / "custom.mk").write_text(
            "pre-examples:\n\t@touch hook-ran\n",
            encoding="utf-8",
        )
        before = tuple(sorted(root.rglob("*")))
        result = tm.ok(
            u.Tests.run_isolated_make(
                ["-f", str(root / "Makefile"), "examples", "OPTIONS=Y"],
                cwd=tmp_path,
            ),
        )
        declaration = next(
            verb for verb in config.Infra.codegen.make.verbs if verb.name == "examples"
        )
        tm.ok(u.Cli.process_succeeded(result.outcome))
        tm.that(result.stdout, has=declaration.description)
        tm.that(result.stdout, lacks="Nothing to be done")
        tm.that(tuple(sorted(root.rglob("*"))), eq=before)

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_absent_entrypoint_fails_before_activation_and_hooks(
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """An absent declaration or source is a failure before any runtime effects."""
        module = "examples.selected" if declared else None
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
            shape=u.Tests.MakeEnvironmentShape(examples_module=module),
        )
        (root / "examples").mkdir()
        (root / ".envrc.local").write_text("touch activation-ran\n", encoding="utf-8")
        (root / "custom.mk").write_text(
            "pre-examples:\n\t@touch hook-ran\n",
            encoding="utf-8",
        )
        result = tm.ok(
            u.Tests.run_isolated_make(
                ["-f", str(root / "Makefile"), "examples"],
                cwd=tmp_path,
            ),
        )
        tm.fail(u.Cli.process_succeeded(result.outcome))
        expected = (
            "declared module source is missing"
            if declared
            else "repository.examples_module"
        )
        tm.that(result.stderr, has=expected)
        tm.fail((root / "activation-ran").exists())
        tm.fail((root / "hook-ran").exists())
        tm.fail((tmp_path / "hook-ran").exists())

    @staticmethod
    def test_selected_module_imports_the_owning_source_from_root_cwd(
        tmp_path: Path,
    ) -> None:
        """Native Make executes the declared module against the actual source tree."""
        module = "examples.selected"
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
            shape=u.Tests.MakeEnvironmentShape(examples_module=module),
        )
        tm.ok(u.Tests.create_python_environment(root))
        examples = root / "examples"
        examples.mkdir()
        (examples / "__init__.py").write_text("", encoding="utf-8")
        (examples / "selected.py").write_text(
            "from pathlib import Path\n"
            "import fixture_project\n"
            "assert Path(fixture_project.__file__).resolve() == "
            "Path.cwd() / 'src/fixture_project/__init__.py'\n"
            "print('declared module imported owning source')\n",
            encoding="utf-8",
        )
        (root / "custom.mk").write_text(
            "pre-examples:\n\t@printf 'pre-examples\\n'\n"
            "post-examples:\n\t@printf 'post-examples\\n'\n",
            encoding="utf-8",
        )
        result = tm.ok(
            u.Tests.run_isolated_make(
                ["-f", str(root / "Makefile"), "examples"],
                cwd=tmp_path,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )
        tm.that(
            result.stdout,
            has=[
                "pre-examples",
                "declared module imported owning source",
                "post-examples",
            ],
        )
