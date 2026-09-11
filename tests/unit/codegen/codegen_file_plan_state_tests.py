"""Atomic file state comparison reconciles bytes and str representations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_cli import m, u

from flext_infra import c
from flext_infra.utilities import FlextInfraUtilitiesCodegenFilePlan

_GATES: Mapping[str, Mapping[str, int]] = {"lint": {"time-seconds": 30}}


def _observed_state(root: Path, *, text: str) -> m.Cli.AtomicFileState:
    """Read one real file through the canonical binary state owner."""
    target = root / "member" / c.Infra.PYPROJECT_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    state = u.Cli.atomic_read_binary_file_state(target, required=True)
    if state.failure:
        raise AssertionError(state.error)
    return state.value


class TestsCodegenFilePlanStateDiffers:
    """Same content in bytes vs str is not drift; real deltas still are."""

    def test_bytes_before_str_desired_same_content_is_not_drift(
        self, tmp_path: Path
    ) -> None:
        before = _observed_state(tmp_path, text='name = "demo"\n')

        differs = FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            before, desired_content=b'name = "demo"\n', desired_mode=before.mode
        )

        assert differs is False

    def test_str_desired_matches_binary_observed(self, tmp_path: Path) -> None:
        before = _observed_state(tmp_path, text='name = "demo"\n')

        differs = FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            before, desired_content=b'name = "demo"\n', desired_mode=before.mode
        )

        assert differs is False

    def test_real_content_delta_still_differs(self, tmp_path: Path) -> None:
        before = _observed_state(tmp_path, text='name = "demo"\n')

        differs = FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            before, desired_content=b'name = "other"\n', desired_mode=before.mode
        )

        assert differs is True

    def test_mode_delta_differs_even_with_equal_content(self, tmp_path: Path) -> None:
        before = _observed_state(tmp_path, text='name = "demo"\n')

        drifted = FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            before, desired_content=b'name = "demo"\n', desired_mode=0o755
        )

        assert drifted is True
