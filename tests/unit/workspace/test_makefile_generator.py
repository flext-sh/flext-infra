"""Workspace Makefile generator tests through the public generator API."""

from __future__ import annotations

import subprocess
from pathlib import Path

from flext_infra import FlextInfraWorkspaceMakefileGenerator


def _write_workspace_root(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "pyproject.toml").write_text(
        "[project]\nname='workspace-root'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    return workspace_root


def _assert_contains_all(text: str, parts: list[str]) -> None:
    for part in parts:
        assert part in text


def test_workspace_makefile_generator_sanitizes_orchestrator_env(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    _assert_contains_all(
        makefile_text,
        [
            'WORKSPACE_PYTHON := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(WORKSPACE_PYTHONPATH)" $(PY)',
            'WORKSPACE_FLEXT_INFRA := FLEXT_WORKSPACE_ROOT="$(CURDIR)" $(WORKSPACE_PYTHON) -m flext_infra',
            "WORKSPACE_INFRA_WORKSPACE := $(WORKSPACE_FLEXT_INFRA) workspace",
            "ORCHESTRATOR := $(WORKSPACE_INFRA_WORKSPACE) orchestrate",
            "ORCHESTRATOR_PROJECTS :=",
            "--projects $(proj)",
        ],
    )


def test_workspace_makefile_generator_declares_canonical_workspace_variables(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    _assert_contains_all(
        makefile_text,
        [
            "PROJECT ?=",
            "PROJECTS ?=",
            "DEPS_REPORT ?= 1",
            "PR_BRANCH ?= 0.1.0",
            "WORKSPACE_INFRA_DEPS := $(WORKSPACE_FLEXT_INFRA) deps",
            "WORKSPACE_INFRA_MAINTENANCE := $(WORKSPACE_FLEXT_INFRA) maintenance run",
            "WORKSPACE_INFRA_RELEASE := $(WORKSPACE_FLEXT_INFRA) release run",
            "WORKSPACE_INFRA_VALIDATE := $(WORKSPACE_FLEXT_INFRA) validate",
            "WORKSPACE_INFRA_GITHUB := $(WORKSPACE_FLEXT_INFRA) github",
        ],
    )


def test_workspace_makefile_generator_reuses_mod_and_boot_feedback(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    assert makefile_text.count("$(MAKE) mod") == 1
    _assert_contains_all(
        makefile_text,
        [
            "Run 'make boot'.",
            "Run 'make boot' first to create the environment.",
            "re-run: make boot",
        ],
    )


def test_workspace_makefile_generator_declares_workspace_boot_separation(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    _assert_contains_all(
        makefile_text,
        [
            "FLEXT_PROJECTS :=",
            "WORKSPACE_PROJECTS :=",
            "ATTACHABLE_PROJECTS :=",
            "tool.flext.workspace or tool.uv.workspace",
            'docs_path = root / "docs" / "docs_config.json"',
            'gitmodules = root / ".gitmodules"',
            "path not in excluded",
            "independent project (no workspace writes)",
            "attach-only project (outside uv workspace)",
            'uv pip install --python "$(PY)" --editable "$$proj[dev]" --no-sources --no-deps',
            '$(MAKE) val VALIDATE_SCOPE=workspace PROJECTS="$(WORKSPACE_PROJECTS)"',
        ],
    )


def test_workspace_makefile_generator_does_not_persist_external_project_names(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    assert "algar-oud-mig" not in makefile_text
    assert "gruponos-meltano-native" not in makefile_text


def test_workspace_makefile_generator_emits_parseable_discovery_commands(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    process = subprocess.run(
        ["make", "-C", str(workspace_root), "--dry-run", "help"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert process.returncode == 0


def test_workspace_makefile_generator_uses_check_only_for_maintenance_validation(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    _assert_contains_all(
        makefile_text,
        ["$(WORKSPACE_INFRA_MAINTENANCE) --check-only || exit 1"],
    )


def test_workspace_makefile_generator_limits_absolute_path_scan_to_sources(
    tmp_path: Path,
) -> None:
    workspace_root = _write_workspace_root(tmp_path)

    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    assert result.success, result.error
    makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

    _assert_contains_all(
        makefile_text,
        [
            "git grep -nE '/home/.*/flext|file:///home/.*/flext' -- '*.py' '**/*.py' '*.toml' '**/*.toml' '*.yml' '**/*.yml' '*.yaml' '**/*.yaml' '*.json' '**/*.json' '.gitignore' 'base.mk' '**/base.mk' ':!.planning/**' ':!.reports/**' ':!.sisyphus/**' ':!docs/**'",
        ],
    )
