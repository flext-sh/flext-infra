from __future__ import annotations

from pathlib import Path
from typing import TypeGuard

import tomlkit
from flext_tests import tm

from tests import c, m, u


def _is_str_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


# Tests below call ``u.Infra().rewrite_dep_paths`` directly with the canonical
# Pydantic 2 ``m.Infra.PathSyncCommand`` model — no local adapter, no manual
# kwarg validation. ``is_root`` is implicitly conveyed by setting
# ``workspace`` to ``pyproject.parent`` (the canonical method derives the
# flag itself by comparing ``pyproject_path`` against
# ``command.workspace_path / pyproject.toml``); non-root tests point
# ``workspace`` at ``pyproject.parent.parent``. Pydantic validates every
# ``PathSyncCommand`` field — including the ``mode`` enum — at construction
# time, so the tests rely on the model's own validation rather than custom
# per-test kwarg handling.


class TestsFlextInfraDepsPathSyncRewriteDeps:
    def test_rewrite_dep_paths_success(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\ndependencies = ["flext-core @ file://.flext-deps/flext-core"]\n',
        )
        result = u.Infra().rewrite_dep_paths(
            pyproject,
            command=m.Infra.PathSyncCommand(
                mode=c.Infra.PathSyncMode.WORKSPACE,
                workspace=str(tmp_path),
                apply=True,
            ),
            internal_names={"flext-core"},
            workspace_members=(),
        )
        tm.ok(result)
        assert len(result.value) > 0

    def test_rewrite_dep_paths_dry_run(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        original = (
            '[project]\ndependencies = ["flext-core @ file://.flext-deps/flext-core"]\n'
        )
        pyproject.write_text(original)
        result = u.Infra().rewrite_dep_paths(
            pyproject,
            command=m.Infra.PathSyncCommand(
                mode=c.Infra.PathSyncMode.WORKSPACE,
                workspace=str(tmp_path),
                apply=False,
            ),
            internal_names={"flext-core"},
            workspace_members=(),
        )
        tm.ok(result)
        tm.that(pyproject.read_text(), eq=original)

    def test_rewrite_dep_paths_no_changes(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["requests>=2.0.0"]\n')
        result = u.Infra().rewrite_dep_paths(
            pyproject,
            command=m.Infra.PathSyncCommand(
                mode=c.Infra.PathSyncMode.WORKSPACE,
                workspace=str(tmp_path),
                apply=True,
            ),
            internal_names={"flext-core"},
            workspace_members=(),
        )
        tm.that(tm.ok(result), empty=True)

    def test_rewrite_dep_paths_read_failure(self, tmp_path: Path) -> None:
        result = u.Infra().rewrite_dep_paths(
            tmp_path / "pyproject.toml",
            command=m.Infra.PathSyncCommand(
                mode=c.Infra.PathSyncMode.WORKSPACE,
                workspace=str(tmp_path),
                apply=True,
            ),
            internal_names={"flext-core"},
            workspace_members=(),
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
            u.Infra().rewrite_dep_paths(
                pyproject,
                command=m.Infra.PathSyncCommand(
                    mode=c.Infra.PathSyncMode.WORKSPACE,
                    workspace=str(tmp_path),
                    apply=True,
                ),
                internal_names={"flext-core"},
                workspace_members=(),
            ),
            has="TOML write error",
        )

    def test_rewrite_dep_paths_with_internal_names(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\ndependencies = ["flext-core @ file:.flext-deps/flext-core"]\n',
        )
        result = u.Infra().rewrite_dep_paths(
            pyproject,
            command=m.Infra.PathSyncCommand(
                mode=c.Infra.PathSyncMode.WORKSPACE,
                workspace=str(tmp_path.parent),
                apply=True,
            ),
            internal_names={"flext-core"},
            workspace_members=(),
        )
        tm.ok(result)
        assert len(result.value) > 0

    def test_rewrite_dep_paths_dry_run_non_root(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        original = '[project]\ndependencies = ["flext-core @ file:../flext-core"]\n'
        pyproject.write_text(original)
        tm.ok(
            u.Infra().rewrite_dep_paths(
                pyproject,
                command=m.Infra.PathSyncCommand(
                    mode=c.Infra.PathSyncMode.WORKSPACE,
                    workspace=str(tmp_path.parent),
                    apply=False,
                ),
                internal_names={"flext-core"},
                workspace_members=(),
            ),
        )
        tm.that(pyproject.read_text(), eq=original)

    def test_rewrite_dep_paths_read_failure_non_root(self, tmp_path: Path) -> None:
        tm.fail(
            u.Infra().rewrite_dep_paths(
                tmp_path / "pyproject.toml",
                command=m.Infra.PathSyncCommand(
                    mode=c.Infra.PathSyncMode.WORKSPACE,
                    workspace=str(tmp_path.parent),
                    apply=True,
                ),
                internal_names={"flext-core"},
                workspace_members=(),
            ),
        )

    def test_rewrite_dep_paths_with_no_deps(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry.dependencies]\npython = "^3.13"')
        tm.ok(
            u.Infra().rewrite_dep_paths(
                pyproject,
                command=m.Infra.PathSyncCommand(
                    mode=c.Infra.PathSyncMode.STANDALONE,
                    workspace=str(tmp_path.parent),
                    apply=False,
                ),
                internal_names=set(),
                workspace_members=(),
            ),
        )

    def test_root_workspace_sources_cover_all_workspace_members(
        self, tmp_path: Path
    ) -> None:
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

        result = u.Infra().rewrite_dep_paths(
            pyproject,
            command=m.Infra.PathSyncCommand(
                mode=c.Infra.PathSyncMode.WORKSPACE,
                workspace=str(tmp_path),
                apply=True,
            ),
            internal_names={"flext-api", "flext-core", "flexcore"},
            workspace_members=("flext-api", "flext-core"),
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
