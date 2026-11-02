"""Source-only normalization of legacy protocol declarations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestsProtocolSourceBootstrap:
    """Exercise the pre-import stdlib protocol repair entrypoint."""

    @staticmethod
    def test_normalizes_protocols_without_touching_models_and_repeats(
        tmp_path: Path,
    ) -> None:
        root = tmp_path / "repository"
        protocols = root / "src" / "flext_infra" / "_protocols"
        protocols.mkdir(parents=True)
        module = protocols / "mixed.py"
        module.write_text(
            "from typing import Annotated, Protocol\n"
            "from pydantic import BaseModel, Field\n"
            "from flext_infra import m\n"
            "\n"
            "class Models:\n"
            "    class Payload(BaseModel):\n"
            "        title: Annotated[str, Field(description='keep')]\n"
            "\n"
            "class Ports:\n"
            "    class Reader(Protocol):\n"
            "        title: Annotated[str, 'public', m.Field(description='drop')]\n"
            "        count: int = m.Field(default=0)\n"
            "        receipt: p.Cli.AtomicFileState | None\n"
            "\n"
            "class Other(Protocol):\n"
            "    enabled: Annotated[bool, m.Field(description='drop')]\n",
            encoding="utf-8",
        )
        entrypoint = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "_protocols_bootstrap.py"
        )
        command = (sys.executable, str(entrypoint), str(root))
        first = subprocess.run(command, check=True, capture_output=True, text=True)
        normalized = module.read_text(encoding="utf-8")
        second = subprocess.run(command, check=True, capture_output=True, text=True)

        assert "normalized protocol modules: 1" in first.stdout
        assert "normalized protocol modules: 0" in second.stdout
        assert "title: Annotated[str, 'public']" in normalized
        assert "count: int = ..." in normalized
        assert "enabled: bool" in normalized
        assert normalized.count("@runtime_checkable") == 2
        assert "from typing import runtime_checkable" in normalized
        assert "title: Annotated[str, Field(description='keep')]" in normalized
        assert "from flext_infra import m" not in normalized
        assert "if TYPE_CHECKING:\n    from flext_infra import p" in normalized
        assert "\nfrom flext_infra import p\n" not in normalized
