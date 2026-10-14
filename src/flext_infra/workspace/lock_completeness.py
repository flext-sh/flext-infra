"""Fail-closed completeness validation of the committed uv.lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from json import dumps
from pathlib import Path

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraFlextBindingService,
    FlextInfraWorkspaceDetector,
)


class FlextInfraWorkspaceLockCompleteness:
    """Verify native UV ownership, freshness and the active resolved closure.

    This is read-only lock verification, not deptry's import-usage analysis or
    a resolver. Native UV checks declared origins and bounds; the typed graph
    independently rejects fragments that lost reachable package entries.
    """

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.WorkspaceLockRequest,
    ) -> p.Result[int]:
        """Validate one CLI request against the checkout's committed lock.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return cls.validate(request.repository_root)

    @classmethod
    def validate(cls, repository_root: Path) -> p.Result[int]:
        """Require the checkout's committed lock to be complete.

        Returns:
            The resulting ``p.Result[int]``.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        lock_path = context.value.lock_path
        if not lock_path.is_file():
            return r[int].fail(f"{lock_path}: no committed lock; run make upg")
        return cls.validate_lock_file(lock_path)

    @classmethod
    def validate_lock_file(cls, lock_path: Path) -> p.Result[int]:
        """Check one native lock against its manifests and consumer interpreter.

        Returns:
            The resulting ``p.Result[int]``.

        """
        try:
            return cls._validated_lock(lock_path)
        except (OSError, ValueError) as exc:
            return r[int].fail(f"{lock_path}: {exc}", exception=exc)

    @classmethod
    def _validated_lock(cls, lock_path: Path) -> p.Result[int]:
        """Run the completeness phases over one native lock.

        Returns:
            The resulting ``p.Result[int]``.

        """
        loaded = cls._loaded_native_lock(lock_path)
        if loaded.failure:
            return r[int].from_failure(loaded)
        owned = cls._resolved_lock_owner(lock_path)
        if owned.failure:
            return r[int].from_failure(owned)
        context, owner = owned.value
        verified = cls._verified_native_owner(lock_path, context, owner)
        if verified.failure:
            return r[int].from_failure(verified)
        probed = cls._probed_lock_facts(verified.value, context, owner, loaded.value)
        if probed.failure:
            return r[int].from_failure(probed)
        packages, facts = probed.value
        pending = cls._pending_lock_edges(
            lock_path,
            loaded.value,
            owner,
            packages,
            facts,
        )
        if pending.failure:
            return r[int].from_failure(pending)
        return cls._resolved_closure_size(lock_path, packages, pending.value, facts)

    @classmethod
    def _loaded_native_lock(
        cls, lock_path: Path
    ) -> p.Result[m.Infra.LockedEnvironment]:
        """Parse the committed lock and require a native UV lock path.

        Returns:
            The resulting ``p.Result[m.Infra.LockedEnvironment]``.

        """
        payload = u.Cli.toml_read_json(lock_path)
        if payload.failure:
            return r[m.Infra.LockedEnvironment].from_failure(payload)
        locked = m.Infra.LockedEnvironment.model_validate_json(
            dumps(payload.value),
        )
        if lock_path.name != c.Infra.UV_LOCK_FILENAME:
            return r[m.Infra.LockedEnvironment].fail(
                f"{lock_path}: not a native UV lock path",
            )
        return r[m.Infra.LockedEnvironment].ok(locked)

    @classmethod
    def _resolved_lock_owner(
        cls,
        lock_path: Path,
    ) -> p.Result[t.Pair[m.Infra.WorkspaceRuntimeContext, Path]]:
        """Elect the resolution context that owns this committed lock.

        Returns:
            The resulting ``(resolution context, workspace owner)`` pair.

        """
        result_type = r[t.Pair[m.Infra.WorkspaceRuntimeContext, Path]]
        context = FlextInfraWorkspaceDetector.resolution_context(lock_path.parent)
        if context.failure:
            return result_type.from_failure(context)
        owner = lock_path.parent.resolve()
        if lock_path.resolve() != context.value.lock_path.resolve():
            return result_type.fail(
                f"{lock_path}: lock differs from selected resolution context",
            )
        return result_type.ok((context.value, owner))

    @staticmethod
    def _verified_native_owner(
        lock_path: Path,
        context: m.Infra.WorkspaceRuntimeContext,
        owner: Path,
    ) -> p.Result[Path]:
        """Require native UV to elect the same workspace owner.

        Returns:
            The managed UV binary the owner election was verified with.

        """
        result_type = r[Path]
        binary = u.Infra.managed_mise_binary(c.Infra.UV, context.runtime_root)
        if binary.failure:
            return result_type.from_failure(binary)
        native_owner = u.Cli.run(
            (str(binary.value), "workspace", "dir", "--project", str(owner)),
            cwd=owner,
        )
        if native_owner.failure:
            return result_type.from_failure(native_owner)
        if Path(native_owner.value.stdout.strip()) != owner:
            return result_type.fail(
                f"{lock_path}: native UV owner differs from selected "
                f"resolution context",
            )
        return result_type.ok(binary.value)

    @staticmethod
    def _probed_lock_facts(
        binary: Path,
        context: m.Infra.WorkspaceRuntimeContext,
        owner: Path,
        locked: m.Infra.LockedEnvironment,
    ) -> p.Result[t.Pair[t.SequenceOf[m.Infra.LockedPackage], t.StrMapping]]:
        """Probe the lock freshness and read the interpreter's marker facts.

        Returns:
            The resulting ``(locked packages, marker environment facts)`` pair.

        """
        result_type = r[t.Pair[t.SequenceOf[m.Infra.LockedPackage], t.StrMapping]]
        python = u.Infra.runtime_python(context.runtime_root)
        environment = FlextInfraFlextBindingService.consumer_marker_environment(
            consumer_root=owner,
            python=python,
        )
        if environment.failure:
            return result_type.from_failure(environment)
        checked = u.Cli.run(
            (
                str(binary),
                "lock",
                "--check",
                "--project",
                str(owner),
                "--python",
                str(python),
            ),
            cwd=owner,
        )
        if checked.failure:
            return result_type.from_failure(checked)
        facts = environment.value
        packages = tuple(
            item
            for item in locked.package
            if not item.resolution_markers
            or any(
                Marker(marker).evaluate(environment=dict(facts))
                for marker in item.resolution_markers
            )
        )
        return result_type.ok((packages, facts))

    @classmethod
    def _pending_lock_edges(
        cls,
        lock_path: Path,
        locked: m.Infra.LockedEnvironment,
        owner: Path,
        packages: t.SequenceOf[m.Infra.LockedPackage],
        facts: t.StrMapping,
    ) -> p.Result[t.SequenceOf[m.Infra.LockedDependency]]:
        """Collect the active dependency edges every local root contributes.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.LockedDependency]]``.

        """
        result_type = r[t.SequenceOf[m.Infra.LockedDependency]]
        pending: list[m.Infra.LockedDependency] = []
        for item in packages:
            edges = cls._locked_item_edges(locked, owner, item, facts)
            if edges.failure:
                return result_type.from_failure(edges)
            pending.extend(edges.value)
        if not pending:
            return result_type.fail(
                f"{lock_path}: lock has no local manifest roots; run make upg",
            )
        return result_type.ok(tuple(pending))

    @classmethod
    def _locked_item_edges(
        cls,
        locked: m.Infra.LockedEnvironment,
        owner: Path,
        item: m.Infra.LockedPackage,
        facts: t.StrMapping,
    ) -> p.Result[t.SequenceOf[m.Infra.LockedDependency]]:
        """Collect the active edges one locked package root contributes.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.LockedDependency]]``.

        """
        result_type = r[t.SequenceOf[m.Infra.LockedDependency]]
        source = item.source
        local = next(
            (
                slot
                for slot in (source.editable, source.directory, source.virtual)
                if slot is not None
            ),
            None,
        )
        if local is None or (local != "." and item.name not in locked.members):
            return result_type.ok(())
        root = (owner / local).resolve()
        parsed = u.Cli.toml_read_document(root / c.PYPROJECT_FILENAME)
        if parsed.failure:
            return result_type.from_failure(parsed)
        document = parsed.value
        manifest_payload = u.Cli.toml_as_mapping(document)
        if manifest_payload is None:
            return result_type.fail(
                f"{root}: locked local manifest is not a TOML mapping",
            )
        project = u.Cli.json_as_mapping(manifest_payload.get(c.Infra.PROJECT))
        manifest = m.Infra.DepsToml.MemberRequirements.model_validate(
            {
                "name": project.get(c.Infra.NAME),
                "dependencies": project.get(c.Infra.DEPENDENCIES, ()),
                "optional_dependencies": project.get(
                    c.Infra.OPTIONAL_DEPENDENCIES,
                    {},
                ),
                "dependency_groups": manifest_payload.get(
                    c.Infra.DEPENDENCY_GROUPS,
                    {},
                ),
            },
        )
        edges: list[m.Infra.LockedDependency] = [
            m.Infra.LockedDependency(
                name=manifest.name,
                version=item.version,
                source=item.source,
                extra=tuple(manifest.optional_dependencies),
            ),
        ]
        for line in u.Infra.active_session_requirements(
            document,
            environment=facts,
        ):
            requirement = Requirement(line)
            edges.append(
                m.Infra.LockedDependency(
                    name=requirement.name,
                    extra=tuple(requirement.extras),
                ),
            )
        edges.extend(
            edge
            for group in item.dev_dependencies.values()
            for edge in group
            if edge.marker is None
            or Marker(edge.marker).evaluate(environment=dict(facts))
        )
        return result_type.ok(tuple(edges))

    @staticmethod
    def _resolved_closure_size(
        lock_path: Path,
        packages: t.SequenceOf[m.Infra.LockedPackage],
        pending: t.SequenceOf[m.Infra.LockedDependency],
        facts: t.StrMapping,
    ) -> p.Result[int]:
        """Walk the active edge closure to unique resolved package entries.

        Returns:
            The resulting ``p.Result[int]``.

        """
        result_type = r[int]
        visited: dict[int, frozenset[str]] = {}
        worklist = list(pending)
        while worklist:
            edge = worklist.pop()
            matches = tuple(
                index
                for index, item in enumerate(packages)
                if canonicalize_name(item.name) == canonicalize_name(edge.name)
                and (edge.version is None or item.version == edge.version)
                and (edge.source is None or item.source == edge.source)
            )
            if len(matches) != 1:
                return result_type.fail(
                    f"{lock_path}: active graph edge {edge.name} has "
                    f"{len(matches)} matching [[package]] entries; run make upg",
                )
            index = matches[0]
            extras = visited.get(index, frozenset()) | frozenset(edge.extra)
            if index in visited and visited[index] == extras:
                continue
            visited[index] = extras
            item = packages[index]
            worklist.extend(
                dependency
                for dependency in (
                    *item.dependencies,
                    *(
                        dependency
                        for extra in extras
                        for dependency in item.optional_dependencies.get(extra, ())
                    ),
                )
                if dependency.marker is None
                or any(
                    Marker(dependency.marker).evaluate(
                        environment={**facts, "extra": extra},
                    )
                    for extra in ("", *extras)
                )
            )
        return result_type.ok(len(visited))


__all__: tuple[str, ...] = ("FlextInfraWorkspaceLockCompleteness",)
