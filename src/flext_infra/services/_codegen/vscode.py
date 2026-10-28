"""VS Code settings codegen owner — the single canonical merge instrumentation.

This is the only place that knows how ``.vscode/settings.json`` is produced.
It parses that explicitly JSONC document through the canonical string-aware
normalizer, validates the resulting mapping, merges the config-driven canonical
keys from ``config.Infra.codegen.vscode`` plus the artifact-derived exclude maps,
and serializes the result with ``u.Cli.json_dumps``. Environment tokens remain
portable and resolve against the folder opened in the editor.
Planning, atomic writes, and fixed-point verification stay owned
by ``FlextInfraCodegenConform``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core.config_sources import FlextStrictYamlConfigSource

from flext_infra import c, m, r, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenVscode:
    """Produce the canonical ``.vscode/settings.json`` document for one root."""

    @classmethod
    def load_vscode_spec(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.CodegenVscodeSpec]:
        """Resolve a repository's typed editor declaration using the strict loader.

        Returns:
            Library defaults overlaid by this project's and local declarations.

        """

        def editor_spec(inputs: m.Infra.CodegenInputs) -> m.Infra.CodegenVscodeSpec:
            return inputs.spec.vscode

        return u.Infra.load_codegen_inputs(repository_root).map(editor_spec)

    @staticmethod
    def vscode_settings(spec: m.Infra.CodegenVscodeSpec) -> t.JsonMapping:
        """Elect ordered declaration pairs without changing array order.

        Returns:
            Each setting's complete value from its final declared pair.

        """
        return u.Infra.configuration_pairs(spec.settings)

    @classmethod
    def vscode_declaration_delta(
        cls,
        repository_root: Path,
        settings: t.JsonMapping,
        *,
        spec: m.Infra.CodegenVscodeSpec,
    ) -> p.Result[m.Infra.CodegenVscodeDeclarationDelta]:
        """Extract portable project overrides through the existing editor owner.

        Derived settings and retired keys remain owned by their generators.
        Environment tokens are compared unchanged, including nested maps and lists.

        Returns:
            Minimal overrides representable by the canonical configuration merge.

        """
        result_type = r[m.Infra.CodegenVscodeDeclarationDelta]
        loaded = u.Infra.load_codegen_inputs(repository_root)
        if loaded.failure:
            return result_type.from_failure(loaded)
        expected: t.MutableJsonMapping = {}
        generated = cls._apply_canonical_settings(
            expected,
            repository_root,
            spec=spec,
            codegen=loaded.value.spec,
        )
        if generated.failure:
            return result_type.from_failure(generated)
        deltas = cls._portable_vscode_deltas(
            settings, spec, expected, loaded.value.spec
        )
        if deltas.failure:
            return result_type.from_failure(deltas)
        delta = m.Infra.CodegenVscodeDeclarationDelta(values=deltas.value)
        validated = cls.compose_vscode_delta(spec, delta)
        if validated.failure:
            return result_type.from_failure(validated)
        return result_type.ok(delta)

    @classmethod
    def _portable_vscode_deltas(
        cls,
        portable: t.JsonMapping,
        spec: m.Infra.CodegenVscodeSpec,
        expected: t.JsonMapping,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.MutableJsonMapping]:
        """Extract complete values as pairs under the single settings owner.

        Returns:
            Ordered setting pairs reproducing the portable document's changes.

        """
        artifact_settings = cls._artifact_settings(codegen)
        pairs: list[t.JsonValue] = [
            [key, value]
            for key, value in sorted(portable.items())
            if key not in spec.stripped_keys
            and key not in artifact_settings
            and (key not in expected or value != expected[key])
        ]
        deltas: t.MutableJsonMapping = {"settings": pairs} if pairs else {}
        return r[t.MutableJsonMapping].ok(deltas)

    @staticmethod
    def compose_vscode_delta(
        spec: m.Infra.CodegenVscodeSpec,
        delta: m.Infra.CodegenVscodeDeclarationDelta,
    ) -> p.Result[m.Infra.CodegenVscodeSpec]:
        """Compose a preview through the canonical deep-merge utility.

        Returns:
            The effective declaration after ordered mapping/list composition.

        """
        baseline = u.json_mapping_adapter().validate_python(
            spec.model_dump(mode="json"),
        )
        merged = FlextStrictYamlConfigSource.merge_values(
            dict(baseline), dict(delta.values)
        )
        return r[m.Infra.CodegenVscodeSpec].create_from_callable(
            partial(m.Infra.CodegenVscodeSpec.model_validate, merged),
        )

    @classmethod
    def render_vscode_settings(
        cls,
        repository_root: Path,
        *,
        spec: m.Infra.CodegenVscodeSpec | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
    ) -> p.Result[str]:
        """Return the canonical-merged ``settings.json`` document for one root.

        ``spec`` is an explicitly resolved project configuration. Live custom
        keys remain intact outside its declared ownership. Rendering
        elects the runtime through the existing topology owner when the
        declaration selects an environment token.

        Returns:
            The canonical-merged ``settings.json`` document for one root.

        """
        settings_path = (
            repository_root / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        )
        read_result = cls._read_existing_settings(settings_path)
        if read_result.failure:
            return r[str].from_failure(read_result)
        settings: t.MutableJsonMapping = {
            key: u.normalize_to_json_value(value)
            for key, value in read_result.value.items()
        }
        if codegen is None:
            selected = u.Infra.load_codegen_inputs(repository_root)
            if selected.failure:
                return r[str].from_failure(selected)
            codegen = selected.value.spec
        if spec is None:
            spec = codegen.vscode
        applied = cls._apply_canonical_settings(
            settings,
            repository_root,
            spec=spec,
            codegen=codegen,
        )
        if applied.failure:
            return r[str].from_failure(applied)
        serialized = u.Cli.json_dumps(dict(settings), indent=2, sort_keys=True)
        if serialized.failure:
            return r[str].from_failure(serialized)
        return r[str].ok(serialized.value + "\n")

    @classmethod
    def _read_existing_settings(cls, settings_path: Path) -> p.Result[t.JsonMapping]:
        """Read one VS Code JSONC document into a validated JSON mapping.

        Returns:
            The resulting ``p.Result[t.JsonMapping]``.

        """
        if not settings_path.exists():
            empty_settings: t.JsonMapping = {}
            return r[t.JsonMapping].ok(empty_settings)
        read_result = u.Cli.files_read_text(settings_path)
        if read_result.failure:
            return r[t.JsonMapping].from_failure(read_result)
        return cls.parse_vscode_settings(read_result.value)

    @classmethod
    def parse_vscode_settings(cls, content: str) -> p.Result[t.JsonMapping]:
        """Validate live or immutable index JSONC through the single editor parser.

        Returns:
            The validated editor document.

        """
        parsed = u.Cli.json_parse(cls._normalize_jsonc(content))
        if parsed.failure:
            return r[t.JsonMapping].from_failure(parsed)
        if not isinstance(parsed.value, Mapping):
            return r[t.JsonMapping].fail("VS Code settings root must be an object")
        return r[t.JsonMapping].ok(
            u.json_mapping_adapter().validate_python(parsed.value),
        )

    @classmethod
    def _normalize_jsonc(cls, content: str) -> str:
        """Return strict JSON text from VS Code JSONC content.

        Returns:
            Strict JSON text from VS Code JSONC content.

        """
        return cls._remove_trailing_commas(cls._remove_jsonc_comments(content))

    @staticmethod
    def _copy_string_literal(content: str, index: int, output: list[str]) -> int:
        """Copy one complete JSON string literal to ``output``.

        ``index`` points at the opening quote; the returned index is the first
        character after the literal, so structural scanners never re-enter a
        string and never interpret its contents.

        Returns:
            The resulting ``int``.

        """
        output.append(content[index])
        index += 1
        escaped = False
        while index < len(content):
            char = content[index]
            output.append(char)
            index += 1
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                break
        return index

    @staticmethod
    def _remove_jsonc_comments(content: str) -> str:
        """Remove JSONC comments while preserving comment markers in strings.

        Returns:
            The resulting ``str``.

        """
        output: list[str] = []
        in_line_comment = False
        in_block_comment = False
        index = 0
        while index < len(content):
            char = content[index]
            next_char = content[index + 1] if index + 1 < len(content) else ""
            if in_line_comment:
                if char in "\r\n":
                    in_line_comment = False
                    output.append(char)
                index += 1
                continue
            if in_block_comment:
                if char == "*" and next_char == "/":
                    in_block_comment = False
                    index += 2
                    continue
                index += 1
                continue
            if char == '"':
                index = FlextInfraCodegenVscode._copy_string_literal(
                    content,
                    index,
                    output,
                )
                continue
            if char == "/" and next_char == "/":
                in_line_comment = True
                index += 2
                continue
            if char == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue
            output.append(char)
            index += 1
        return "".join(output)

    @staticmethod
    def _remove_trailing_commas(content: str) -> str:
        """Remove commas before object or array closers outside strings.

        Returns:
            The resulting ``str``.

        """
        output: list[str] = []
        index = 0
        while index < len(content):
            char = content[index]
            if char == '"':
                index = FlextInfraCodegenVscode._copy_string_literal(
                    content,
                    index,
                    output,
                )
                continue
            if char == ",":
                next_index = index + 1
                while next_index < len(content) and content[next_index].isspace():
                    next_index += 1
                if next_index < len(content) and content[next_index] in "}]":
                    index += 1
                    continue
            output.append(char)
            index += 1
        return "".join(output)

    @classmethod
    def _apply_canonical_settings(
        cls,
        settings: t.MutableJsonMapping,
        repository_root: Path,
        *,
        spec: m.Infra.CodegenVscodeSpec | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
    ) -> p.Result[bool]:
        """Merge canonical codegen VS Code settings into one settings mapping.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if codegen is None:
            loaded = u.Infra.load_codegen_inputs(repository_root)
            if loaded.failure:
                return r[bool].from_failure(loaded)
            codegen = loaded.value.spec
        spec = codegen.vscode if spec is None else spec
        changed = cls._apply_union_settings(settings, spec.map_union_settings)
        token = spec.runtime_environment_token
        environment = (
            "${workspaceFolder}/"
            + u.Infra
            .runtime_environment_dir(repository_root)
            .relative_to(repository_root.resolve(), walk_up=True)
            .as_posix()
            if token is not None
            else ""
        )
        for key, value in cls.vscode_settings(spec).items():
            normalized = u.normalize_to_json_value(value)
            if token is not None:
                normalized = cls._bind_environment_value(
                    normalized, token=token, environment=environment
                )
            if key not in settings or settings[key] != normalized:
                settings[key] = normalized
                changed = True
        # The three exclude maps are complete projections of the artifact SSOT.
        # Replacing them removes retired artifacts instead of preserving stale
        # generated keys forever. Only explicitly declared non-artifact maps use
        # merge semantics.
        artifact_maps = cls._artifact_settings(codegen)
        artifacts_changed = False
        for key, canonical_map in artifact_maps.items():
            canonical = {
                name: u.normalize_to_json_value(value)
                for name, value in canonical_map.items()
            }
            if settings.get(key) == canonical:
                continue
            settings[key] = canonical
            artifacts_changed = True
        # Stripped keys are owned canonically by pyproject.toml [tool.pyright];
        # keeping them in settings.json makes Pylance emit settingsNotOverridable
        # warnings. Actively delete every retired key so existing files converge
        # to a warning-free projection.
        stripped_changed = cls._strip_retired_keys(settings, spec.stripped_keys)
        for key, retired in spec.stripped_map_keys.items():
            current = settings.get(key)
            if isinstance(current, Mapping):
                retained = {
                    name: value
                    for name, value in current.items()
                    if name not in retired
                }
                if retained != current:
                    settings[key] = u.normalize_to_json_value(retained)
                    stripped_changed = True
        return r[bool].ok(
            artifacts_changed or stripped_changed or changed,
        )

    @classmethod
    def _bind_environment_value(
        cls, value: t.JsonValue, *, token: str, environment: str
    ) -> t.JsonValue:
        """Bind the declared environment token inside one validated setting.

        Returns:
            The same JSON shape with environment tokens resolved in string values.

        """
        if isinstance(value, str):
            return value.replace(token, environment)
        if isinstance(value, list):
            return [
                cls._bind_environment_value(item, token=token, environment=environment)
                for item in value
            ]
        if isinstance(value, Mapping):
            return {
                key: cls._bind_environment_value(
                    item, token=token, environment=environment
                )
                for key, item in value.items()
            }
        return value

    @staticmethod
    def _artifact_settings(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> Mapping[str, Mapping[str, str | bool]]:
        """Project the declared artifact maps through their single editor owner.

        Returns:
            Complete derived maps consumed by rendering and migration.

        """
        return {
            "files.exclude": dict(codegen.vscode_files_exclude_map),
            "files.watcherExclude": dict(codegen.vscode_watcher_exclude_map),
            "search.exclude": dict(codegen.vscode_search_exclude_map),
        }

    @staticmethod
    def _strip_retired_keys(
        settings: t.MutableJsonMapping,
        stripped_keys: Sequence[str],
    ) -> bool:
        """Delete every key listed in ``stripped_keys`` from the settings mapping.

        Returns:
            The resulting ``bool``.

        """
        changed = False
        for key in stripped_keys:
            if key in settings:
                del settings[key]
                changed = True
        return changed

    @staticmethod
    def _apply_union_settings(
        settings: t.MutableJsonMapping,
        map_union_settings: Mapping[str, t.JsonMapping],
    ) -> bool:
        """Union-merge canonical map keys over existing project entries.

        Returns:
            The resulting ``bool``.

        """
        changed = False
        for key, canonical_map in map_union_settings.items():
            current = settings.get(key)
            existing: t.MutableJsonMapping = (
                {
                    name: u.normalize_to_json_value(value)
                    for name, value in current.items()
                }
                if isinstance(current, Mapping)
                else {}
            )
            merged = {
                **dict(existing),
                **{
                    name: u.normalize_to_json_value(value)
                    for name, value in canonical_map.items()
                },
            }
            if settings.get(key) == merged:
                continue
            settings[key] = merged
            changed = True
        return changed


__all__: list[str] = ["FlextInfraCodegenVscode"]
