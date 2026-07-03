"""Focused tests for census preview source caching."""

from __future__ import annotations

from pathlib import Path

import pytest

import flext_infra
from flext_infra import c, m, p, r, u as infra_u
from flext_infra._utilities.census import FlextInfraUtilitiesRefactorCensus
from flext_infra._utilities.protected_edit import FlextInfraUtilitiesProtectedEdit
from flext_infra.refactor.census import FlextInfraRefactorCensus
from tests.typings import t
from tests.utilities import u
from flext_infra.workspace.rope import FlextInfraRopeWorkspace


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
        original_source = FlextInfraRopeWorkspace.source
        source_calls = 0

        def _tracking_source(
            rope: FlextInfraRopeWorkspace,
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
            FlextInfraRopeWorkspace,
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
            second = FlextInfraUtilitiesRefactorCensus.preview_simple_removal_candidate(
                rope,
                workspace_root,
                candidate,
                gates=("lint",),
                source_cache=source_cache,
            )

        assert first.unwrap() is True
        assert second.unwrap() is True
        assert source_calls == 1
        assert module_path.resolve() in source_cache

    def test_build_simple_removal_sources_collapse_excess_blank_lines(
        self,
        tmp_path: Path,
    ) -> None:
        """Removing a top-level block should not leave four blank lines behind."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def before() -> int:\n"
                "    return 1\n\n\n"
                "class Helper:\n"
                "    pass\n\n\n"
                "def after() -> int:\n"
                "    return before()\n"
            ),
            encoding="utf-8",
        )
        candidate = m.Infra.Census.RemovalCandidate(
            project="flext-demo",
            file_path=str(module_path.resolve()),
            line=6,
            object_name="Helper",
            object_kind="class",
            scope_path="Helper",
            reason="unused",
            suggested_action="remove",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            updates = FlextInfraUtilitiesRefactorCensus.build_simple_removal_sources(
                rope,
                candidate,
            )

        assert updates is not None
        updated_source = updates[module_path.resolve()]
        assert "class Helper" not in updated_source
        assert "def after" in updated_source
        assert "\n\n\n\n" not in updated_source

    def test_build_simple_removal_sources_handle_multiline_class_base_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Multiline class-base references should not abort simple-removal planning."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        base_path = package_root / "base.py"
        base_path.write_text(
            ("from __future__ import annotations\n\nclass Shared:\n    pass\n"),
            encoding="utf-8",
        )
        tests_dir = workspace_root / c.Infra.DIR_TESTS
        tests_dir.mkdir(parents=True, exist_ok=True)
        consumer_path = tests_dir / "constants.py"
        consumer_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from flext_demo.base import Shared\n\n"
                "class Other:\n"
                "    pass\n\n"
                "class TestsFacade:\n"
                "    class Tests(\n"
                "        Other,\n"
                "        Shared,\n"
                "    ):\n"
                "        pass\n"
            ),
            encoding="utf-8",
        )
        candidate = m.Infra.Census.RemovalCandidate(
            project="flext-demo",
            file_path=str(base_path.resolve()),
            line=3,
            object_name="Shared",
            object_kind="class",
            scope_path="Shared",
            reason="test_only",
            suggested_action="remove",
            test_reference_sites=(
                m.Infra.Census.ReferenceSite(
                    file_path=str(consumer_path.resolve()),
                    line=3,
                    surface=c.Infra.DIR_TESTS,
                ),
                m.Infra.Census.ReferenceSite(
                    file_path=str(consumer_path.resolve()),
                    line=11,
                    surface=c.Infra.DIR_TESTS,
                ),
            ),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            updates = FlextInfraUtilitiesRefactorCensus.build_simple_removal_sources(
                rope,
                candidate,
            )

        assert updates is not None
        updated_consumer = updates[consumer_path.resolve()]
        assert "from flext_demo.base import Shared" not in updated_consumer
        assert "Shared," not in updated_consumer
        assert "Other," in updated_consumer

    def test_removed_alias_names_resolve_runtime_aliases_via_rope_objects(
        self,
        tmp_path: Path,
    ) -> None:
        """Removed aliases are resolved from Rope object identity, not AST."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                '__all__: list[str] = ["Helper", "h"]\n\n'
                "class Helper:\n"
                "    pass\n\n"
                "h = Helper\n"
            ),
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            alias_names = FlextInfraUtilitiesRefactorCensus._removed_alias_names(
                rope,
                module_path,
                target_name="Helper",
                removed_ranges=((8, 8),),
            )

        assert alias_names == ("h",)

    def test_aliased_import_occurrence_lines_use_rope_import_statements(
        self,
        tmp_path: Path,
    ) -> None:
        """Aliased import usage is located from Rope import statements."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        base_path = package_root / "base.py"
        base_path.write_text(
            ("from __future__ import annotations\n\nclass Shared:\n    pass\n"),
            encoding="utf-8",
        )
        consumer_path = package_root / "consumer.py"
        consumer_source = (
            "from flext_demo.base import Shared as Alias\n\nVALUE = Alias\n"
        )
        consumer_path.write_text(
            consumer_source,
            encoding="utf-8",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            occurrence_lines = (
                FlextInfraUtilitiesRefactorCensus._aliased_import_occurrence_lines(
                    rope,
                    consumer_path,
                    consumer_source,
                    imported_name="Shared",
                )
            )

        assert occurrence_lines == (1, 3)

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
            gates: t.StrSequence,
            source_cache: dict[Path, str] | None = None,
        ) -> p.Result[bool]:
            """Capture the source cache instance reused across candidates."""
            del rope, workspace, candidate, gates
            assert source_cache is not None
            seen_cache_ids.append(id(source_cache))
            return r[bool].ok(True)

        monkeypatch.setattr(
            infra_u.Infra,
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

    def test_preview_simple_removal_candidate_formats_blank_lines_after_removal(
        self,
        tmp_path: Path,
    ) -> None:
        """Preview formatting fixes blank-line churn introduced by class removal."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "dispatcher.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def run() -> int:\n"
                "    return 1\n\n\n"
                "class ExampleDispatchDsl:\n"
                "    @staticmethod\n"
                "    def run() -> int:\n"
                "        return run()\n\n\n"
                'if __name__ == "__main__":\n'
                "    raise SystemExit(run())\n"
            ),
            encoding="utf-8",
        )
        candidate = m.Infra.Census.RemovalCandidate(
            project="flext-demo",
            file_path=str(module_path.resolve()),
            line=6,
            object_name="ExampleDispatchDsl",
            object_kind="class",
            scope_path="ExampleDispatchDsl",
            reason="unused",
            suggested_action="remove",
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            preview = (
                FlextInfraUtilitiesRefactorCensus.preview_simple_removal_candidate(
                    rope,
                    workspace_root,
                    candidate,
                    gates=("lint",),
                )
            )

        assert preview.unwrap() is True
        source = module_path.read_text(encoding="utf-8")
        assert "class ExampleDispatchDsl" in source

    def test_validated_project_reports_record_preview_rejections(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Rejected previews remain visible as violations without aborting."""
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
            removal_candidate_count=1,
            removal_candidates=(self._candidate(module_path),),
        )

        def _preview_candidate(
            rope: p.Infra.RopeWorkspaceDsl,
            workspace: Path,
            candidate: m.Infra.Census.RemovalCandidate,
            *,
            gates: t.StrSequence,
            source_cache: dict[Path, str] | None = None,
        ) -> p.Result[bool]:
            """Return one explicit preview failure for the candidate."""
            del rope, workspace, candidate, gates, source_cache
            return r[bool].fail("preview broke")

        monkeypatch.setattr(
            infra_u.Infra,
            "preview_simple_removal_candidate",
            staticmethod(_preview_candidate),
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            validated = service._validated_project_reports(
                rope,
                (project_report,),
            )

        assert len(validated) == 1
        assert validated[0].removal_candidate_count == 0
        assert len(validated[0].removal_candidates) == 0
        assert len(validated[0].violations) == 1
        assert validated[0].violations_total == 1
        assert validated[0].violations[0].kind == "preview_rejected"
        assert validated[0].violations[0].description == "preview broke"

    def test_preview_simple_removal_candidate_skips_project_validate_on_refresh(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Preview cleanup keeps preserved indexes without revalidating Rope."""
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
        refresh_calls: list[tuple[bool, bool]] = []

        def _preview_source_writes(
            *args: object,
            **kwargs: object,
        ) -> tuple[bool, list[str]]:
            """Short-circuit protected preview writes for this unit test."""
            del args, kwargs
            return (True, [])

        original_refresh = FlextInfraRopeWorkspace.refresh

        def _tracking_refresh(
            rope: FlextInfraRopeWorkspace,
            *,
            preserve_indexes: bool = False,
            validate_project: bool = True,
        ) -> m.Infra.RopeWorkspaceSession:
            """Capture refresh flags used by preview cleanup."""
            refresh_calls.append((preserve_indexes, validate_project))
            return original_refresh(
                rope,
                preserve_indexes=preserve_indexes,
                validate_project=validate_project,
            )

        monkeypatch.setattr(
            FlextInfraUtilitiesProtectedEdit,
            "preview_source_writes",
            staticmethod(_preview_source_writes),
        )
        monkeypatch.setattr(
            FlextInfraRopeWorkspace,
            "refresh",
            _tracking_refresh,
        )

        with flext_infra.infra.rope_workspace(workspace_root) as rope:
            result = FlextInfraUtilitiesRefactorCensus.preview_simple_removal_candidate(
                rope,
                workspace_root,
                candidate,
                gates=("lint",),
            )

        assert result.unwrap() is True
        assert refresh_calls == [(True, False)]
