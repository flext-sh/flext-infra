"""Atomic file state comparison preserves exact bytes and file presence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra import m, u
from tests import c, tm


class TestsFlextInfraCodegenFilePlanState:
    """Equal binary states converge; content, presence, and mode deltas do not."""

    _GATES: Mapping[str, Mapping[str, int]] = {"lint": {"time-seconds": 30}}

    @staticmethod
    def _observed_state(root: Path, *, content: bytes) -> m.Cli.AtomicFileState:
        """Read one real file through the canonical binary state owner.

        Returns:
            The resulting ``m.Cli.AtomicFileState``.

        """
        target = root / "member" / c.PYPROJECT_FILENAME
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        state = u.Cli.atomic_read_binary_file_state(target, required=True)
        if state.failure:
            tm.reject(state.error)
        return state.value

    @pytest.mark.parametrize("content", [b"", b'name = "demo"\n', b"\xff\n"])
    def test_equal_binary_content_is_not_drift(
        self,
        tmp_path: Path,
        content: bytes,
    ) -> None:
        """Test equal binary content is not drift."""
        before = self._observed_state(tmp_path, content=content)

        differs = u.Infra.atomic_file_state_differs(
            before,
            desired_content=content,
            desired_mode=before.mode,
        )

        tm.that(differs, eq=False)

    @pytest.mark.parametrize(
        ("content", "desired_content"),
        [
            (b'name = "demo"\n', b'name = "other"\n'),
            (b'name = "demo"', b'name = "demo"\n'),
            (b'name = "demo"\r\n', b'name = "demo"\n'),
            (b"\xff\n", b"\xfe\n"),
            (b"\xff\n", b"\xef\xbf\xbd\n"),
        ],
    )
    def test_real_content_delta_still_differs(
        self,
        tmp_path: Path,
        content: bytes,
        desired_content: bytes,
    ) -> None:
        """Test real content delta still differs."""
        before = self._observed_state(tmp_path, content=content)

        differs = u.Infra.atomic_file_state_differs(
            before,
            desired_content=desired_content,
            desired_mode=before.mode,
        )

        tm.that(differs, eq=True)

    def test_mode_delta_differs_even_with_equal_content(self, tmp_path: Path) -> None:
        """Test mode delta differs even with equal content."""
        before = self._observed_state(tmp_path, content=b'name = "demo"\n')

        drifted = u.Infra.atomic_file_state_differs(
            before,
            desired_content=before.content,
            desired_mode=0o755,
        )

        tm.that(drifted, eq=True)

    @staticmethod
    def test_absent_file_is_not_an_empty_file(tmp_path: Path) -> None:
        """Test absent file is not an empty file."""
        state = u.Cli.atomic_read_binary_file_state(
            tmp_path / c.PYPROJECT_FILENAME,
            required=False,
        )
        if state.failure:
            tm.reject(state.error)

        tm.that(
            u.Infra.atomic_file_state_differs(
                state.value, desired_content=b"", desired_mode=state.value.mode
            ),
            truth=True,
        )
        tm.that(
            u.Infra.atomic_file_state_differs(
                state.value, desired_content=None, desired_mode=state.value.mode
            ),
            truth=False,
        )

    def test_empty_file_requires_deletion(self, tmp_path: Path) -> None:
        """Test empty file requires deletion."""
        before = self._observed_state(tmp_path, content=b"")

        tm.that(
            u.Infra.atomic_file_state_differs(
                before, desired_content=None, desired_mode=None
            ),
            truth=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "content", [b"", b"def load() -> bytes: ...\n", b"invalid [\n"]
    )
    def test_stub_output_is_rejected_at_the_plan_model(
        tmp_path: Path,
        content: bytes,
    ) -> None:
        """A first-party stub write cannot even be planned; live bytes stay."""
        target = tmp_path / "boundary.pyi"
        target.write_bytes(content)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        with pytest.raises(m.ValidationError, match=r"\.pyi publication is forbidden"):
            m.Infra.CodegenFilePlan(
                project=tmp_path,
                path=target,
                before=before,
                desired_content=content,
                desired_mode=before.mode,
            )
        tm.that(target.read_bytes(), eq=content)
        tm.that(tuple(tmp_path.iterdir()), eq=(target,))

    @staticmethod
    def test_stub_retirement_uses_the_real_absent_state(tmp_path: Path) -> None:
        """The publication law permits guarded removal, not empty stub replacement."""
        target = tmp_path / "boundary.pyi"
        target.write_bytes(b"value: int\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        plan = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=target,
            before=before,
            desired_content=None,
            desired_mode=None,
        )
        tm.ok(u.Infra.publish_codegen_plans(tmp_path, (plan,)))
        tm.that(target.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize("name", ["py.typed", "typings.py", "protocols.py"])
    def test_legitimate_typing_surfaces_remain_publishable(
        tmp_path: Path,
        name: str,
    ) -> None:
        """Only stub output paths are prohibited, not ordinary typed declarations."""
        target = tmp_path / name
        content = (
            b""
            if name == "py.typed"
            else b"from typing import Protocol\nclass Port(Protocol):\n"
            b"    def load(self) -> bytes: ...\n"
        )
        plan = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=target,
            before=tm.ok(u.Cli.atomic_read_binary_file_state(target)),
            desired_content=content,
            desired_mode=0o644,
        )
        tm.ok(
            u.Cli.publish_file_changes(
                (plan,), lock_path=u.Infra.mutation_lock_path(plan.project).unwrap()
            )
        )
        tm.that(target.read_bytes(), eq=content)

    @pytest.mark.parametrize(
        ("content", "desired_content"),
        [
            (b'name = "demo"', b'name = "demo"\n'),
            (b'name = "demo"\r\n', b'name = "demo"\n'),
            (b"\xff\n", b"\xfe\n"),
        ],
    )
    def test_drift_report_exposes_exact_byte_delta(
        self,
        tmp_path: Path,
        content: bytes,
        desired_content: bytes,
    ) -> None:
        """Test drift report exposes exact byte delta."""
        before = self._observed_state(tmp_path, content=content)
        planned = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=before.path,
            before=before,
            desired_content=desired_content,
            desired_mode=before.mode,
        )

        report = u.Infra.codegen_file_drift_report((planned,))

        tm.that(report, has=repr(content))
        tm.that(report, has=repr(desired_content))
        tm.that(report, lacks="mode-only drift")

    def test_drift_report_names_mode_only_delta(self, tmp_path: Path) -> None:
        """Test drift report names mode only delta."""
        before = self._observed_state(tmp_path, content=b'name = "demo"\n')
        planned = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=before.path,
            before=before,
            desired_content=before.content,
            desired_mode=0o755,
        )

        report = u.Infra.codegen_file_drift_report((planned,))

        tm.that(report, has="mode-only drift")
        tm.that(report, has="desired=0o755")

    @staticmethod
    @pytest.mark.parametrize("limit", [0, -1])
    def test_drift_report_rejects_non_positive_limit(limit: int) -> None:
        """Test drift report rejects non positive limit."""
        with pytest.raises(ValueError, match="limit must be positive"):
            u.Infra.codegen_file_drift_report(
                (),
                limit=limit,
            )
