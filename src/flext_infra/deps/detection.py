"""Dependency detection and analysis service for deptry, pip-check, and typing stubs."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_core import FlextLogger, FlextUtilities, r
from flext_infra import c, m, p, t, u


class FlextInfraDependencyDetectionService:
    """Runtime vs dev dependency detector using deptry, pip-check, and mypy stub analysis."""

    _log = FlextLogger.create_module_logger(__name__)

    DEFAULT_MODULE_TO_TYPES_PACKAGE: t.StrMapping = (
        c.Infra.DEFAULT_MODULE_TO_TYPES_PACKAGE
    )

    def __init__(self) -> None:
        """Initialize the dependency detection service with selector, toml, and runner."""
        self.selector: u.Infra | None = None
        self.toml: p.Infra.TomlReader | None = None
        self.runner: p.Infra.CommandRunner | None = None

    def _resolve_projects(
        self,
        workspace_root: Path,
        names: t.StrSequence,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        if self.selector is not None:
            return self.selector.resolve_projects(workspace_root, names)
        return u.Infra.resolve_projects(workspace_root, names)

    def _read_plain(self, path: Path) -> r[t.Infra.ContainerDict]:
        if self.toml is not None:
            return self.toml.read_plain(path)
        return u.Infra.read_plain(path)

    def _run_raw(
        self,
        cmd: t.StrSequence,
        *,
        cwd: Path | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> r[m.Infra.CommandOutput]:
        if self.runner is not None:
            return self.runner.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
        return u.Infra.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)

    @staticmethod
    def to_infra_value(
        value: t.Infra.InfraValue | None,
    ) -> t.Infra.InfraValue:
        """Convert container value to namespaced infra value."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        scalar_types = (str, int, float, bool, type(None))
        if isinstance(value, list):
            try:
                sequence = t.Infra.JSON_SEQ_ADAPTER.validate_python(value)
            except ValidationError:
                return None
            converted: MutableSequence[t.Infra.InfraValue] = []
            for item in sequence:
                converted_item = FlextInfraDependencyDetectionService.to_infra_value(
                    item,
                )
                if (converted_item is None and item is not None) or not isinstance(
                    converted_item, scalar_types
                ):
                    return None
                converted.append(converted_item)
            return converted
        try:
            mapping_value = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        except ValidationError:
            return None
        converted_map: MutableMapping[str, t.Infra.InfraValue] = {}
        for key, map_item in mapping_value.items():
            converted_item = FlextInfraDependencyDetectionService.to_infra_value(
                map_item,
            )
            if (converted_item is None and map_item is not None) or not isinstance(
                converted_item, scalar_types
            ):
                return None
            converted_map[str(key)] = converted_item
        return converted_map

    @staticmethod
    def _mapping_from_value(
        value: t.Infra.InfraValue | None,
    ) -> t.Infra.ContainerDict:
        if value is None:
            return {}
        mapped_value = u.Infra.as_toml_mapping(value)
        if mapped_value is None:
            return {}
        return FlextInfraDependencyDetectionService._to_toml_config(mapped_value)

    @staticmethod
    def classify_issues(
        issues: Sequence[t.Infra.ContainerDict],
    ) -> m.Infra.DeptryIssueGroups:
        """Classify deptry issues by error code (DEP001-DEP004)."""
        groups = m.Infra.DeptryIssueGroups.model_validate({
            "dep001": [],
            "dep002": [],
            "dep003": [],
            "dep004": [],
        })
        for item in issues:
            normalized_item: t.MutableStrMapping = {}
            for key, raw_value in item.items():
                if raw_value is None:
                    normalized_item[str(key)] = ""
                    continue
                if isinstance(raw_value, (str, int, float, bool)):
                    normalized_item[str(key)] = str(raw_value)
            error_obj = item.get(c.Infra.ERROR)
            if not u.is_mapping(error_obj):
                continue
            try:
                error_data = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(error_obj)
            except ValidationError:
                continue
            code = error_data.get(c.Infra.CODE)
            bucket = {
                "DEP001": groups.dep001,
                "DEP002": groups.dep002,
                "DEP003": groups.dep003,
                "DEP004": groups.dep004,
            }.get(FlextUtilities.ensure_str(code))
            if bucket is not None:
                bucket.append(normalized_item)
        return groups

    @staticmethod
    def _to_toml_config(
        payload: Mapping[str, t.Infra.InfraValue],
    ) -> t.Infra.ContainerDict:
        normalized: MutableMapping[str, t.Infra.InfraValue] = {}
        for key, value in payload.items():
            converted = FlextInfraDependencyDetectionService.to_infra_value(value)
            if converted is None and value is not None:
                continue
            normalized[str(key)] = converted
        return normalized

    def build_project_report(
        self,
        project_name: str,
        deptry_issues: Sequence[t.Infra.ContainerDict],
    ) -> m.Infra.ProjectDependencyReport:
        """Build a project dependency report from classified deptry issues."""
        classified = self.classify_issues(deptry_issues)

        def _module_names(
            items: Sequence[Mapping[str, t.Infra.InfraValue]],
        ) -> MutableSequence[str]:
            return [
                str(val)
                for item in items
                if (val := item.get(c.Infra.MODULE)) is not None
            ]

        return m.Infra.ProjectDependencyReport(
            project=project_name,
            deptry=m.Infra.DeptryReport(
                missing=_module_names(classified.dep001),
                unused=_module_names(classified.dep002),
                transitive=_module_names(classified.dep003),
                dev_in_runtime=_module_names(classified.dep004),
                raw_count=len(deptry_issues),
            ),
        )

    def discover_project_paths(
        self,
        workspace_root: Path,
        projects_filter: t.StrSequence | None = None,
    ) -> r[Sequence[Path]]:
        """Discover project paths with pyproject.toml in workspace.

        Returns only the Path objects, filtered to those with pyproject.toml.
        For full ProjectInfo metadata, use u.Infra.discover_projects().
        """
        names = projects_filter or []
        result = self._resolve_projects(workspace_root, names)
        if result.is_failure:
            return r[Sequence[Path]].fail(result.error or "project resolution failed")
        projects_info: Sequence[m.Infra.ProjectInfo] = result.value
        projects = [
            project.path
            for project in projects_info
            if (project.path / c.Infra.Files.PYPROJECT_FILENAME).exists()
        ]
        return r[Sequence[Path]].ok(sorted(projects))

    def get_current_typings_from_pyproject(self, project_path: Path) -> t.StrSequence:
        """Extract currently declared typing packages from project pyproject.toml."""
        pyproject = project_path / c.Infra.Files.PYPROJECT_FILENAME
        read_result = self._read_plain(pyproject)
        if read_result.is_failure:
            return []
        data = self._to_toml_config(read_result.value)
        if not data:
            return []
        names: t.Infra.StrSet = set()
        tool = self._mapping_from_value(data.get(c.Infra.TOOL))
        poetry = self._mapping_from_value(tool.get(c.Infra.POETRY))
        group = self._mapping_from_value(poetry.get(c.Infra.GROUP))
        typings_group = self._mapping_from_value(group.get(c.Infra.Directories.TYPINGS))
        deps = self._mapping_from_value(typings_group.get(c.Infra.DEPENDENCIES))
        names.update(str(key) for key in deps)
        project = self._mapping_from_value(data.get(c.Infra.PROJECT))
        optional = self._mapping_from_value(
            project.get(c.Infra.OPTIONAL_DEPENDENCIES),
        )
        typings = optional.get(c.Infra.Directories.TYPINGS)
        if isinstance(typings, list):
            for spec in typings:
                spec_text = str(spec)
                names.add(
                    spec_text
                    .split("[", maxsplit=1)[0]
                    .split(">=", maxsplit=1)[0]
                    .split("==", maxsplit=1)[0]
                    .strip(),
                )
        elif u.is_mapping(typings):
            names.update(str(k) for k in typings)
        return sorted(names)

    def get_required_typings(
        self,
        project_path: Path,
        venv_bin: Path,
        limits_path: Path | None = None,
        *,
        include_mypy: bool = True,
    ) -> r[m.Infra.TypingsReport]:
        """Analyze project and generate typing stubs requirements report."""
        limits = self.load_dependency_limits(limits_path)
        exclude_set: t.Infra.StrSet = set()
        typing_libraries = limits.get(c.Infra.TYPING_LIBRARIES)
        if u.is_mapping(typing_libraries):
            excluded = typing_libraries.get(c.Infra.EXCLUDE)
            if isinstance(excluded, list):
                exclude_set = {str(e) for e in excluded}
        hinted: t.StrSequence = []
        missing_modules: t.StrSequence = []
        if include_mypy:
            hints_result = self.run_mypy_stub_hints(project_path, venv_bin)
            if hints_result.is_failure:
                return r[m.Infra.TypingsReport].fail(
                    hints_result.error or "typing hint detection failed",
                )
            typed_hints: t.Infra.Pair[t.StrSequence, t.StrSequence] = hints_result.value
            hinted, missing_modules = typed_hints
        required_set: t.Infra.StrSet = set(hinted)
        for module_name in missing_modules:
            package = self.module_to_types_package(module_name, limits)
            if package:
                required_set.add(package)
        required_set -= exclude_set
        current = self.get_current_typings_from_pyproject(project_path)
        current_set = set(current)
        python_cfg = limits.get(c.Infra.PYTHON)
        version_val = (
            python_cfg.get(c.Infra.VERSION) if u.is_mapping(python_cfg) else None
        )
        python_version = str(version_val) if version_val is not None else None
        report = m.Infra.TypingsReport(
            required_packages=sorted(required_set),
            hinted=hinted,
            missing_modules=missing_modules,
            current=current,
            to_add=sorted(required_set - current_set),
            to_remove=sorted(current_set - required_set),
            limits_applied=bool(limits),
            python_version=python_version,
        )
        return r[m.Infra.TypingsReport].ok(report)

    def load_dependency_limits(
        self,
        limits_path: Path | None = None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Load dependency limits configuration from TOML file."""
        path = limits_path or Path(__file__).resolve().parent / "dependency_limits.toml"
        result = self._read_plain(path)
        if result.is_failure:
            return {}
        return self._to_toml_config(result.value)

    def module_to_types_package(
        self,
        module_name: str,
        limits: Mapping[str, t.Infra.InfraValue],
    ) -> str | None:
        """Map a module name to its corresponding types-* package."""
        root = module_name.split(".", 1)[0]
        if root.startswith(u.Infra.INTERNAL_PREFIXES):
            return None
        typing_libraries = limits.get(c.Infra.TYPING_LIBRARIES)
        if u.is_mapping(typing_libraries):
            module_to_package = typing_libraries.get(c.Infra.MODULE_TO_PACKAGE)
            mapped_packages = u.Infra.as_toml_mapping(module_to_package)
            if mapped_packages is not None and root in mapped_packages:
                value = mapped_packages.get(root)
                return str(value) if value is not None else None
        return self.DEFAULT_MODULE_TO_TYPES_PACKAGE.get(root.lower())

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
        *,
        config_path: Path | None = None,
        json_output_path: Path | None = None,
        extend_exclude: t.StrSequence | None = None,
    ) -> r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]]:
        """Run deptry analysis on a project and parse JSON output."""
        config = config_path or project_path / c.Infra.Files.PYPROJECT_FILENAME
        if not config.exists():
            return r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]].ok(([], 0))
        out_file = json_output_path or project_path / ".deptry-report.json"
        cmd: MutableSequence[str] = [
            str(venv_bin / c.Infra.DEPTRY),
            ".",
            "--config",
            str(config),
            "--json-output",
            str(out_file),
            "--no-ansi",
        ]
        if extend_exclude:
            for excluded in extend_exclude:
                cmd.extend(["--extend-exclude", excluded])
        result = self._run_raw(
            cmd,
            cwd=project_path,
            timeout=c.Infra.Timeouts.MEDIUM,
        )
        if result.is_failure:
            return r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]].fail(
                result.error or "deptry execution failed",
            )
        issues: Sequence[t.Infra.ContainerDict] = []
        if out_file.exists():
            raw = out_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            loaded_result = u.Infra.parse(raw) if raw.strip() else None
            if (
                loaded_result is not None
                and loaded_result.is_success
                and isinstance(loaded_result.value, list)
            ):
                normalized_issues: MutableSequence[t.Infra.ContainerDict] = []
                for item in loaded_result.value:
                    if not u.is_mapping(item):
                        continue
                    try:
                        typed_item = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item)
                    except ValidationError:
                        continue
                    converted_issue = self._to_toml_config(typed_item)
                    if len(converted_issue) == len(typed_item):
                        normalized_issues.append(converted_issue)
                issues = normalized_issues
            if json_output_path is None:
                with contextlib.suppress(OSError):
                    out_file.unlink()
        cmd_result: m.Infra.CommandOutput = result.value
        return r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]].ok((
            issues,
            cmd_result.exit_code,
        ))

    def run_mypy_stub_hints(
        self,
        project_path: Path,
        venv_bin: Path,
        *,
        timeout: int = c.Infra.Timeouts.DEFAULT,
    ) -> r[t.Infra.Pair[t.StrSequence, t.StrSequence]]:
        """Run mypy to detect missing type stubs and hinted packages."""
        mypy_bin = venv_bin / c.Infra.MYPY
        if not mypy_bin.exists():
            return r[t.Infra.Pair[t.StrSequence, t.StrSequence]].ok(([], []))
        cmd: t.StrSequence = [
            str(mypy_bin),
            c.Infra.Paths.DEFAULT_SRC_DIR,
            "--config-file",
            c.Infra.Files.PYPROJECT_FILENAME,
            "--no-error-summary",
        ]
        env = {
            **os.environ,
            "VIRTUAL_ENV": str(venv_bin.parent),
            "PATH": f"{venv_bin}:{os.environ.get('PATH', '')}",
        }
        result = self._run_raw(cmd, cwd=project_path, timeout=timeout, env=env)
        if result.is_failure:
            return r[t.Infra.Pair[t.StrSequence, t.StrSequence]].fail(
                result.error or "mypy execution failed",
            )
        cmd_result: m.Infra.CommandOutput = result.value
        output = f"{cmd_result.stdout}\n{cmd_result.stderr}"
        hinted = {
            match.group(1).strip()
            for match in u.Infra.MYPY_HINT_RE.finditer(output)
            if match.group(1).strip()
        }
        missing = {
            match.group(1).strip()
            for match in u.Infra.MYPY_STUB_RE.finditer(output)
            if match.group(1).strip()
        }
        return r[t.Infra.Pair[t.StrSequence, t.StrSequence]].ok((
            sorted(hinted),
            sorted(missing),
        ))

    def run_pip_check(
        self,
        workspace_root: Path,
        venv_bin: Path,
    ) -> r[t.Infra.Pair[t.StrSequence, int]]:
        """Run pip check to detect dependency conflicts in workspace."""
        pip = venv_bin / "pip"
        if not pip.exists():
            return r[t.Infra.Pair[t.StrSequence, int]].ok(([], 0))
        env = {**os.environ, "VIRTUAL_ENV": str(venv_bin.parent)}
        result = self._run_raw(
            [str(pip), c.Infra.Verbs.CHECK],
            cwd=workspace_root,
            timeout=c.Infra.Timeouts.SHORT,
            env=env,
        )
        if result.is_failure:
            return r[t.Infra.Pair[t.StrSequence, int]].fail(
                result.error or "pip check failed"
            )
        cmd_result: m.Infra.CommandOutput = result.value
        output = cmd_result.stdout
        lines = output.strip().splitlines() if output else []
        return r[t.Infra.Pair[t.StrSequence, int]].ok((lines, cmd_result.exit_code))


__all__ = [
    "FlextInfraDependencyDetectionService",
]
