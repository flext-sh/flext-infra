"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from importlib.resources import files
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from flext_cli import u
from flext_infra import (
    c,
    m,
    p,
    r,
    t,
)
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    _tool_config_cache: r[m.Infra.ToolConfigDocument] | None = None

    @staticmethod
    def cli_args(**kwargs: t.Infra.InfraValue) -> t.Infra.CliNamespace:
        """Build a CLI-like namespace for command helpers and tests."""
        namespace_factory = t.Infra.CliNamespace.__value__
        return namespace_factory(**kwargs)

    CliArgs = staticmethod(cli_args)

    @staticmethod
    def git_run(cmd: t.StrSequence, cwd: Path) -> p.Result[str]:
        """Run a git command and return stdout as ``r[str]``."""
        run_result = u.Cli.run_raw(cmd, cwd=cwd)
        if run_result.failure:
            return r[str].fail(run_result.error or "git command failed")
        output = run_result.value
        if output.exit_code != 0:
            return r[str].fail(output.stderr or output.stdout or "git command failed")
        return r[str].ok(output.stdout)

    @staticmethod
    def _selected_project_names(
        workspace_root: Path,
        projects: t.StrSequence | None,
    ) -> t.StrSequence:
        """Resolve selected project names or discover all when filter is empty."""
        selected = [name.strip() for name in (projects or []) if name.strip()]
        if selected:
            return selected
        discovered = FlextInfraUtilitiesDocsScope.discover_projects(workspace_root)
        if discovered.failure:
            return []
        return sorted(
            project.name
            for project in discovered.value
            if project.name and project.name.strip()
        )

    # ------------------------------------------------------------------
    # Generic validation (SSOT for TypeAdapter-based coercion)
    # ------------------------------------------------------------------

    @staticmethod
    def validate[T](
        adapter: TypeAdapter[T],
        value: t.ValueOrModel,
        *,
        default: T,
    ) -> T:
        """Validate *value* with any ``TypeAdapter[T]``, returning *default* on failure.

        SSOT for all Pydantic-adapter validation in flext-infra.
        Replaces every try/except ValidationError pattern.

        Example::

            mapping = u.Infra.validate(
                t.Infra.INFRA_MAPPING_ADAPTER,
                raw,
                default={},
            )
            items = u.Infra.validate(
                t.Infra.INFRA_SEQ_ADAPTER,
                raw,
                default=[],
            )
        """
        try:
            return adapter.validate_python(value)
        except (ValidationError, TypeError):
            return default

    # ------------------------------------------------------------------
    # Mapping / list normalization (thin wrappers over validate)
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_str_mapping(
        value: t.ValueOrModel | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Normalize a value to a string-keyed mapping, or ``{}`` on failure."""
        return FlextInfraUtilitiesBase.validate(
            t.Infra.INFRA_MAPPING_ADAPTER,
            value,
            default={},
        )

    @staticmethod
    def normalize_mapping_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Normalize a value to a list of string-keyed mappings."""
        if value is None or not isinstance(value, list):
            return []
        items = FlextInfraUtilitiesBase.validate(
            t.Infra.INFRA_SEQ_ADAPTER,
            value,
            default=[],
        )
        result: list[Mapping[str, t.Infra.InfraValue]] = []
        for item in items:
            validated = FlextInfraUtilitiesBase.validate(
                t.Infra.INFRA_MAPPING_ADAPTER,
                item,
                default={},
            )
            if validated:
                result.append(validated)
        return result

    # ------------------------------------------------------------------
    # Deep path navigation (generic key-path traversal)
    # ------------------------------------------------------------------

    @staticmethod
    def _walk_path(
        data: Mapping[str, t.Infra.InfraValue],
        keys: tuple[str, ...],
    ) -> t.Infra.InfraValue | None:
        """Walk a key path through nested mappings, returning the leaf value."""
        current: Mapping[str, t.Infra.InfraValue] = data
        for key in keys[:-1]:
            raw = current.get(key)
            if raw is None:
                return None
            try:
                current = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
            except ValidationError:
                return None
        return current.get(keys[-1]) if keys else None

    @staticmethod
    def nested_int(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        """Extract a nested int by key path."""
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return u.to_int(raw, default=default) if raw is not None else default

    @staticmethod
    def deep_mapping(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Navigate nested dicts by key path → normalized mapping.

        Replaces chains of ``normalize_str_mapping(x.get("key"))``.
        """
        if not keys:
            return FlextInfraUtilitiesBase.normalize_str_mapping(data)
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return FlextInfraUtilitiesBase.normalize_str_mapping(raw)

    @staticmethod
    def deep_list(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Navigate nested dicts by key path → list of mappings."""
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return FlextInfraUtilitiesBase.normalize_mapping_list(raw)

    # ------------------------------------------------------------------
    # Generic scalar extraction (PEP 695)
    # ------------------------------------------------------------------

    @staticmethod
    def pick_str(
        data: Mapping[str, t.Infra.InfraValue],
        key: str,
        default: str = "",
    ) -> str:
        """Extract a string from mapping, coercing if needed."""
        raw = data.get(key, default)
        return str(raw).strip() if raw is not None else default

    @staticmethod
    def pick_int(
        data: Mapping[str, t.Infra.InfraValue],
        key: str,
        default: int = 0,
    ) -> int:
        """Extract an int from mapping, coercing if needed."""
        raw = data.get(key, default)
        if raw is None:
            return default
        if isinstance(raw, int):
            return raw
        if isinstance(raw, (str, float, bool)):
            return u.to_int(raw, default=default)
        return default

    @staticmethod
    def pick_bool(
        data: Mapping[str, t.Infra.InfraValue],
        key: str,
        *,
        default: bool = False,
    ) -> bool:
        """Extract a bool from mapping."""
        raw = data.get(key)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            normalized = raw.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        if isinstance(raw, int | float):
            return raw != 0
        return default

    @staticmethod
    def get_str_key(
        mapping: Mapping[str, t.Infra.InfraValue],
        key: str,
        *,
        default: str = "",
        case: str | None = None,
    ) -> str:
        """Extract and normalize a string key with optional case conversion."""
        raw = FlextInfraUtilitiesBase.pick_str(mapping, key, default)
        return u.normalize(raw, case=case)

    @staticmethod
    def _load_tool_config_cached() -> p.Result[m.Infra.ToolConfigDocument]:
        """Load, validate, and cache ``tool_config.yml`` for dependency tooling."""
        cached = FlextInfraUtilitiesBase._tool_config_cache
        if cached is not None:
            return cached
        try:
            raw_text = (
                files("flext_infra.deps")
                .joinpath("tool_config.yml")
                .read_text(encoding=c.Infra.ENCODING_DEFAULT)
            )
            parsed = u.Cli.yaml_parse(raw_text)
            if parsed.failure:
                result = r[m.Infra.ToolConfigDocument].fail(
                    parsed.error or "tool_config.yml parse failed",
                )
                FlextInfraUtilitiesBase._tool_config_cache = result
                return result
            validated = m.Infra.ToolConfigDocument.model_validate(parsed.value)
            result = r[m.Infra.ToolConfigDocument].ok(validated)
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValidationError,
            ValueError,
        ) as exc:
            result = r[m.Infra.ToolConfigDocument].fail(
                f"failed to load tool_config.yml: {exc}",
            )
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result

    @staticmethod
    def load_tool_config() -> p.Result[m.Infra.ToolConfigDocument]:
        """Return cached dependency tool configuration."""
        return FlextInfraUtilitiesBase._load_tool_config_cached()

    # ------------------------------------------------------------------
    # Scan result builder (PEP 695 inline type parameter)
    # ------------------------------------------------------------------

    @classmethod
    def build_scan_result[V: p.Infra.ViolationWithLine](
        cls,
        *,
        file_path: Path,
        detector_name: str,
        rule_id: str,
        violations: Sequence[V],
        message_builder: Callable[[V], str],
    ) -> m.Infra.ScanResult:
        """Build a standardized scan result from typed violations."""
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=FlextInfraUtilitiesBase.pick_int(
                        violation.model_dump(), "line"
                    ),
                    message=message_builder(violation),
                    severity="error",
                    rule_id=rule_id,
                )
                for violation in violations
            ],
            detector_name=detector_name,
        )


__all__: list[str] = ["FlextInfraUtilitiesBase"]
