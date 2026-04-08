"""CLI workflow tests for refactor model automation."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from flext_infra import FlextInfraCli


def test_centralize_pydantic_cli_outputs_extended_metrics(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    module_dir = workspace / "src" / "sample_pkg"
    module_dir.mkdir(parents=True)
    (module_dir / "service.py").write_text(
        "from __future__ import annotations\n"
        "from pydantic import BaseModel\n"
        "from typing import TypeAlias\n\n"
        "class SamplePayload(BaseModel):\n"
        "    value: str\n\n"
        "PayloadMap: TypeAlias = dict[str, str]\n",
        encoding="utf-8",
    )
    buffer = StringIO()
    cli_args = [
        "centralize-pydantic",
        f"--workspace={workspace!s}",
        "--dry-run",
        "--normalize-remaining",
    ]
    with redirect_stdout(buffer):
        result = FlextInfraCli().main(["refactor"] + cli_args)
    assert result == 0


def test_centralize_pydantic_cli_apply_uses_local_private_module_imports(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    module_dir = workspace / "src" / "sample_pkg"
    module_dir.mkdir(parents=True)
    (module_dir / "__init__.py").write_text(
        "from __future__ import annotations\n",
        encoding="utf-8",
    )
    service_file = module_dir / "service.py"
    service_file.write_text(
        "from __future__ import annotations\n"
        "from collections.abc import Mapping\n"
        "from typing import TypeAlias\n\n"
        "PayloadMap: TypeAlias = Mapping[str, str]\n"
        "def consume(payload: PayloadMap) -> PayloadMap:\n"
        "    return payload\n\n"
        "value = 1\n",
        encoding="utf-8",
    )
    buffer = StringIO()
    cli_args = [
        "centralize-pydantic",
        f"--workspace={workspace!s}",
        "--apply",
    ]
    with redirect_stdout(buffer):
        result = FlextInfraCli().main(["refactor"] + cli_args)

    assert result == 0
    rewritten = service_file.read_text(encoding="utf-8")
    models_file = module_dir / "_models.py"
    models_text = models_file.read_text(encoding="utf-8")
    assert "PayloadMap: TypeAlias = Mapping[str, str]" not in rewritten
    assert "from sample_pkg._models import PayloadMap" in rewritten
    assert rewritten.startswith("from __future__ import annotations\n")
    assert "class PayloadMap(RootModel[Mapping[str, str]]):" in models_text
    assert "from collections.abc import Mapping" in models_text
    assert service_file.with_suffix(".py.bak").exists()


def test_ultrawork_models_cli_runs_dry_run_copy(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "sample-project"
    module_dir = project / "src" / "sample_pkg"
    module_dir.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        "[project]\nname='sample'\n",
        encoding="utf-8",
    )
    (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
    (module_dir / "service.py").write_text(
        "from __future__ import annotations\n"
        "from pydantic import BaseModel\n\n"
        "class SamplePayload(BaseModel):\n"
        "    value: str\n",
        encoding="utf-8",
    )
    buffer = StringIO()
    cli_args = [
        "ultrawork-models",
        f"--workspace={workspace!s}",
        "--dry-run",
        "--normalize-remaining",
    ]
    with redirect_stdout(buffer):
        result = FlextInfraCli().main(["refactor"] + cli_args)
    assert result == 0


def test_namespace_enforce_cli_fails_on_manual_protocol_violation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "sample-project"
    module_dir = project / "src" / "sample_pkg"
    module_dir.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        "[project]\nname='sample'\n",
        encoding="utf-8",
    )
    (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
    (module_dir / "service.py").write_text(
        "from __future__ import annotations\n"
        "from typing import Protocol\n\n"
        "class External(Protocol):\n"
        "    def call(self) -> str:\n"
        "        ...\n",
        encoding="utf-8",
    )
    buffer = StringIO()
    cli_args = [
        "namespace-enforce",
        f"--workspace={workspace!s}",
        "--dry-run",
    ]
    with redirect_stdout(buffer):
        result = FlextInfraCli().main(["refactor"] + cli_args)
    assert result != 0
