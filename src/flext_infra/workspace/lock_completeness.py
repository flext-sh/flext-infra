"""Fail-closed completeness validation of the committed uv.lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, u
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import FlextInfraFlextBindingService
from flext_infra import p, r, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


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
            payload = u.Cli.toml_read_json(lock_path)
            if payload.failure:
                return r[int].from_failure(payload)
            locked = m.Infra.LockedEnvironment.model_validate(payload.value)
            if lock_path.name != c.Infra.UV_LOCK_FILENAME:
                return r[int].fail(f"{lock_path}: not a native UV lock path")
            owned = FlextInfraCodegenConform.require_own_lock(lock_path.parent)
            if owned.failure:
                return r[int].from_failure(owned)
            owner = owned.value.resolve()
            python = u.Infra.runtime_python(owner)
            environment = FlextInfraFlextBindingService.consumer_marker_environment(
                consumer_root=owner,
                python=python,
            )
            if environment.failure:
                return r[int].from_failure(environment)
            checked = u.Cli.run(
                (
                    c.Infra.UV,
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
                return r[int].from_failure(checked)
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
            pending: list[m.Infra.LockedDependency] = []
            for item in packages:
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
                    continue
                root = (owner / local).resolve()
                parsed = u.Cli.toml_read_document(root / c.PYPROJECT_FILENAME)
                if parsed.failure:
                    return r[int].from_failure(parsed)
                document = parsed.value
                manifest_payload = u.Cli.toml_as_mapping(document)
                if manifest_payload is None:
                    return r[int].fail(
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
                pending.append(
                    m.Infra.LockedDependency(
                        name=manifest.name,
                        version=item.version,
                        source=item.source,
                        extra=tuple(manifest.optional_dependencies),
                    ),
                )
                for line in u.Infra.active_session_requirements(
                    document,
                    environment=facts,
                ):
                    requirement = Requirement(line)
                    pending.append(
                        m.Infra.LockedDependency(
                            name=requirement.name,
                            extra=tuple(requirement.extras),
                        ),
                    )
                pending.extend(
                    edge
                    for group in item.dev_dependencies.values()
                    for edge in group
                    if edge.marker is None
                    or Marker(edge.marker).evaluate(environment=dict(facts))
                )
            if not pending:
                return r[int].fail(
                    f"{lock_path}: lock has no local manifest roots; run make upg",
                )
            visited: dict[int, frozenset[str]] = {}
            while pending:
                edge = pending.pop()
                matches = tuple(
                    index
                    for index, item in enumerate(packages)
                    if canonicalize_name(item.name) == canonicalize_name(edge.name)
                    and (edge.version is None or item.version == edge.version)
                    and (edge.source is None or item.source == edge.source)
                )
                if len(matches) != 1:
                    return r[int].fail(
                        f"{lock_path}: active graph edge {edge.name} has {len(matches)} "
                        "matching [[package]] entries; run make upg",
                    )
                index = matches[0]
                extras = visited.get(index, frozenset()) | frozenset(edge.extra)
                if index in visited and visited[index] == extras:
                    continue
                visited[index] = extras
                item = packages[index]
                pending.extend(
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
            return r[int].ok(len(visited))
        except (OSError, ValueError) as exc:
            return r[int].fail(f"{lock_path}: {exc}", exception=exc)


__all__: tuple[str, ...] = ("FlextInfraWorkspaceLockCompleteness",)
