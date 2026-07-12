from __future__ import annotations

from typing import TYPE_CHECKING

from tests.constants import c
from tests.utilities import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraUtilitiesformatting:
    def test_generate_module_skeleton_is_static_on_public_instance(self) -> None:
        # mro-i6nq.10: Guard the public instance binding lost during consolidation.
        source = u.Infra().generate_module_skeleton(
            class_name="FlextDemoModels",
            base_class="FlextModels",
            docstring="Models for demo.",
        )

        compile(source, "models.py", "exec")
        assert "class FlextDemoModels(FlextModels):" in source

    def test_normalize_python_source_is_read_only_and_idempotent(
        self,
        tmp_path: Path,
    ) -> None:
        target = tmp_path / c.Infra.INIT_PY
        source = "x=(\n    1,\n)\n"

        # mro-i6nq.10: Exercise the public read-only normalizer contract directly.
        first = u.Infra.normalize_python_source(source, filename=target).unwrap()
        second = u.Infra.normalize_python_source(first, filename=target).unwrap()

        assert first == "x = (1,)\n"
        assert second == first
        assert not target.exists()

    def test_normalize_python_source_discovers_config_by_filename(
        self,
        tmp_path: Path,
    ) -> None:
        config_path = tmp_path / "pyproject.toml"
        u.Cli.atomic_write_text_file(
            config_path,
            '[tool.ruff.lint.per-file-ignores]\n"ignored.py" = ["F401"]\n',
        ).unwrap()

        ignored = u.Infra.normalize_python_source(
            "import os\n",
            filename=tmp_path / "ignored.py",
        ).unwrap()
        regular = u.Infra.normalize_python_source(
            "import os\n",
            filename=tmp_path / "regular.py",
        ).unwrap()

        assert ignored == "import os\n"
        assert regular == ""

    def test_normalize_python_source_propagates_invalid_syntax(
        self,
        tmp_path: Path,
    ) -> None:
        result = u.Infra.normalize_python_source(
            "def broken(:\n",
            filename=tmp_path / "broken.py",
        )

        assert result.failure
