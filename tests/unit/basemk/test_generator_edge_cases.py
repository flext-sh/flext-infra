"""Real edge-case tests for public generator APIs."""

from __future__ import annotations

import io
from pathlib import Path
from typing import override

from flext_infra import FlextInfraBaseMkGenerator


class _FailingStream(io.StringIO):
    @override
    def write(self, s: str) -> int:
        del s
        msg = "Stream write failed"
        raise OSError(msg)


def test_generator_write_handles_file_path_failure(tmp_path: Path) -> None:
    blocked_parent = tmp_path / "readonly"
    blocked_parent.write_text("occupied", encoding="utf-8")

    result = FlextInfraBaseMkGenerator().write(
        "all:\n\t@echo 'test'\n",
        output=blocked_parent / "test.mk",
    )

    assert result.failure
    assert "base.mk write failed" in (result.error or "")


def test_generator_write_to_stream_handles_oserror() -> None:
    result = FlextInfraBaseMkGenerator().write(
        "all:\n\t@echo 'test'\n",
        stream=_FailingStream(),
    )

    assert result.failure
    assert "stdout write failed" in (result.error or "")


def test_generator_write_to_closed_stream_fails() -> None:
    stream = io.StringIO()
    stream.close()

    result = FlextInfraBaseMkGenerator().write(
        "all:\n\t@echo 'test'\n",
        stream=stream,
    )

    assert result.failure
    assert "stdout write failed" in (result.error or "")
