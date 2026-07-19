"""Ruff tooling SSOT regression tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import tomlkit

from flext_infra import config, u
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer


class TestsFlextInfraModernizerTooling:
    """Verify public modernization preserves canonical Ruff policy."""

    def test_conform_source_emits_complete_ruff_per_file_ignores(
        self, tmp_path: Path
    ) -> None:
        """Preserve rich mappings and the approved tests-only policy."""
        pyproject = tmp_path / "pyproject.toml"
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tmp_path, skip_check=True
        )

        rendered = modernizer.conform_source(
            '[project]\nname = "sample"\n', path=pyproject
        )

        if rendered.failure:
            message = rendered.error or "modernizer failed"
            raise AssertionError(message)
        payload = u.Cli.toml_mapping_from_text(rendered.value)
        if payload is None:
            message = "modernizer emitted invalid TOML"
            raise AssertionError(message)
        mapping = u.Cli.toml_mapping_path(
            payload, ("tool", "ruff", "lint", "per-file-ignores")
        )
        if mapping is None:
            message = "modernizer omitted Ruff per-file ignores"
            raise AssertionError(message)
        canonical = config.Infra.tooling.tools.ruff.lint.per_file_ignores
        if mapping["**/*middleware*"] != sorted(canonical["**/*middleware*"]):
            message = "modernizer replaced rich middleware ignores"
            raise AssertionError(message)
        if mapping["**/__init__.py"] != sorted(canonical["**/__init__.py"]):
            message = "modernizer replaced rich package-root ignores"
            raise AssertionError(message)
        if mapping["**/tests/**/*.py"] != ["FBT001", "PLC1901", "S108"]:
            message = "modernizer omitted approved tests-only ignores"
            raise AssertionError(message)

    def test_conform_existing_source_preserves_non_owned_tooling(
        self, tmp_path: Path
    ) -> None:
        """Merge missing Ruff entries without migrating established consumer policy."""
        pyproject = tmp_path / "pyproject.toml"
        source = """[project]
name = "sample"

[tool.coverage.report]
fail_under = 25

[tool.pytest.ini_options]
addopts = ["--strict-markers", "--markdown-docs"]
filterwarnings = ["ignore:consumer warning"]

[tool.pyrefly]
project-includes = ["src/**/*.py*"]

[tool.pyright]
include = ["src"]

[tool.ruff.lint]
ignore = ["S101", "D102", "PLR2004"]

[tool.ruff.lint.per-file-ignores]
"**/*middleware*" = ["ANN401", "FBT001"]
"consumer-only.py" = ["T201"]

[tool.vulture]
paths = ["src"]
"""
        before = tomlkit.parse(source)
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tmp_path, skip_check=True
        )

        rendered = modernizer.conform_existing_source(source, path=pyproject)

        if rendered.failure:
            message = rendered.error or "preservative conform failed"
            raise AssertionError(message)
        after = tomlkit.parse(rendered.value)
        before_tool = before["tool"]
        after_tool = after["tool"]
        for section in ("coverage", "pytest", "pyrefly", "pyright", "vulture"):
            if after_tool[section] != before_tool[section]:
                message = f"unowned section changed: {section}"
                raise AssertionError(message)
        if after_tool["ruff"]["lint"]["ignore"] != ["S101", "D102", "PLR2004"]:
            message = "authorized global Ruff ignores changed"
            raise AssertionError(message)
        mapping = after_tool["ruff"]["lint"]["per-file-ignores"]
        if mapping["**/*middleware*"] != ["ANN401", "FBT001"]:
            message = "existing Ruff entry changed"
            raise AssertionError(message)
        if mapping["consumer-only.py"] != ["T201"]:
            message = "consumer-owned stale entry was removed"
            raise AssertionError(message)
        if mapping["**/tests/**/*.py"] != ["FBT001", "PLC1901", "S108"]:
            message = "approved tests-only entry was not merged"
            raise AssertionError(message)

    def test_full_modernize_runs_non_ruff_phases_with_existing_ruff_table(
        self, tmp_path: Path
    ) -> None:
        """Keep the broad modernize contract while preserving consumer Ruff entries."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "sample"
version = "0.1.0"

[tool.ruff.lint.per-file-ignores]
"consumer-only.py" = ["T201"]
""",
            encoding="utf-8",
        )
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tmp_path,
            apply_changes=True,
            skip_check=True,
            skip_comments=True,
        )

        exit_code = modernizer.run()

        if exit_code != 0:
            message = f"full modernize exited {exit_code}"
            raise AssertionError(message)
        payload = u.Cli.toml_mapping_from_text(pyproject.read_text(encoding="utf-8"))
        if payload is None:
            message = "full modernize emitted invalid TOML"
            raise AssertionError(message)
        build_system = u.Cli.toml_mapping_child(payload, "build-system")
        if build_system is None or build_system["build-backend"] != "hatchling.build":
            message = "full modernize skipped build-system migration"
            raise AssertionError(message)
        mapping = u.Cli.toml_mapping_path(
            payload, ("tool", "ruff", "lint", "per-file-ignores")
        )
        if mapping is None or mapping["consumer-only.py"] != ["T201"]:
            message = "full modernize removed consumer Ruff entry"
            raise AssertionError(message)
        if mapping["**/tests/**/*.py"] != ["FBT001", "PLC1901", "S108"]:
            message = "full modernize omitted tests Ruff entry"
            raise AssertionError(message)

    def test_conform_existing_source_preserves_multiline_toml_values(
        self, tmp_path: Path
    ) -> None:
        """Insert canonical entries after complete parsed values, never inside arrays."""
        source = """[project]
name = "sample"

[tool.ruff.lint.per-file-ignores]
# before
"consumer.py" = [
  "T201",
]
# between
'single.py' = [ "S101" ]
# after

[tool.coverage.report]
fail_under = 25
"""
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tmp_path, skip_check=True
        )

        rendered = modernizer.conform_existing_source(
            source, path=tmp_path / "pyproject.toml"
        )

        if rendered.failure:
            message = rendered.error or "multiline preservation failed"
            raise AssertionError(message)
        parsed = tomlkit.parse(rendered.value)
        mapping = parsed["tool"]["ruff"]["lint"]["per-file-ignores"]
        if mapping["consumer.py"] != ["T201"] or mapping["single.py"] != ["S101"]:
            message = "existing quoted-key assignments changed"
            raise AssertionError(message)
        if mapping["**/tests/**/*.py"] != ["FBT001", "PLC1901", "S108"]:
            message = "canonical tests assignment missing"
            raise AssertionError(message)
        for preserved in (
            '# before\n"consumer.py" = [\n  "T201",\n]\n# between',
            "'single.py' = [ \"S101\" ]\n# after",
            "[tool.coverage.report]\nfail_under = 25",
        ):
            if preserved not in rendered.value:
                message = f"source bytes changed: {preserved}"
                raise AssertionError(message)

    def test_conform_existing_source_handles_empty_and_invalid_tables(
        self, tmp_path: Path
    ) -> None:
        """Populate an empty table and reject malformed or inline representations."""
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tmp_path, skip_check=True
        )
        empty = modernizer.conform_existing_source(
            '[project]\nname = "sample"\n\n[tool.ruff.lint.per-file-ignores]\n',
            path=tmp_path / "empty.toml",
        )
        if empty.failure:
            message = empty.error or "empty table merge failed"
            raise AssertionError(message)
        parsed = tomlkit.parse(empty.value)
        if "**/tests/**/*.py" not in parsed["tool"]["ruff"]["lint"]["per-file-ignores"]:
            message = "empty table was not populated"
            raise AssertionError(message)
        invalid = modernizer.conform_existing_source(
            '[project\nname = "sample"\n', path=tmp_path / "invalid.toml"
        )
        if invalid.success:
            message = "invalid TOML succeeded"
            raise AssertionError(message)
        inline = modernizer.conform_existing_source(
            '[project]\nname = "sample"\n\n[tool.ruff.lint]\n'
            'per-file-ignores = { "consumer.py" = ["T201"] }\n',
            path=tmp_path / "inline.toml",
        )
        if inline.success:
            message = "inline per-file-ignore table was not rejected"
            raise AssertionError(message)
