"""Cooldown admission and the requirement bounds ``make upg`` owns.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, config, m, p, r, s, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCooldownAdmission(s[bool]):
    """Hold every governed requirement inside the ``[tool.uv]`` cooldown.

    ``make upg`` owns the floors and pins its ``[tool.flext.upg]`` record names
    (ADR-030 release eligibility). Native ``uv pip compile`` applies each
    project's own ``exclude-newer`` policy. Before any lock is written,
    :meth:`admit` drops every refused upg-owned bound, so the native
    ``uv lock --upgrade`` picks the newest release the cooldown admits, and
    reports every other refused line, together with every consumer pin of a
    FLEXT-managed tool, at once with its owner. After resolution,
    :meth:`record_bounds` writes each upg-owned bound from the project's own
    ``uv.lock``, so an owned bound is always inside the window.
    """

    @classmethod
    def admit(
        cls,
        request: p.Infra.WorkspaceRequest,
        runner: p.Cli.CommandRunner,
    ) -> p.Result[bool]:
        """Release refused upg-owned bounds or report every other refusal.

        Returns:
            Success once every authored requirement is inside the window, else
            one failure after every refusal is reported and nothing is written.

        """
        located = cls._runtime_root(request).flat_map(
            lambda root: u.Infra.managed_mise_binary(c.Infra.UV, root).map(
                lambda uv: (root, uv)
            ),
        )
        if located.failure:
            return r[bool].from_failure(located)
        root, uv = located.value
        violations: list[str] = []
        plans: dict[Path, Mapping[str, str]] = {}
        for project_root in u.Infra.governed_project_roots(root):
            pyproject = project_root / c.PYPROJECT_FILENAME
            read = cls._declarations(pyproject)
            if read.failure:
                return r[bool].from_failure(read)
            owned, registry = read.value
            violations.extend(cls._managed_violations(pyproject, registry))
            refused = cls._refused((runner, uv, project_root), registry)
            if refused.failure:
                return r[bool].from_failure(refused)
            released: dict[str, str] = {}
            for (section, line, name), reason in refused.value:
                if (
                    name in owned
                    and section != c.Infra.UV_CONSTRAINT_DEPENDENCIES_SECTION
                ):
                    released[line] = u.Infra.bounded_requirement(
                        line, owned[name], None
                    )
                    continue
                violations.append(
                    f"{pyproject}: {line} [{section}]; owner: "
                    f"{cls._owner(line, pyproject, section)}\n{reason}",
                )
            if released:
                plans[pyproject] = released
        if violations:
            for violation in violations:
                u.Cli.error(f"cooldown: {violation}")
            return r[bool].fail(
                f"cooldown refuses {len(violations)} declared requirement(s); "
                "change each at its named owner before upg writes any lock",
            )
        return cls._published(plans, "released for the cooldown resolution")

    @classmethod
    def record_bounds(
        cls,
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[bool]:
        """Write every upg-owned bound from its project's resolved ``uv.lock``.

        Returns:
            Success once each owned bound equals its locked version, or the
            first read or lock-shape failure.

        """
        root = cls._runtime_root(request)
        if root.failure:
            return r[bool].from_failure(root)
        plans: dict[Path, Mapping[str, str]] = {}
        for project_root in u.Infra.governed_project_roots(root.value):
            planned = cls._locked_bounds(project_root)
            if planned.failure:
                return r[bool].from_failure(planned)
            if planned.value:
                plans[project_root / c.PYPROJECT_FILENAME] = planned.value
        return cls._published(plans, "written from the resolved lock")

    @staticmethod
    def _runtime_root(request: p.Infra.WorkspaceRequest) -> p.Result[Path]:
        """Elect the runtime root whose governed projects upg resolves.

        Returns:
            The runtime root, or the election failure.

        """
        return FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root
        ).map(lambda context: context.runtime_root)

    @classmethod
    def _locked_bounds(cls, project_root: Path) -> p.Result[Mapping[str, str]]:
        """Plan one project's upg-owned bounds from its own ``uv.lock``.

        Returns:
            The changed requirement lines, or the first read or lock failure.

        """
        result = r[Mapping[str, str]]
        pyproject = project_root / c.PYPROJECT_FILENAME
        read = cls._declarations(pyproject)
        if read.failure:
            return result.from_failure(read)
        owned, registry = read.value
        targets = [
            (line, name, owned[name])
            for section, line, name in registry
            if name in owned and section != c.Infra.UV_CONSTRAINT_DEPENDENCIES_SECTION
        ]
        if not targets:
            return result.ok({})
        lock_path = project_root / c.Infra.UV_LOCK_FILENAME
        lock = u.Cli.toml_read_json(lock_path).flat_map(
            lambda payload: u.validate_value(m.Infra.LockedEnvironment, payload),
        )
        if lock.failure:
            return result.from_failure(lock)
        planned: dict[str, str] = {}
        for line, name, operator in targets:
            versions = sorted({
                package.version
                for package in lock.value.package
                if package.name == name
            })
            if len(versions) != 1:
                return result.fail(
                    f"{lock_path}: upg-owned {name} must lock exactly one "
                    f"version, found {versions or 'none'}",
                )
            bounded = u.Infra.bounded_requirement(line, operator, versions[0])
            if bounded != line:
                planned[line] = bounded
        return result.ok(planned)

    @staticmethod
    def _declarations(
        pyproject: Path,
    ) -> p.Result[tuple[Mapping[str, str], Sequence[tuple[str, str, str]]]]:
        """Read one pyproject's upg record and its registry requirements.

        Direct references and ``[tool.uv.sources]`` names (FLEXT members and
        forks) resolve outside the index and its cooldown and are skipped.

        Returns:
            The owned ``name -> operator`` record and the unique
            ``(section, requirement, name)`` registry requirements.

        """
        result = r[tuple[Mapping[str, str], Sequence[tuple[str, str, str]]]]
        payload = u.Cli.toml_read_json(pyproject)
        if payload.failure:
            return result.from_failure(payload)
        record = u.validate_value(
            m.Infra.UpgBounds,
            u.Cli.toml_mapping_path(payload.value, c.Infra.UPG_BOUNDS_TABLE) or {},
        )
        if record.failure:
            return result.from_failure(record)
        owned = {
            u.Infra.dep_name(name) or name: operator
            for names, operator in (
                (record.value.floors, c.Infra.UPG_FLOOR_OPERATOR),
                (record.value.pins, c.Infra.UPG_PIN_OPERATOR),
            )
            for name in names
        }
        if len(owned) != len(record.value.floors) + len(record.value.pins):
            return result.fail(
                f"{pyproject}: [tool.flext.upg] names a distribution twice",
            )
        uv_table = (
            u.Cli.toml_mapping_path(payload.value, (c.Infra.TOOL, c.Infra.UV)) or {}
        )
        sourced = frozenset(
            u.Infra.dep_name(name) or name
            for name in u.Cli.toml_mapping_child(uv_table, c.Infra.UV_SOURCES_KEY) or {}
        )
        registry: dict[str, tuple[str, str, str]] = {}
        for path, key in u.Infra.requirement_arrays(payload.value):
            items = (u.Cli.toml_mapping_path(payload.value, path) or {}).get(key, [])
            lines = (
                [line for line in items if isinstance(line, str)]
                if isinstance(items, list)
                else []
            )
            for line in lines:
                name = u.Infra.registry_requirement_name(line, sourced)
                if name is not None and line not in registry:
                    registry[line] = (".".join((*path, key)), line, name)
        return result.ok((owned, tuple(registry.values())))

    @classmethod
    def _refused(
        cls,
        scope: tuple[p.Cli.CommandRunner, Path, Path],
        registry: Sequence[tuple[str, str, str]],
    ) -> p.Result[Sequence[tuple[tuple[str, str, str], str]]]:
        """Ask native uv, under the project's own cooldown, which lines it refuses.

        One resolution of every line admits the common case; only when it
        fails is each line resolved alone, so every refusal is named at once.

        Returns:
            Each refused requirement with uv's own explanation, or the first
            execution failure.

        """
        result = r[Sequence[tuple[tuple[str, str, str], str]]]
        if not registry:
            return result.ok(())
        bulk = cls._compiled(scope, [line for _, line, _ in registry])
        if bulk.failure or bulk.value.exit_code == 0:
            return result.from_failure(bulk) if bulk.failure else result.ok(())
        refused: list[tuple[tuple[str, str, str], str]] = []
        for entry in registry:
            alone = cls._compiled(scope, [entry[1]])
            if alone.failure:
                return result.from_failure(alone)
            if alone.value.exit_code != 0:
                refused.append((entry, alone.value.stderr.strip()))
        return result.ok(tuple(refused))

    @staticmethod
    def _compiled(
        scope: tuple[p.Cli.CommandRunner, Path, Path],
        lines: Sequence[str],
    ) -> p.Result[p.Cli.CommandOutput]:
        """Resolve requirement lines without dependencies through native uv.

        Returns:
            uv's own outcome, or the execution failure.

        """
        runner, uv, project_root = scope
        return runner.run_raw(
            (
                str(uv),
                *c.Infra.UV_COOLDOWN_COMPILE_ARGUMENTS,
                "--python-version",
                config.Infra.codegen.toolchain.python_version,
                "-",
            ),
            cwd=project_root,
            timeout=c.Infra.TIMEOUT_LONG,
            options=m.Cli.ProcessOptions(input_data="\n".join(lines)),
        )

    @staticmethod
    def _managed_violations(
        pyproject: Path,
        registry: Sequence[tuple[str, str, str]],
    ) -> Sequence[str]:
        """Name every dev-group pin of a FLEXT-managed tool.

        The SSOT ``Infra.codegen.scaffold.project.dev`` owns those tools'
        floors and ``make upg`` resolves them; a consumer pin freezes a tool
        the SSOT keeps moving.

        Returns:
            One violation per pinned managed tool.

        """
        managed = tuple(config.Infra.codegen.scaffold.project.dev)
        names = {u.Infra.dep_name(line): line for line in managed}
        dev = f"{c.Infra.DEPENDENCY_GROUPS}.{c.Infra.DEV}"
        return tuple(
            f"{pyproject}: {line} [{section}] pins the FLEXT-managed {name} "
            f"({names[name]}); owner: flext-infra config "
            "Infra.codegen.scaffold.project.dev"
            for section, line, name in registry
            if section == dev
            and name in names
            and line not in managed
            and u.Infra.pinned_requirement(line)
        )

    @staticmethod
    def _owner(line: str, pyproject: Path, section: str) -> str:
        """Name the owner that must change one refused requirement line.

        Returns:
            The FLEXT SSOT key that projects the line, or its authored location.

        """
        codegen = config.Infra.codegen
        if line in codegen.scaffold.project.dev:
            return "flext-infra config Infra.codegen.scaffold.project.dev"
        if line in codegen.toolchain.uv_constraint_dependencies:
            return (
                "flext-infra config Infra.codegen.toolchain.uv_constraint_dependencies"
            )
        return f"authored in {pyproject} [{section}]"

    @staticmethod
    def _published(
        plans: Mapping[Path, Mapping[str, str]],
        reason: str,
    ) -> p.Result[bool]:
        """Rewrite each planned requirement line in place, one file at a time.

        Returns:
            Success once every plan is written, or the first write failure.

        """
        for pyproject, rewrites in plans.items():
            document = u.Cli.toml_read_document(pyproject)
            payload = u.Cli.toml_read_json(pyproject)
            if document.failure or payload.failure:
                return r[bool].from_failure(document if document.failure else payload)
            for path, key in u.Infra.requirement_arrays(payload.value):
                items = (u.Cli.toml_mapping_path(payload.value, path) or {}).get(key)
                if not isinstance(items, list) or not any(
                    item in rewrites for item in items if isinstance(item, str)
                ):
                    continue
                container = u.Cli.toml_table_path(document.value, path)
                if container is None or not all(isinstance(i, str) for i in items):
                    return r[bool].fail(
                        f"{pyproject}: [{'.'.join((*path, key))}] mixes include "
                        "entries with an upg-owned requirement",
                    )
                _ = u.Cli.toml_sync_string_list(
                    container,
                    key,
                    [rewrites.get(str(item), str(item)) for item in items],
                )
            written = u.Cli.toml_write_document(pyproject, document.value)
            if written.failure:
                return written
            for old, new in rewrites.items():
                u.Cli.info(f"upg: {pyproject}: {old} -> {new} ({reason})")
        return r[bool].ok(value=True)


__all__: tuple[str, ...] = ("FlextInfraCooldownAdmission",)
