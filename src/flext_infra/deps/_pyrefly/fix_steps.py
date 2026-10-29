"""Cohesive pyrefly-config fix-step mixin for FlextInfraConfigFixer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import TYPE_CHECKING

from flext_infra import c, r, t, u
from flext_infra.deps import FlextInfraExtraPathsManager

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import m, p


class FlextInfraDepsPyreflyFixSteps:
    """Mixin holding the three cohesive pyrefly fix-steps."""

    _repository_root: Path

    def _sync_search_path(
        self,
        pyrefly: MutableMapping[str, t.JsonValue],
        project_dir: Path,
    ) -> p.Result[Sequence[str]]:
        """Synchronize tool.pyrefly.search-path from YAML rules.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

        """
        search_raw = pyrefly.get(c.Infra.SEARCH_PATH)
        if not isinstance(search_raw, list):
            return r[Sequence[str]].ok(())
        validated = u.validate_value(u.json_list_adapter(), list(search_raw))
        if validated.failure:
            return r[Sequence[str]].fail_op("validate-search-path", validated.error)
        current_search = [
            path_item for path_item in validated.value if isinstance(path_item, str)
        ]
        expected_search = FlextInfraExtraPathsManager(
            repository_root=self._repository_root,
        ).pyrefly_search_paths(project_dir=project_dir)
        if current_search != expected_search:
            pyrefly[c.Infra.SEARCH_PATH] = u.Cli.toml_array(expected_search)
            return r[Sequence[str]].ok(["synchronized search-path from YAML rules"])
        return r[Sequence[str]].ok(())

    def _sync_project_includes(
        self,
        pyrefly: MutableMapping[str, t.JsonValue],
        project_dir: Path,
        *,
        is_root: bool,
    ) -> p.Result[Sequence[str]]:
        """Synchronize tool.pyrefly.project-includes from canonical path rules.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

        """
        includes_raw = pyrefly.get(c.Infra.PROJECT_INCLUDES)
        if not isinstance(includes_raw, list):
            return r[Sequence[str]].ok(())
        validated = u.validate_value(u.json_list_adapter(), list(includes_raw))
        if validated.failure:
            return r[Sequence[str]].fail_op(
                "validate-project-includes",
                validated.error,
            )
        current_includes = [
            path_item for path_item in validated.value if isinstance(path_item, str)
        ]
        expected_includes = FlextInfraExtraPathsManager(
            repository_root=self._repository_root,
        ).pyrefly_project_includes(project_dir=project_dir, is_root=is_root)
        if current_includes != expected_includes:
            pyrefly[c.Infra.PROJECT_INCLUDES] = u.Cli.toml_array(expected_includes)
            return r[Sequence[str]].ok([
                "synchronized project-includes from YAML rules",
            ])
        return r[Sequence[str]].ok(())

    @staticmethod
    def _strip_ignored_sub_configs(
        pyrefly: MutableMapping[str, t.JsonValue],
    ) -> p.Result[tuple[Sequence[str], bool]]:
        """Drop ignore=true entries from tool.pyrefly.sub-config.

        Returns:
            The resulting ``p.Result[tuple[Sequence[str], bool]]``.

        """
        sub_configs = pyrefly.get(c.Infra.SUB_CONFIG)
        if not isinstance(sub_configs, list):
            return r[tuple[Sequence[str], bool]].ok(((), False))
        validated_configs: p.Result[t.JsonList] = u.validate_value(
            t.Infra.INFRA_SEQ_ADAPTER,
            sub_configs,
        )
        if validated_configs.failure:
            return r[tuple[Sequence[str], bool]].fail_op(
                "validate-sub-configs",
                validated_configs.error,
            )
        configs: Sequence[t.JsonValue] = validated_configs.value
        fixes: MutableSequence[str] = []
        removed_ignore = False
        new_configs: MutableSequence[t.JsonValue] = []
        for conf in configs:
            conf_out: t.JsonValue = conf
            if isinstance(conf, Mapping):
                validated_conf: p.Result[t.JsonMapping] = u.validate_value(
                    t.Infra.INFRA_MAPPING_ADAPTER,
                    conf,
                )
                if validated_conf.failure:
                    return r[tuple[Sequence[str], bool]].fail_op(
                        "validate-pyrefly-sub-config",
                        validated_conf.error,
                    )
                conf_map = validated_conf.value
                conf_out = dict(conf_map)
            else:
                new_configs.append(conf_out)
                continue
            if conf_map.get(c.Infra.IGNORE) is True:
                removed_ignore = True
                matches = conf_map.get("matches", c.Infra.DEFAULT_UNKNOWN)
                fixes.append(f"removed ignore=true sub-settings for '{matches}'")
                continue
            new_configs.append(conf_out)
        if len(new_configs) != len(configs):
            pyrefly[c.Infra.SUB_CONFIG] = list(
                u.json_list_adapter().validate_python(new_configs),
            )
        return r[tuple[Sequence[str], bool]].ok((fixes, removed_ignore))

    @staticmethod
    def _sync_project_excludes(
        pyrefly: MutableMapping[str, t.JsonValue],
        *,
        codegen: m.Infra.CodegenConfigSpec,
        tool_config: m.Infra.ToolConfigDocument,
    ) -> p.Result[Sequence[str]]:
        """Synchronize tool.pyrefly.project-excludes from YAML rules.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

        """
        current_excludes: Sequence[str] = []
        excludes = pyrefly.get(c.Infra.PROJECT_EXCLUDES)
        if isinstance(excludes, list):
            validated = u.validate_value(u.json_list_adapter(), list(excludes))
            if validated.failure:
                return r[Sequence[str]].fail_op(
                    "validate-project-excludes",
                    validated.error,
                )
            current_excludes = [str(value) for value in validated.value]
        expected_excludes = u.Infra.pyrefly_project_excludes(
            u.Infra.native_tool_strings(
                tool_config,
                c.Infra.PYREFLY,
                c.Infra.PROJECT_EXCLUDES,
            ),
            codegen=codegen,
        )
        if current_excludes != expected_excludes:
            pyrefly[c.Infra.PROJECT_EXCLUDES] = u.Cli.toml_array(expected_excludes)
            return r[Sequence[str]].ok([
                "synchronized project-excludes from YAML rules",
            ])
        return r[Sequence[str]].ok(())


__all__: list[str] = ["FlextInfraDepsPyreflyFixSteps"]
