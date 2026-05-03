"""Focused tests for census preview source caching."""

from __future__ import annotations

from pathlib import Path

import pytest

import flext_infra
import flext_infra.refactor.census as census_module
from flext_infra import FlextInfraRefactorCensus, m, p, r
from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from tests import u


class TestsFlextInfraRefactorCensusPreviewCache:
    """Validate preview-path source caching in census dry runs."""

    @staticmethod
    def _candidate(
        file_path: Path,
        *,
        object_name: str = "helper",
    ) -> m.Infra.Census.RemovalCandidate:
        """Build one minimal top-level removal candidate."""
        return m.Infra.Census.RemovalCandidate(
            project="flext-demo",
            file_path=str(file_path.resolve()),
            line=3,
            object_name=object_name,
            object_kind="function",
            scope_path=object_name,
            reason="unused",
            suggested_action="remove",
        )

    def test_preview_simple_removal_candidate_reuses_shared_source_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Repeated previews reuse the same original source snapshot."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def helper() -> int:\n"
                "    return 1\n"
            ),
            encoding="utf-8",
        )
        candidate = self._candidate(module_path)
        original_source = flext_infra.FlextInfraRopeWorkspace.source
        source_calls = 0

        def _tracking_source(
            rope: flext_infra.FlextInfraRopeWorkspace,
            file_path: Path,
        ) -> str:
            """Track source reads for the target module."""
            nonlocal source_calls
            if file_path.resolve() == module_path.resolve():
                source_calls += 1
            return original_source(rope, file_path)

        def _preview_source_writes(
            *args: object,
            **kwargs: object,
        ) -> tuple[bool, list[str]]:
            """Short-circuit protected preview writes for this unit test."""
            del args, kwargs
            return (True, [])

        monkeypatch.setattr(
            flext_infra.FlextInfraRopeWorkspace,
            "source",
            _tracking_source,
        )
        monkeypatch.setattr(
            FlextInfraUtilitiesProtectedEdit,
            "preview_source_writes",
            staticmethod(_preview_source_writes),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            source_cache: dict[Path, str] = {}
            first = FlextInfraUtilitiesRefactorCensus.preview_simple_removal_candidate(
                rope,
                workspace_root,
                candidate,
                gates=("lint",),
                source_cache=source_cache,
            )
            second = (
                FlextInfraUtilitiesRefactorCensus.preview_simple_removal_candidate(
                    rope,
                    workspace_root,
                    candidate,
                    gates=("lint",),
                    source_cache=source_cache,
                )
            )

        assert first.unwrap() is True
        assert second.unwrap() is True
        assert source_calls == 1
        assert module_path.resolve() in source_cache

    def test_validated_project_reports_share_one_preview_source_cache(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Dry-run validation reuses one source cache across candidates."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            "from __future__ import annotations\n",
            encoding="utf-8",
        )
        service = FlextInfraRefactorCensus(
            workspace=workspace_root,
            selected_projects=("flext-demo",),
            include_local_scopes=False,
        )
        project_report = m.Infra.Census.ProjectReport(
            project="flext-demo",
            removal_candidate_count=2,
            removal_candidates=(
                self._candidate(module_path, object_name="first"),
                self._candidate(module_path, object_name="second"),
            ),
        )
        seen_cache_ids: list[int] = []

        def _preview_candidate(
            rope: p.Infra.RopeWorkspaceDsl,
            workspace: Path,
            candidate: m.Infra.Census.RemovalCandidate,
            *,
            gates: tuple[str, ...],
            source_cache: dict[Path, str] | None = None,
        ) -> p.Result[bool]:
            """Capture the source cache instance reused across candidates."""
            del rope, workspace, candidate, gates
            assert source_cache is not None
            seen_cache_ids.append(id(source_cache))
            return r[bool].ok(True)

        monkeypatch.setattr(
            census_module.u.Infra,
            "preview_simple_removal_candidate",
            staticmethod(_preview_candidate),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            validated = service._validated_project_reports(
                rope,
                (project_report,),
            )

        assert len(validated) == 1
        assert validated[0].removal_candidate_count == 2
        assert len(seen_cache_ids) == 2
        assert seen_cache_ids[0] == seen_cache_ids[1]
