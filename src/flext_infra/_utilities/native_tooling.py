"""Validate and compose the declared native tool-option catalog.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sysconfig
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

from flext_cli import u

from flext_infra import m, p, r, t


class FlextInfraUtilitiesNativeTooling:
    """Own native option values without file-discovery or projection behavior."""

    @staticmethod
    def native_tool_search_path_admission(
        document: m.Infra.ToolConfigDocument,
        repository_root: Path,
    ) -> p.Result[bool]:
        """Check rooted native search paths once, without copying the typed document.

        Returns:
            Admission of source paths and actual installed dependency typing.

        """
        pending: list[tuple[str, t.JsonValue]] = [
            (key, value) for pairs in document.settings.values() for key, value in pairs
        ]
        pending.extend(
            (key, value)
            for override in document.tools.mypy.overrides
            for key, value in override.settings
        )
        pyright = document.tools.pyright.path_rules
        pyrefly = document.tools.pyrefly.path_rules
        pending.extend(
            ("search-path", path)
            for path in (
                pyright.source_dir,
                pyright.project_root,
                *pyright.env_dirs,
                *pyright.test_like_dirs,
                *(override.root for override in pyright.diagnostic_path_overrides),
                pyrefly.source_dir,
                pyrefly.project_root,
                *pyrefly.env_dirs,
                *pyrefly.workspace_include_child_env_dirs,
                *pyrefly.project_shared_search_paths,
            )
        )
        root = repository_root.resolve()
        installed_roots = tuple(
            Path(sysconfig.get_path(key)).resolve() for key in ("purelib", "platlib")
        )
        while pending:
            key, value = pending.pop()
            option = key.rsplit(".", 1)[-1].casefold().replace("-", "").replace("_", "")
            if isinstance(value, Mapping):
                pending.extend(value.items())
            elif isinstance(value, list):
                pending.extend((key, item) for item in value)
            elif isinstance(value, str) and (
                "path" in option
                or option in {"root", "sourcedir", "envdirs", "projectincludes"}
            ):
                for entry in value.replace("\\", "/").split(":"):
                    path = Path(entry).expanduser()
                    resolved = (path if path.is_absolute() else root / path).resolve()
                    if any(
                        resolved.is_relative_to(installed)
                        for installed in installed_roots
                    ):
                        continue
                    if any(
                        part in {"typings", "stubs"}
                        or part.endswith((".pyi", "-stubs"))
                        or "-stubs-" in part
                        for part in path.parts
                    ):
                        return r[bool].fail(
                            f"Local stub search roots are forbidden: {key}={value}"
                        )
        return r[bool].ok(value=True)

    @staticmethod
    def configuration_pairs(
        entries: t.SequenceOf[t.Pair[str, t.JsonValue]],
    ) -> t.JsonDict:
        """Elect ordered pairs and isolate their mutable values from consumers.

        Returns:
            The last declared value per key, preserving nested array order.

        """
        return deepcopy(dict(entries))

    @staticmethod
    def native_tool_settings(
        document: m.Infra.ToolConfigDocument, table: str
    ) -> t.JsonDict:
        """Read a declared native table without inventing an absent configuration.

        Returns:
            The elected JSON-compatible options for the declared table.

        """
        return FlextInfraUtilitiesNativeTooling.configuration_pairs(
            document.settings[table]
        )

    @staticmethod
    def native_tool_configuration(
        document: m.Infra.ToolConfigDocument, root: str
    ) -> t.JsonDict:
        """Compose a declared native root and its nested option tables.

        Returns:
            The elected tool configuration with native nested table structure.

        Raises:
            KeyError: If the requested root has no declared option tables.

        """
        result: t.JsonDict = {}
        selected = False
        for table, entries in sorted(document.settings.items()):
            owner, separator, nested = table.partition(".")
            if owner != root:
                continue
            selected = True
            target = u.Cli.toml_mapping_ensure_path(
                result, nested.split(".") if separator else ()
            )
            target.update(FlextInfraUtilitiesNativeTooling.configuration_pairs(entries))
        if not selected:
            raise KeyError(root)
        return result

    @staticmethod
    def native_tool_setting[TValue](
        document: m.Infra.ToolConfigDocument,
        table: str,
        key: str,
        target: t.TypeForm[TValue],
    ) -> TValue:
        """Validate one native option, preserving lookup and validation failures.

        Returns:
            The configured value validated against the consumer's type.

        """
        return u.type_adapter(target).validate_python(
            dict(document.settings[table])[key], strict=True
        )

    @staticmethod
    def native_tool_strings(
        document: m.Infra.ToolConfigDocument, table: str, key: str
    ) -> t.StrSequence:
        """Validate one native string-array option.

        Returns:
            The configured strings, preserving lookup and validation failures.

        """
        return FlextInfraUtilitiesNativeTooling.native_tool_setting(
            document, table, key, t.TypeForm(t.StrSequence)
        )


__all__ = ["FlextInfraUtilitiesNativeTooling"]
