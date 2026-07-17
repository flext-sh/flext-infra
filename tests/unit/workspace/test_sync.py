"""Public sync service tests for workspace synchronization."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.constants import c
from flext_infra.validate.manual_command import FlextInfraManualCommandValidator
from flext_infra.workspace.sync import FlextInfraSyncService
from tests import m
from tests import t
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from tests import p


def _stub_gen(content: str, *, fail: bool = False) -> FlextInfraBaseMkGenerator:
    class _Gen(FlextInfraBaseMkGenerator):
        @override
        def generate_basemk(
            self, settings: m.Infra.BaseMkConfig | t.ScalarMapping | None = None
        ) -> p.Result[str]:
            _ = self
            _ = settings
            return r[str].fail(content) if fail else r[str].ok(content)

    return _Gen(workspace_root=Path.cwd())


def _write_project(project_root: Path, name: str) -> None:
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            f'name = "{name}"\n'
            'version = "0.1.0"\n'
            'description = "Demo project"\n'
            'requires-python = ">=3.13"\n'
        ),
        encoding="utf-8",
    )


def _write_workspace(workspace_root: Path) -> tuple[Path, Path]:
    demo_a = workspace_root / "demo-a"
    demo_b = workspace_root / "demo-b"
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "pyproject.toml").write_text(
        ('[project]\nname = "workspace-root"\nversion = "0.1.0"\n'), encoding="utf-8"
    )
    member_records = "".join(
        (
            f"  - name: {name}\n"
            f"    distribution: {name}\n"
            "    provider: flext-sh\n"
            f"    url: https://github.com/flext-sh/{name}.git\n"
            "    branch: main\n"
            f"    path: {name}\n"
            "    role: workspace-member\n"
            "    state: active\n"
            "    profile: workspace-member\n"
            "    checkout: submodule\n"
            "    codegen: conform\n"
            "    package: true\n"
            "    editable: true\n"
            "    read_only: false\n"
        )
        for name in ("demo-a", "demo-b")
    )
    config_dir = workspace_root / "config"
    config_dir.mkdir()
    (config_dir / "workspace.yaml").write_text(
        (
            "version: 2\n"
            "name: workspace-root\n"
            "repository:\n"
            "  name: workspace-root\n"
            "  distribution: workspace-root\n"
            "  provider: flext-sh\n"
            "  url: https://github.com/flext-sh/workspace-root.git\n"
            "  branch: main\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  profile: workspace-root\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            f"members:\n{member_records}"
            "content_only: []\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )
    for project_root, distribution in ((demo_a, "demo-a"), (demo_b, "demo-b")):
        _write_project(project_root, distribution)
        package_root = project_root / "src" / distribution.replace("-", "_")
        package_root.mkdir(parents=True)
        (package_root / "__init__.py").write_text("", encoding="utf-8")
    return demo_a, demo_b


def _error_text[ValueT](result: p.Result[ValueT]) -> str:
    return result.error or ""


class TestsFlextInfraWorkspaceSync:
    """Behavior contract for test_sync."""

    def test_sync_result_serializes_json_safe_metadata(self, tmp_path: Path) -> None:
        """Serialize path and timestamp metadata into JSON-safe values."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        payload = m.Infra.SyncResult(
            files_changed=2,
            source=source,
            target=target,
            timestamp=datetime(2026, 5, 4, tzinfo=UTC),
        )

        tm.that(
            payload.model_dump(mode="json"),
            eq={
                "files_changed": 2,
                "source": str(source),
                "target": str(target),
                "timestamp": "2026-05-04T00:00:00+00:00",
            },
        )
        tm.that(
            u.normalize_to_json_value(payload),
            eq={
                "files_changed": 2,
                "source": str(source),
                "target": str(target),
                "timestamp": "2026-05-04T00:00:00+00:00",
            },
        )

    def test_sync_generates_basemk_gitignore_and_makefile(self, tmp_path: Path) -> None:
        """Generate canonical project files and strict editor settings."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        ).execute()

        tm.ok(result)
        tm.that(result.value.files_changed, gt=0)
        tm.that((project_root / "base.mk").exists(), eq=False)
        tm.that((project_root / ".gitignore").exists(), eq=True)
        tm.that((project_root / "Makefile").exists(), eq=True)
        settings = u.Cli.json_read(project_root / ".vscode" / "settings.json").unwrap()
        tm.that(settings["python.analysis.typeCheckingMode"], eq="strict")
        overrides = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            settings["python.analysis.diagnosticSeverityOverrides"]
        )
        tm.that(overrides["reportUntypedBaseClass"], eq="none")

    def test_sync_dry_run_reports_changes_without_writing(self, tmp_path: Path) -> None:
        """Report pending changes without writing project files in dry-run mode."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        result = FlextInfraSyncService(
            canonical_root=project_root.parent, workspace_root=project_root
        ).execute()

        tm.ok(result)
        tm.that(result.value.files_changed, gt=0)
        tm.that((project_root / ".gitignore").exists(), eq=False)
        tm.that((project_root / ".envrc").exists(), eq=False)
        tm.that((project_root / ".mise.toml").exists(), eq=False)
        tm.that((project_root / ".vscode" / "settings.json").exists(), eq=False)
        tm.that((project_root / "Makefile").exists(), eq=False)

    def test_sync_uses_package_tests_dir_when_present(self, tmp_path: Path) -> None:
        """Point generated Makefiles at package-local tests when present."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        (project_root / "src" / "demo_project" / "tests").mkdir(parents=True)

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        ).execute()

        tm.ok(result)
        makefile_text = (project_root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile_text, has="TESTS_DIR ?= src/demo_project/tests")

    def test_sync_is_idempotent_on_second_run(self, tmp_path: Path) -> None:
        """Produce zero file changes when a synchronized project runs again."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        service = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        )

        first_result = service.execute()
        tm.ok(first_result)
        second_result = service.execute()

        tm.ok(second_result)
        tm.that(second_result.value.files_changed, eq=0)

    def test_sync_deduplicates_gitignore_managed_block(self, tmp_path: Path) -> None:
        """Collapse duplicate managed blocks while preserving manual entries."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        header = c.Infra.GITIGNORE_MANAGED_HEADER
        gitignore = project_root / ".gitignore"
        gitignore.write_text(
            f"custom.log\n\n{header}\n.direnv/\n\n"
            f"# keep manual ignore\n.venv/\n{header}\nbase.mk\n",
            encoding="utf-8",
        )
        service = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        )

        result = service.execute()
        second_result = service.execute()

        tm.ok(result)
        tm.ok(second_result)
        tm.that(second_result.value.files_changed, eq=0)
        synced = gitignore.read_text(encoding="utf-8")
        tm.that(synced.count(header), eq=1)
        tm.that(synced, has="custom.log\n")
        tm.that(synced, has="# keep manual ignore\n")
        for pattern in c.Infra.REQUIRED_GITIGNORE_ENTRIES:
            tm.that(synced.count(f"{pattern}\n"), eq=1)

    def test_sync_preserves_custom_vscode_settings(self, tmp_path: Path) -> None:
        """Preserve custom editor values while adding canonical diagnostics."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        settings_path = project_root / ".vscode" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        _ = settings_path.write_text(
            (
                "{\n"
                '  "editor.formatOnSave": true,\n'
                '  "python.analysis.diagnosticSeverityOverrides": {\n'
                '    "reportUnknownMemberType": "none",\n'
                "  },\n"
                "}\n"
            ),
            encoding="utf-8",
        )

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        ).execute()
        second_result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        ).execute()

        tm.ok(result)
        tm.ok(second_result)
        settings = u.Cli.json_read(settings_path).unwrap()
        tm.that(settings["editor.formatOnSave"], eq=True)
        overrides = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            settings["python.analysis.diagnosticSeverityOverrides"]
        )
        tm.that(overrides["reportUnknownMemberType"], eq="none")
        tm.that(overrides["reportUntypedBaseClass"], eq="none")
        tm.that(second_result.value.files_changed, eq=0)

    def test_sync_fails_when_workspace_root_is_missing(self, tmp_path: Path) -> None:
        """Return a typed failure when the requested workspace does not exist."""
        missing_root = tmp_path / "missing" / "workspace"

        result = FlextInfraSyncService(workspace_root=missing_root).execute()

        tm.fail(result)
        tm.that(_error_text(result), has="does not exist")

    def test_sync_fails_when_generator_fails(self, tmp_path: Path) -> None:
        """Propagate the typed base.mk generator failure."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")

        service = FlextInfraSyncService(
            canonical_root=project_root.parent, workspace_root=project_root
        )
        service.generator = _stub_gen("Generation failed", fail=True)
        result = service.execute()

        tm.fail(result)
        tm.that(_error_text(result), has="Generation failed")

    def test_sync_fails_when_gitignore_path_is_directory(self, tmp_path: Path) -> None:
        """Return a typed failure when the gitignore target is a directory."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        (project_root / ".gitignore").mkdir()

        result = FlextInfraSyncService(
            canonical_root=project_root.parent, workspace_root=project_root
        ).execute()

        tm.fail(result)
        tm.that(_error_text(result), has=".gitignore")

    def test_sync_workspace_root_also_syncs_child_projects(
        self, tmp_path: Path
    ) -> None:
        """Synchronize every configured child from the workspace root."""
        workspace_root = tmp_path / "workspace"
        demo_a, demo_b = _write_workspace(workspace_root)

        result = FlextInfraSyncService(
            canonical_root=workspace_root,
            workspace_root=workspace_root,
            apply_changes=True,
        ).execute()

        tm.ok(result)
        tm.that((workspace_root / "base.mk").exists(), eq=False)
        tm.that((workspace_root / "Makefile").exists(), eq=True)
        for project_root in (demo_a, demo_b):
            tm.that((project_root / "base.mk").exists(), eq=False)
            tm.that((project_root / "Makefile").exists(), eq=True)

    def test_sync_workspace_root_writes_pre_commit_config(self, tmp_path: Path) -> None:
        """Write the canonical pre-commit config for workspace roots."""
        workspace_root = tmp_path / "workspace"
        _ = _write_workspace(workspace_root)

        result = FlextInfraSyncService(
            canonical_root=workspace_root,
            workspace_root=workspace_root,
            apply_changes=True,
        ).execute()

        tm.ok(result)
        pre_commit_path = workspace_root / ".pre-commit-config.yaml"
        gitignore_text = (workspace_root / ".gitignore").read_text(encoding="utf-8")
        tm.that(
            pre_commit_path.read_text(encoding="utf-8").strip(),
            eq=(FlextInfraManualCommandValidator.render_pre_commit_config().strip()),
        )
        tm.that(gitignore_text, has="!.pre-commit-config.yaml")

    def test_sync_regenerates_project_makefile_without_legacy_passthrough(
        self, tmp_path: Path
    ) -> None:
        """Replace legacy Makefile content with the canonical generated surface."""
        project_root = tmp_path / "project"
        _write_project(project_root, "demo-project")
        (project_root / "Makefile").write_text(
            "# legacy custom target\ncustom-target:\n\t@echo legacy\n", encoding="utf-8"
        )

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace_root=project_root,
            apply_changes=True,
        ).execute()

        tm.ok(result)
        makefile_text = (project_root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile_text, lacks="custom-target")
        tm.that(makefile_text, has="-include custom.mk")
        tm.that((project_root / "custom.mk").exists(), eq=False)

    def test_atomic_write_ok(self, tmp_path: Path) -> None:
        """Write text atomically through the public CLI utility."""
        target = tmp_path / "test.txt"

        result = u.Cli.atomic_write_text_file(target, "test content")

        tm.ok(result)
        tm.that(result.value, eq=True)
        tm.that(target.read_text(encoding="utf-8"), eq="test content")

    def test_atomic_write_fails_when_parent_is_a_file(self, tmp_path: Path) -> None:
        """Return a typed failure when an atomic-write parent is a file."""
        blocked_parent = tmp_path / "occupied"
        blocked_parent.write_text("occupied", encoding="utf-8")

        result = u.Cli.atomic_write_text_file(blocked_parent / "test.txt", "content")

        tm.fail(result)
        tm.that(_error_text(result), has="ensure_dir")
