"""Test formatting module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, p, tm, u


class TestsFlextInfraUtilitiesformatting:
    @staticmethod
    def test_missing_native_width_never_invents_a_formatting_policy(
        tool_config_document: p.Infra.ToolConfigDocument,
    ) -> None:
        """Missing owned configuration fails instead of fabricating a width."""
        document = tool_config_document.model_copy(
            update={"settings": {**tool_config_document.settings, "ruff": ()}}
        )
        with pytest.raises(KeyError, match="line-length"):
            u.Infra.native_tool_setting(document, "ruff", "line-length", int)

    @staticmethod
    @pytest.mark.parametrize("width_factor", [1, 2])
    def test_staged_formatting_uses_destination_policy_without_publication(
        tmp_path: Path,
        width_factor: int,
    ) -> None:
        """Format and execute candidate bytes without replacing their live receipt."""
        width = (
            u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff", "line-length", int
            )
            * width_factor
        )
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        pyproject = root / c.PYPROJECT_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                pyproject,
                re.sub(
                    r"(?m)^line-length = \d+$",
                    f"line-length = {width}",
                    pyproject.read_text(encoding=c.DEFAULT_ENCODING),
                    count=1,
                ),
            )
        )
        path = package / "candidate.py"
        original = "values = []\n"
        tm.ok(u.Cli.atomic_write_text_file(path, original))
        values = tuple(range(width))
        candidate = "import sys\n\nvalues = [" + ", ".join(map(str, values)) + "]\n"
        preserved = tm.ok(u.Infra.normalize_source(root, path, candidate))
        tm.fail("import sys" in preserved)
        tm.ok(all(len(line) <= width for line in preserved.splitlines()))
        tm.that(
            tm.ok(u.Infra.normalize_source(root, path, preserved)),
            eq=preserved,
        )
        # Premise: a rewrite of authored bytes carrying format debt repairs
        # only what it introduced; the debt stays for ``make fmt``.
        values_line = "values = [" + ", ".join(map(str, values)) + "]"
        normalized = tm.ok(
            u.Infra.normalize_source(
                root,
                path,
                candidate,
                before_source=candidate + "print(sys.version)\n",
            )
        )
        tm.fail("import sys" in normalized)
        tm.that(normalized, has=values_line)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        output = tm.ok(
            u.Cli.run((sys.executable, "-c", preserved + "print(sum(values))\n"))
        )
        tm.that(output.stdout.strip(), eq=str(sum(values)))
        with pytest.raises(SyntaxError):
            u.Infra.normalize_source(root, path, "values = [\n")
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

    @staticmethod
    def test_incompatible_line_width_rejects_candidate_without_publication(
        tmp_path: Path,
    ) -> None:
        """Unrepairable destination policy fails without changing live source."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        pyproject = root / c.PYPROJECT_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                pyproject,
                re.sub(
                    r"(?m)^line-length = \d+$",
                    "line-length = 1",
                    pyproject.read_text(encoding=c.DEFAULT_ENCODING),
                    count=1,
                ),
            )
        )
        path = package / "candidate.py"
        original = "values = []\n"
        tm.ok(u.Cli.atomic_write_text_file(path, original))

        rejected = u.Infra.normalize_source(root, path, "values = [1, 2]\n")

        tm.fail(rejected, has="E501")
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original)

    @staticmethod
    def test_publication_never_rewrites_authored_module_with_findings(
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
    ) -> None:
        """An authored module with lint and format findings is published as is.

        Premise (measured on a consumer ``make gen``): a source rewrite that
        only reorders imports reached publication, where the normalization
        repaired its own ``I001`` and then reformatted the whole authored
        module. Publication repairs only what a rewrite introduced; authored
        format debt and lint findings belong to ``make fmt``/``make fix``.
        A generated projection is still formatted in full. Both sources are
        scenario data under ``tests/fixtures/authored-publication``.
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        scenarios = fixture_tree(
            "authored-publication", destination=tmp_path / "scenarios"
        )
        authored = (scenarios / "authored.py").read_text(encoding=c.DEFAULT_ENCODING)
        churn = (scenarios / "import-churn.py").read_bytes()
        path = package / "authored.py"
        tm.ok(u.Cli.atomic_write_text_file(path, authored))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(path))
        plan = m.Infra.CodegenFilePlan(
            project=root,
            path=path,
            before=before,
            desired_content=churn,
            desired_mode=before.mode,
        )
        changes = tm.ok(u.Infra.normalized_codegen_changes((plan,)))
        tm.that(changes[0].desired_content, eq=before.content)
        tm.ok(u.Infra.publish_codegen_plans(root, (plan,)))
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=authored)
        generated = f"{c.Infra.AUTOGEN_HEADER}\nvalues = [\n    1\n]\n"
        tm.that(
            tm.ok(
                u.Infra.normalize_source(
                    root,
                    package / "generated.py",
                    generated + "extra = [\n    2\n]\n",
                    before_source=generated,
                )
            ),
            has="values = [1]\nextra = [2]\n",
        )

    @staticmethod
    def test_touched_formatting_repairs_imports_and_reaches_fixed_point(
        tmp_path: Path,
    ) -> None:
        """Repair published sources through the destination's lint and format policy."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "published.py"
        missing = package / "removed.py"
        tm.ok(u.Cli.atomic_write_text_file(path, "import sys\n\nvalues=[1,2]\n"))
        u.Infra.normalize_touched_files((path, path, missing), root)
        normalized = path.read_text(encoding=c.DEFAULT_ENCODING)
        tm.fail("import sys" in normalized)
        u.Infra.normalize_touched_files((path, missing), root)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=normalized)
        tm.fail(missing.exists())
        output = tm.ok(
            u.Cli.run((sys.executable, "-c", normalized + "print(sum(values))\n"))
        )
        tm.that(output.stdout.strip(), eq="3")

    @staticmethod
    def test_generate_module_skeleton_is_static_on_public_instance() -> None:
        # flext-i6nq.10: Guard the public instance binding lost during consolidation.
        source = tm.ok(
            u.Infra().generate_module_skeleton(
                context=m.Infra.ModuleSkeletonRenderContext(
                    class_name="FlextModelsDemo",
                    base_class="FlextModels",
                    base_module="flext_core",
                    docstring="Models for demo.",
                ),
            )
        )

        compile(source, "models.py", "exec")
        tm.that(source, has="class FlextModelsDemo(\n    FlextModels,\n):")
        tm.that(source, has="from flext_core import FlextModels")

    @staticmethod
    def test_generate_module_skeleton_renders_uncomposed_domain() -> None:
        # g95/g96: seed() renders domain skeletons with no base class; the JSON
        # context dump delivers lists, so the template must never build tuples.
        rendered = u.Infra.generate_module_skeleton(
            context=m.Infra.ModuleSkeletonRenderContext(
                class_name="FlextUtilitiesDemoDomain",
                base_class=None,
                base_module=None,
                docstring="Native domain namespace.",
            ),
        )

        source = tm.ok(rendered)
        compile(source, "domain.py", "exec")
        tm.that(source, has="class FlextUtilitiesDemoDomain:")
        tm.that(source, has="Native domain namespace.")
