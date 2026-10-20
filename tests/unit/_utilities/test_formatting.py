"""Test formatting module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, config
from tests import tm, u


class TestsFlextInfraUtilitiesformatting:
    @staticmethod
    @pytest.mark.parametrize("width_factor", [1, 2])
    def test_staged_formatting_uses_destination_policy_without_publication(
        tmp_path: Path,
        width_factor: int,
    ) -> None:
        """Format and execute candidate bytes without replacing their live receipt."""
        width = config.Infra.tooling.tools.ruff.line_length * width_factor
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        pyproject = root / c.PYPROJECT_FILENAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                pyproject,
                pyproject.read_text(encoding=c.DEFAULT_ENCODING).replace(
                    "[tool.ruff]\n", f"[tool.ruff]\nline-length = {width}\n", 1
                ),
            )
        )
        path = package / "candidate.py"
        original = "values = []\n"
        tm.ok(u.Cli.atomic_write_text_file(path, original))
        values = tuple(range(width))
        candidate = "import sys\n\nvalues = [" + ", ".join(map(str, values)) + "]\n"
        preserved = tm.ok(u.Infra.normalize_source(root, path, candidate))
        tm.that("import sys" in preserved, eq=False)
        normalized = tm.ok(
            u.Infra.normalize_source(
                root,
                path,
                candidate,
                before_source=candidate + "print(sys.version)\n",
            )
        )
        tm.that("import sys" in normalized, eq=False)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        tm.that(all(len(line) <= width for line in normalized.splitlines()), eq=True)
        tm.that(
            tm.ok(u.Infra.normalize_source(root, path, normalized)),
            eq=normalized,
        )
        output = tm.ok(
            u.Cli.run((sys.executable, "-c", normalized + "print(sum(values))\n"))
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
                pyproject.read_text(encoding=c.DEFAULT_ENCODING).replace(
                    "[tool.ruff]\n", "[tool.ruff]\nline-length = 1\n", 1
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
        tm.that("import sys" in normalized, eq=False)
        u.Infra.normalize_touched_files((path, missing), root)
        tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=normalized)
        tm.that(missing.exists(), eq=False)
        output = tm.ok(
            u.Cli.run((sys.executable, "-c", normalized + "print(sum(values))\n"))
        )
        tm.that(output.stdout.strip(), eq="3")

    @staticmethod
    def test_generate_module_skeleton_is_static_on_public_instance() -> None:
        # flext-i6nq.10: Guard the public instance binding lost during consolidation.
        source = u.Infra().generate_module_skeleton(
            class_name="FlextDemoModels",
            base_class="FlextModels",
            base_module="flext_core",
            docstring="Models for demo.",
        )

        compile(source, "models.py", "exec")
        tm.that(source, has="class FlextDemoModels(FlextModels):")
        tm.that(source, has="from flext_core import FlextModels")
