from __future__ import annotations

from pathlib import Path
from typing import TypeGuard

import tomlkit
from flext_tests import tm

from flext_core import r
from tests import t, u


def _is_str_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _rewrite_dep_paths(
    pyproject_path: Path,
    *,
    mode: str,
    internal_names: set[str],
    workspace_members: t.StrSequence = (),
    is_root: bool = False,
    dry_run: bool = False,
) -> r[t.StrSequence]:
    return u.Infra().rewrite_dep_paths(
        pyproject_path,
        mode=mode,
        internal_names=internal_names,
        workspace_members=workspace_members,
        is_root=is_root,
        dry_run=dry_run,
    )


class TestRewriteDepPaths:
    def test_rewrite_dep_paths_success(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\ndependencies = ["flext-core @ file://.flext-deps/flext-core"]\n',
        )
        result = _rewrite_dep_paths(
            pyproject,
            mode="workspace",
            internal_names={"flext-core"},
            is_root=True,
        )
        tm.ok(result)
        assert len(result.value) > 0

    def test_rewrite_dep_paths_dry_run(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        original = (
            '[project]\ndependencies = ["flext-core @ file://.flext-deps/flext-core"]\n'
        )
        pyproject.write_text(original)
        result = _rewrite_dep_paths(
            pyproject,
            mode="workspace",
            internal_names={"flext-core"},
            is_root=True,
            dry_run=True,
        )
        tm.ok(result)
        tm.that(pyproject.read_text(), eq=original)

    def test_rewrite_dep_paths_no_changes(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["requests>=2.0.0"]\n')
        result = _rewrite_dep_paths(
            pyproject,
            mode="workspace",
            internal_names={"flext-core"},
            is_root=True,
        )
        tm.that(tm.ok(result), eq=[])

    def test_rewrite_dep_paths_read_failure(self, tmp_path: Path) -> None:
        result = _rewrite_dep_paths(
            tmp_path / "pyproject.toml",
            mode="workspace",
            internal_names={"flext-core"},
            is_root=True,
        )
        tm.fail(result)

    def test_rewrite_dep_paths_write_failure(
        self,
        tmp_path: Path,
    ) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\ndependencies = ["flext-core @ file://.flext-deps/flext-core"]\n',
            encoding="utf-8",
        )
        pyproject.chmod(0o400)

        tm.fail(
            _rewrite_dep_paths(
                pyproject,
                mode="workspace",
                internal_names={"flext-core"},
                is_root=True,
            ),
            has="TOML write error",
        )


def test_rewrite_dep_paths_with_internal_names(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\ndependencies = ["flext-core @ file:.flext-deps/flext-core"]\n',
    )
    result = _rewrite_dep_paths(
        pyproject,
        mode="workspace",
        internal_names={"flext-core"},
        is_root=False,
        dry_run=False,
    )
    tm.ok(result)
    assert len(result.value) > 0


def test_rewrite_dep_paths_dry_run(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    original = '[project]\ndependencies = ["flext-core @ file:../flext-core"]\n'
    pyproject.write_text(original)
    tm.ok(
        _rewrite_dep_paths(
            pyproject,
            mode="workspace",
            internal_names={"flext-core"},
            is_root=False,
            dry_run=True,
        ),
    )
    tm.that(pyproject.read_text(), eq=original)


def test_rewrite_dep_paths_read_failure(tmp_path: Path) -> None:
    tm.fail(
        _rewrite_dep_paths(
            tmp_path / "pyproject.toml",
            mode="workspace",
            internal_names={"flext-core"},
            is_root=False,
            dry_run=False,
        ),
    )


def test_rewrite_dep_paths_with_no_deps(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.poetry.dependencies]\npython = "^3.13"')
    tm.ok(
        _rewrite_dep_paths(
            pyproject,
            mode="poetry",
            internal_names=set(),
            dry_run=True,
        ),
    )


def test_root_workspace_sources_cover_all_workspace_members(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        (
            "[project]\n"
            'dependencies = ["flext-core>=0.1.0"]\n'
            "[tool.uv.sources]\n"
            "flexcore = { workspace = true }\n"
        ),
        encoding="utf-8",
    )

    result = _rewrite_dep_paths(
        pyproject,
        mode="workspace",
        internal_names={"flext-api", "flext-core", "flexcore"},
        workspace_members=("flext-api", "flext-core"),
        is_root=True,
    )

    tm.ok(result)
    rendered = tomlkit.parse(pyproject.read_text(encoding="utf-8")).unwrap()
    assert _is_str_object_dict(rendered)
    rendered_map = rendered
    tool_table_raw = rendered_map["tool"]
    assert _is_str_object_dict(tool_table_raw)
    tool_table = tool_table_raw
    uv_table_raw_obj = tool_table["uv"]
    assert _is_str_object_dict(uv_table_raw_obj)
    uv_table_raw = uv_table_raw_obj
    sources_raw_obj = uv_table_raw["sources"]
    assert _is_str_object_dict(sources_raw_obj)
    sources_raw = sources_raw_obj
    sources: dict[str, dict[str, bool]] = {}
    for raw_name, raw_source_obj in sources_raw.items():
        assert _is_str_object_dict(raw_source_obj)
        raw_source = raw_source_obj
        workspace_raw_obj = raw_source["workspace"]
        assert isinstance(workspace_raw_obj, bool)
        workspace_raw = workspace_raw_obj
        sources[raw_name] = {"workspace": workspace_raw}
    tm.that(sorted(sources), eq=["flext-api", "flext-core"])
    flext_api_source = sources["flext-api"]
    flext_core_source = sources["flext-core"]
    tm.that(flext_api_source["workspace"], eq=True)
    tm.that(flext_core_source["workspace"], eq=True)
