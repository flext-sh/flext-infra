"""Typed pytest selector boundary contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c
from flext_infra.validate.pytest_selector import FlextInfraPytestSelectorValidator
from flext_tests import tm


class TestsFlextInfraPytestSelectorValidator:
    """Prove selector syntax and filesystem containment before argv creation."""

    def test_file_nodeid_with_spaces_and_percent_is_preserved(
        self, tmp_path: Path
    ) -> None:
        relative = "tests/unit/sample % test.py"
        target = tmp_path / relative
        target.parent.mkdir(parents=True)
        target.write_text("", encoding="utf-8")
        file = f"{relative}::TestsSample::test exact"
        validator = FlextInfraPytestSelectorValidator(
            workspace_root=tmp_path,
            file=file,
            match="exact name and not slow",
            what="all",
        )

        tm.ok(validator.execute())
        tm.that(validator.file, eq=file)

    @pytest.mark.parametrize(
        "file",
        [
            "/outside/test_sample.py",
            "../test_sample.py",
            "tests/../test_sample.py",
            r"tests\test_sample.py",
            "::TestsSample::test_sample",
            "--maxfail=0",
            "tests/test_sample.py\n--maxfail=0",
        ],
    )
    def test_file_rejects_non_normalized_or_control_text(self, file: str) -> None:
        workspace_root = Path.cwd()
        with pytest.raises(c.ValidationError, match="file must"):
            FlextInfraPytestSelectorValidator(workspace_root=workspace_root, file=file)

    def test_what_accepts_only_canonical_test_modes(self) -> None:
        workspace_root = Path.cwd()
        validator = FlextInfraPytestSelectorValidator(
            workspace_root=workspace_root, what="all"
        )
        tm.ok(validator.execute())
        for what in ("cache-status", "cache-clear", "cache-checkpoint"):
            tm.ok(
                FlextInfraPytestSelectorValidator(
                    workspace_root=workspace_root, what=what
                ).execute()
            )
        tm.ok(
            FlextInfraPytestSelectorValidator(
                workspace_root=workspace_root, what="profile", match="focused"
            ).execute()
        )
        with pytest.raises(c.ValidationError, match="profile requires FILE or MATCH"):
            FlextInfraPytestSelectorValidator(
                workspace_root=workspace_root, what="profile"
            )
        with pytest.raises(c.ValidationError, match="what must be"):
            FlextInfraPytestSelectorValidator(
                workspace_root=workspace_root, what="$(shell touch marker)"
            )
        with pytest.raises(c.ValidationError, match="what must be"):
            FlextInfraPytestSelectorValidator(workspace_root=workspace_root, what="cov")
        with pytest.raises(
            c.ValidationError, match="cache-status rejects FILE and MATCH"
        ):
            FlextInfraPytestSelectorValidator(
                workspace_root=workspace_root, what="cache-status", match="x"
            )

    def test_full_rejects_focused_selectors(self) -> None:
        """The complete-suite coverage gate cannot describe a subset."""
        workspace_root = Path.cwd()
        with pytest.raises(c.ValidationError, match="full rejects FILE and MATCH"):
            FlextInfraPytestSelectorValidator(
                workspace_root=workspace_root, what="full", file="tests/test_sample.py"
            )
        with pytest.raises(c.ValidationError, match="full rejects FILE and MATCH"):
            FlextInfraPytestSelectorValidator(
                workspace_root=workspace_root, what="full", match="sample"
            )

    def test_file_rejects_symlink_hop(self, tmp_path: Path) -> None:
        target = tmp_path / "target.py"
        target.write_text("", encoding="utf-8")
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "linked.py").symlink_to(target)

        result = FlextInfraPytestSelectorValidator(
            workspace_root=tmp_path, file="tests/linked.py"
        ).execute()

        tm.fail(result, has="symlink")

    def test_missing_file_fails_at_typed_boundary(self, tmp_path: Path) -> None:
        result = FlextInfraPytestSelectorValidator(
            workspace_root=tmp_path, file="tests/missing.py::test_missing"
        ).execute()

        tm.fail(result, has="does not exist")
