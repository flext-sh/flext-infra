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
from flext_infra.workspace import FlextInfraFlextBindingService


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
        resolved = u.Cli.run(
            (c.Infra.UV, "workspace", "dir", "--project", str(repository_root)),
            cwd=repository_root,
        )
        if resolved.failure:
            return r[int].from_failure(resolved)
        owner = resolved.value.stdout.strip()
        if not owner or not Path(owner).is_absolute():
            return r[int].fail("uv workspace dir returned no absolute lock owner")
        return cls.validate_lock_file(Path(owner) / c.Infra.UV_LOCK_FILENAME)

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
            owner = lock_path.parent
            checked = u.Cli.run(
                (c.Infra.UV, "lock", "--check", "--project", str(owner)),
                cwd=owner,
            )
            if checked.failure:
                return r[int].from_failure(checked)
            environment = FlextInfraFlextBindingService.consumer_marker_environment(
                consumer_root=owner,
                python=u.Infra.runtime_python(owner),
            )
            if environment.failure:
                return r[int].from_failure(environment)
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
                # Native --check validates every source slot; the canonical
                # manifest model validates owned data before requirement selection.
                manifest = u.PyprojectDocument.model_validate(
                    u.Cli.toml_as_mapping(document),
                )
                if manifest.project is None:
                    return r[int].fail(
                        f"{root}: locked local project has no project table",
                    )
                pending.append(
                    m.Infra.LockedDependency(
                        name=manifest.project.name,
                        version=item.version,
                        source=item.source,
                        extra=tuple(item.optional_dependencies),
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
