"""Dependency typings analysis + container-value conversion helpers for detection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.deps import FlextInfraDependencyDetectionRunnersMixin


class FlextInfraDependencyDetectionAnalysis(FlextInfraDependencyDetectionRunnersMixin):
    """Typings analysis + conversion helpers composed with the tool-runner mixin."""

    @staticmethod
    def _read_plain(path: Path) -> p.Result[t.JsonMapping]:
        """Read one TOML document as a plain JSON mapping.

        Returns:
            The resulting ``p.Result[t.JsonMapping]``.

        """
        plain_result = u.Cli.toml_read_json(path)
        if plain_result.failure:
            return r[t.JsonMapping].from_failure(plain_result)
        return r[t.JsonMapping].ok(
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(plain_result.value),
        )

    def read_current_typings_from_pyproject(
        self,
        project_path: Path,
        *,
        include_dev: bool = True,
    ) -> t.StrSequence:
        """Read CUSTOM typing requirements and the canonical development group.

        Returns:
            The resulting ``t.StrSequence``.

        Raises:
            RuntimeError: If failed to read.
            ValueError: If Dependency requirement must not be blank in.

        """
        pyproject = project_path / c.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return []
        read_result = self._read_plain(pyproject)
        if read_result.failure:
            msg = f"failed to read {pyproject}: {read_result.error}"
            raise RuntimeError(msg)
        data = read_result.value
        project = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
            data.get(c.Infra.PROJECT, {}),
        )
        optional = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
            project.get(c.Infra.OPTIONAL_DEPENDENCIES, {}),
        )
        requirements = list(
            t.Infra.STR_SEQ_ADAPTER.validate_python(optional.get(c.Infra.TYPINGS, [])),
        )
        if include_dev:
            groups = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                data.get(c.Infra.DEPENDENCY_GROUPS, {}),
            )
            requirements.extend(
                t.Infra.STR_SEQ_ADAPTER.validate_python(groups.get(c.Infra.DEV, [])),
            )
        names: set[str] = set()
        for spec in requirements:
            name = u.Infra.dep_name(spec)
            if name is None:
                msg = f"Dependency requirement must not be blank in {pyproject}"
                raise ValueError(msg)
            names.add(name)
        return sorted(names)

    def _project_table(
        self,
        project_path: Path,
    ) -> p.Result[t.Pair[Path, t.JsonMapping]]:
        """Read one project's pyproject once, as a plain mapping, with its path.

        Returns:
            The resulting ``p.Result[t.Pair[Path, t.JsonMapping]]``.

        """
        pyproject = project_path / c.PYPROJECT_FILENAME
        read_result = self._read_plain(pyproject)
        if read_result.failure:
            return r[t.Pair[Path, t.JsonMapping]].fail_op(
                f"read {pyproject}",
                read_result.error,
            )
        return r[t.Pair[Path, t.JsonMapping]].ok((pyproject, read_result.value))

    def untyped_imports_followed(self, project_path: Path) -> p.Result[bool]:
        """Return the governed mypy ``follow_untyped_imports`` policy for a project.

        The policy is read from the typed tooling config the pyproject
        projection renders. A project whose own mypy table declares otherwise
        is a policy conflict, never a second source of truth. An absent key
        carries mypy's own default on both sides.

        Returns:
            The governed mypy ``follow_untyped_imports`` policy for a project.

        """
        key = c.Infra.MYPY_FOLLOW_UNTYPED_IMPORTS
        selected = u.Infra.load_tooling_inputs(project_path)
        if selected.failure:
            return r[bool].from_failure(selected)
        options = u.Infra.native_tool_settings(selected.value.document, c.Infra.MYPY)
        governed = (
            u.Infra.native_tool_setting(
                selected.value.document, c.Infra.MYPY, key, bool
            )
            if key in options
            else c.Infra.MYPY_FOLLOW_UNTYPED_IMPORTS_DEFAULT
        )
        table = self._project_table(project_path)
        if table.failure:
            return r[bool].from_failure(table)
        pyproject, data = table.value
        tool = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(data.get(c.Infra.TOOL, {}))
        mypy = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(tool.get(c.Infra.MYPY, {}))
        declared = u.type_adapter(bool).validate_python(
            mypy.get(key, c.Infra.MYPY_FOLLOW_UNTYPED_IMPORTS_DEFAULT),
            strict=True,
        )
        if declared != governed:
            return r[bool].fail(
                f"mypy {key} policy conflict in {pyproject}: the project declares "
                f"{declared!r}, the governed tooling policy declares {governed!r}; "
                "regenerate the projection with make gen",
            )
        return r[bool].ok(governed)

    def analyze_required_typings(
        self,
        project_path: Path,
        limits_path: Path | None = None,
    ) -> p.Result[m.Infra.TypingsReport]:
        """Analyze project and generate typing stubs requirements report.

        Stub discovery uses its own native invocation, independently of
        normal checking's policy for following untyped implementations.

        Returns:
            The resulting ``p.Result[m.Infra.TypingsReport]``.

        """
        followed = self.untyped_imports_followed(project_path)
        if followed.failure:
            return r[m.Infra.TypingsReport].from_failure(followed)
        limits = self.load_dependency_limits(limits_path)
        exclude_set = self._typing_excludes(limits)
        hints_result = self.run_mypy_stub_hints(project_path)
        if hints_result.failure:
            return r[m.Infra.TypingsReport].from_failure(hints_result)
        native = hints_result.value
        hinted, missing_modules = native.hinted, native.missing_modules
        required_set = self._required_set(hinted, missing_modules, limits) - exclude_set
        current = self.read_current_typings_from_pyproject(project_path)
        current_set = set(current)
        python_cfg = limits.get(c.Infra.PYTHON)
        version_val = (
            python_cfg.get(c.Infra.VERSION) if isinstance(python_cfg, Mapping) else None
        )
        python_version = str(version_val) if version_val is not None else None
        report = m.Infra.TypingsReport(
            required_packages=sorted(required_set),
            hinted=hinted,
            missing_modules=missing_modules,
            untyped_modules=tuple(
                module
                for module in native.untyped_modules
                if self.module_to_types_package(module, limits) is None
            ),
            current=current,
            to_add=sorted(required_set - current_set),
            to_remove=(
                []
                if followed.value
                else sorted(
                    set(
                        self.read_current_typings_from_pyproject(
                            project_path,
                            include_dev=False,
                        ),
                    )
                    - required_set,
                )
            ),
            limits_applied=bool(limits),
            python_version=python_version,
            untyped_imports_followed=followed.value,
        )
        return r[m.Infra.TypingsReport].ok(report)

    @staticmethod
    def _typing_excludes(limits: t.MappingKV[str, t.JsonValue]) -> t.Infra.StrSet:
        """Read the typing-library exclusion set from the limits document.

        Returns:
            The declared typing-library exclusions.

        """
        typing_libraries = limits.get(c.Infra.TYPING_LIBRARIES)
        if isinstance(typing_libraries, Mapping):
            excluded = typing_libraries.get(c.Infra.EXCLUDE)
            if isinstance(excluded, list):
                return {str(e) for e in excluded}
        return set()

    def _required_set(
        self,
        hinted: t.StrSequence,
        missing_modules: t.StrSequence,
        limits: t.MappingKV[str, t.JsonValue],
    ) -> t.Infra.StrSet:
        """Derive the required typing packages from the stub hints.

        Returns:
            The required packages set.

        """
        required: t.Infra.StrSet = set(hinted)
        for module_name in missing_modules:
            package = self.module_to_types_package(module_name, limits)
            if package:
                required.add(package)
        return required

    def load_dependency_limits(
        self,
        limits_path: Path | None = None,
    ) -> t.MappingKV[str, t.JsonValue]:
        """Load dependency limits configuration from TOML file.

        Returns:
            The resulting ``t.MappingKV[str, t.JsonValue]``.

        Raises:
            RuntimeError: If failed to load dependency limits from.

        """
        path = (
            limits_path
            or Path(__file__).resolve().parent / c.Infra.DEPENDENCY_LIMITS_FILENAME
        )
        result = self._read_plain(path)
        if result.failure:
            msg = f"failed to load dependency limits from {path}: {result.error}"
            raise RuntimeError(msg)
        return result.value

    @staticmethod
    def module_to_types_package(
        module_name: str,
        limits: t.MappingKV[str, t.JsonValue],
    ) -> str | None:
        """Map a module name to its corresponding types-* package.

        Returns:
            The resulting ``str | None``.

        """
        root = module_name.split(".", 1)[0]
        if root.startswith(c.Infra.INTERNAL_PREFIXES):
            return None
        typing_libraries = limits.get(c.Infra.TYPING_LIBRARIES)
        if isinstance(typing_libraries, Mapping):
            module_to_package = typing_libraries.get(c.Infra.MODULE_TO_PACKAGE)
            if isinstance(module_to_package, Mapping) and root in module_to_package:
                value = module_to_package.get(root)
                return str(value) if value is not None else None
        # 5a7d1d710 removed the hardcoded module->types-* table: the declared
        # typing_libraries.module_to_package config is the only source, so an
        # undeclared module is unknown rather than a guessed types-* name.
        return None


__all__: list[str] = ["FlextInfraDependencyDetectionAnalysis"]
