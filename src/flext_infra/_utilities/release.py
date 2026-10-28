"""Release protocol utilities for the u.Infra FLEXT chain.

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

import tarfile
import textwrap
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from flext_cli import u
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from flext_infra import c, m, p, r
from flext_infra._utilities import FlextInfraUtilitiesDependencies


class FlextInfraUtilitiesRelease:
    """Bump derivation, release notes, changelog, and publish-order utilities."""

    @staticmethod
    def archive_member_path(name: str) -> p.Result[Path]:
        """Return one safe relative archive member path.

        Returns:
            One safe relative archive member path.

        """
        relative = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or relative.is_absolute()
            or any(part in {".", ".."} for part in relative.parts)
        ):
            return r[Path].fail(f"unsafe archive member path: {name}")
        if not relative.parts:
            return r[Path].fail(f"unsafe archive member path: {name}")
        return r[Path].ok(Path(*relative.parts))

    @staticmethod
    def materialize_tar_tree(
        archive: tarfile.TarFile,
        destination: Path,
    ) -> p.Result[bool]:
        """Materialize one trusted tar tree without path traversal.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        members = FlextInfraUtilitiesRelease._validated_tar_members(archive)
        if members.failure:
            return r[bool].from_failure(members)
        validated_members = members.value
        if destination.exists():
            return r[bool].fail(
                f"release stage directory already exists: {destination}",
            )
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op(
                f"create release stage parent {destination.parent}",
                exc,
            )
        try:
            with TemporaryDirectory(
                dir=destination.parent,
                prefix=f".{destination.name}.",
            ) as staging_dir:
                staging = Path(staging_dir)
                written = FlextInfraUtilitiesRelease._write_validated_tar_tree(
                    archive,
                    staging,
                    validated_members,
                )
                if written.failure:
                    return written
                staging.rename(destination)
        except OSError as exc:
            return r[bool].fail_op(
                f"materialize release archive into {destination}",
                exc,
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _validated_tar_members(
        archive: tarfile.TarFile,
    ) -> p.Result[tuple[tuple[tarfile.TarInfo, Path], ...]]:
        """Validate every archive member name and kind for safe materialization.

        Returns:
            The resulting ``p.Result`` of member and relative path pairs.

        """
        try:
            members = tuple(archive.getmembers())
        except tarfile.TarError as exc:
            return r[tuple[tuple[tarfile.TarInfo, Path], ...]].fail_op(
                "read release archive members",
                exc,
            )
        validated_members: list[tuple[tarfile.TarInfo, Path]] = []
        for member in members:
            path_result = FlextInfraUtilitiesRelease.archive_member_path(member.name)
            if path_result.failure:
                return r[tuple[tuple[tarfile.TarInfo, Path], ...]].from_failure(
                    path_result,
                )
            if member.issym() or member.islnk():
                return r[tuple[tuple[tarfile.TarInfo, Path], ...]].fail(
                    f"release archive contains symbolic or hard link: {member.name}",
                )
            if not member.isdir() and not member.isfile():
                return r[tuple[tuple[tarfile.TarInfo, Path], ...]].fail(
                    f"release archive contains unsupported member: {member.name}",
                )
            validated_members.append((member, path_result.value))
        return r[tuple[tuple[tarfile.TarInfo, Path], ...]].ok(
            tuple(validated_members),
        )

    @staticmethod
    def _write_validated_tar_tree(
        archive: tarfile.TarFile,
        staging: Path,
        validated_members: Sequence[tuple[tarfile.TarInfo, Path]],
    ) -> p.Result[bool]:
        """Write prevalidated tar members into a staging directory.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for member, relative_path in validated_members:
            member_path = staging / relative_path
            if member.isdir():
                try:
                    member_path.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    return r[bool].fail_op(
                        f"create release archive directory {member_path}",
                        exc,
                    )
                continue
            try:
                member_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return r[bool].fail_op(
                    f"create release archive parent {member_path.parent}",
                    exc,
                )
            extracted = archive.extractfile(member)
            if extracted is None:
                return r[bool].fail(
                    f"release archive could not open member: {member.name}",
                )
            try:
                member_path.write_bytes(extracted.read())
            except OSError as exc:
                return r[bool].fail_op(
                    f"write release archive member {member_path}",
                    exc,
                )
            finally:
                extracted.close()
        return r[bool].ok(value=True)

    @staticmethod
    def plan_bump(
        subjects: Sequence[str],
        bump_types: Mapping[str, c.Infra.VersionBump],
    ) -> p.Result[c.Infra.VersionBump]:
        """Derive the release bump from the merged pull-request subjects.

        Every subject is the merge commit of one pull request, so it carries the
        pull-request title. A Conventional Commits title maps through
        ``bump_types``; ``!`` marks a breaking change. A GitHub default merge
        subject carries no release information and therefore fails loudly: the
        protocol requires the title, never a guess. Any other merge subject (a
        lane absorbing its integration base) contributes nothing.

        Returns:
            The resulting ``p.Result[c.Infra.VersionBump]``.

        """
        order = tuple(c.Infra.VersionBump)
        bump = c.Infra.VersionBump.NONE
        for subject in subjects:
            if c.Infra.PULL_REQUEST_MERGE_SUBJECT_RE.match(subject):
                return r[c.Infra.VersionBump].fail(
                    "merged pull request without a Conventional Commits title: "
                    f"{subject!r}",
                )
            match = c.Infra.CONVENTIONAL_SUBJECT_RE.match(subject)
            if match is None:
                continue
            candidate = (
                c.Infra.VersionBump.MAJOR
                if match.group("breaking")
                else bump_types.get(match.group("type"), c.Infra.VersionBump.NONE)
            )
            if order.index(candidate) > order.index(bump):
                bump = candidate
        return r[c.Infra.VersionBump].ok(bump)

    @staticmethod
    def release_subject(subject: str, version: str) -> bool:
        """Whether ``subject`` is the protocol's release commit for ``version``.

        Matches the commit as the lane wrote it and as GitHub merged it, which
        appends the pull-request number to the subject.

        Returns:
            The resulting ``bool``.

        """
        match = c.Infra.RELEASE_COMMIT_SUBJECT_RE.match(subject)
        return match is not None and match.group("version") == version

    @staticmethod
    def generate_notes(
        version: str,
        tag: str,
        project_list: Sequence[m.Infra.ProjectInfo],
        changes: str,
        output_path: Path,
    ) -> p.Result[bool]:
        """Generate release notes markdown from release context.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        lines: MutableSequence[str] = [
            f"# Release {tag}",
            "",
            "## Scope",
            "",
            f"- Release version: {version}",
            f"- Projects packaged: {len(project_list) + 1}",
            "",
            "## Projects impacted",
            "",
            "- root",
        ]
        lines.extend(f"- {proj.name}" for proj in project_list)
        lines.extend([
            "",
            "## Pull requests since last release",
            "",
            FlextInfraUtilitiesRelease._markdown_changelog(
                changes or "- Initial tagged release",
            ),
        ])
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            u.write_file(
                output_path,
                "\n".join(lines).rstrip() + "\n",
                encoding=c.DEFAULT_ENCODING,
            )
            u.fetch_logger(__name__).info(
                "release_notes_written",
                path=str(output_path),
            )
            return r[bool].ok(value=True)
        except OSError as exc:
            return r[bool].fail(f"failed to write release notes: {exc}", exception=exc)

    @staticmethod
    def _markdown_changelog(changes: str) -> str:
        """Render merged subjects as escaped, width-bounded markdown bullets.

        A GitHub merge subject is untrusted markdown: a bare ``*`` or ``_`` made
        the formatter rewrite the emphasis and split the subject, and an
        unwrapped subject overran the 88-column markdown ceiling. Escaping the
        inline punctuation first keeps every character literal, and wrapping
        each bullet keeps it inside the ceiling. The transform is deterministic,
        so re-stamping an unchanged plan is byte-identical.

        Returns:
            The resulting ``str``.

        """
        rendered: MutableSequence[str] = []
        for raw in changes.splitlines():
            line = raw.strip()
            if not line:
                continue
            marker = ""
            if line.startswith("- "):
                marker, line = "- ", line[2:]
            escaped = c.Infra.MARKDOWN_INLINE_ESCAPE_RE.sub(r"\\\1", line)
            rendered.append(
                textwrap.fill(
                    escaped,
                    width=c.Infra.RELEASE_NOTES_LINE_LENGTH,
                    initial_indent=marker,
                    subsequent_indent=(
                        c.Infra.RELEASE_NOTES_CONTINUATION_INDENT if marker else ""
                    ),
                    break_long_words=False,
                    break_on_hyphens=False,
                ),
            )
        return "\n".join(rendered)

    @staticmethod
    def update_changelog(
        repository_root: Path,
        version: str,
        tag: str,
        notes_path: Path,
    ) -> p.Result[bool]:
        """Update docs/changelog and docs/releases entries.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        try:
            FlextInfraUtilitiesRelease._write_changelog_files(
                repository_root=repository_root,
                version=version,
                tag=tag,
                notes_path=notes_path,
            )
        except OSError as exc:
            return r[bool].fail_op("changelog update", exc)
        return r[bool].ok(value=True)

    @staticmethod
    def _write_changelog_files(
        *,
        repository_root: Path,
        version: str,
        tag: str,
        notes_path: Path,
    ) -> None:
        """Write the docs changelog plus the latest and tagged release notes."""
        docs = repository_root / c.Infra.DIR_DOCS
        changelog_path = docs / "CHANGELOG.md"
        latest_path = docs / "releases" / "latest.md"
        tagged_path = docs / "releases" / f"{tag}.md"
        notes_text = notes_path.read_text(encoding=c.DEFAULT_ENCODING)
        existing = (
            changelog_path.read_text(encoding=c.DEFAULT_ENCODING)
            if changelog_path.exists()
            else "# Changelog\n\n"
        )
        updated = FlextInfraUtilitiesRelease._updated_changelog(
            existing=existing,
            version=version,
            tag=tag,
        )
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(changelog_path, updated, encoding=c.DEFAULT_ENCODING)
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(latest_path, notes_text, encoding=c.DEFAULT_ENCODING)
        u.write_file(tagged_path, notes_text, encoding=c.DEFAULT_ENCODING)
        u.fetch_logger(__name__).info(
            "release_changelog_written",
            path=str(changelog_path),
        )
        u.fetch_logger(__name__).info(
            "release_tagged_notes_written",
            path=str(tagged_path),
        )

    @staticmethod
    def _updated_changelog(*, existing: str, version: str, tag: str) -> str:
        """Return changelog text with a release section for the version.

        Returns:
            Changelog text with a release section for the version.

        """
        date = u.now().date().isoformat()
        heading = f"## {version} - "
        section = (
            f"{heading}{date}\n\n- Release tag: `{tag}`\n\n"
            f"Full notes: `docs/releases/{tag}.md`\n\n"
        )
        marker = "# Changelog\n\n"
        if heading in existing:
            updated = existing
        elif marker in existing:
            updated = existing.replace(marker, marker + section, 1)
        else:
            updated = marker + section + existing
        # Why: a changelog ending with the section's blank line failed the
        # markdown gate (MD012); the normalization applies on every stamp, so a
        # rerun on an open release lane repairs a changelog written before it.
        return updated.rstrip("\n") + "\n"

    @classmethod
    def release_publish_waves(
        cls,
        targets: Sequence[tuple[str, Path]],
    ) -> p.Result[Sequence[Sequence[str]]]:
        """Group selected release projects into dependency-respecting waves.

        Publishing to an index is immutable: a dependent uploaded before its
        dependency leaves a state no rollback repairs. The order is derived
        from each project's own ``pyproject.toml`` -- the manifests are the
        SSOT, and a hand-written order would be a second source that diverges
        in silence. Every project in a wave depends only on earlier waves, so a
        wave may upload in parallel while the sequence between waves is strict.

        Returns:
            The resulting ``p.Result[Sequence[Sequence[str]]]``.

        """
        selected = {name for name, _ in targets}
        edges: MutableMapping[str, Sequence[str]] = {}
        for name, path in targets:
            declared = cls._release_runtime_dependencies(path)
            if declared.failure:
                return r[Sequence[Sequence[str]]].from_failure(declared)
            # A dependency outside the selection is not an edge: it is already
            # on the index or out of scope, and treating it as an edge would
            # deadlock the graph on a package this release never publishes.
            edges[name] = tuple(
                dependency
                for dependency in declared.value
                if dependency in selected and dependency != name
            )
        return u.Cli.dag_waves(edges)

    @staticmethod
    def _release_runtime_dependencies(path: Path) -> p.Result[Sequence[str]]:
        """Return the runtime dependency names declared by one project.

        Only ``[project].dependencies`` counts. Dev groups are not part of the
        published distribution, so an index never resolves them -- and because
        the platform packages test against each other, counting them would
        report the whole workspace as one cycle.

        Returns:
            The runtime dependency names declared by one project.

        """
        pyproject = path / c.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[Sequence[str]].fail(
                f"release project has no {c.PYPROJECT_FILENAME}: {path}",
            )
        document = u.Cli.toml_read_document(pyproject)
        if document.failure:
            return r[Sequence[str]].from_failure(document)
        payload = u.Cli.toml_as_mapping(document.value)
        project = payload.get(c.Infra.PROJECT) if payload else None
        if not isinstance(project, Mapping):
            return r[Sequence[str]].ok(())
        requirements = project.get(c.Infra.DEPENDENCIES)
        if not isinstance(requirements, Sequence) or isinstance(requirements, str):
            return r[Sequence[str]].ok(())
        return r[Sequence[str]].ok(
            tuple(
                sorted({
                    name
                    for requirement in requirements
                    if isinstance(requirement, str)
                    and (
                        name := FlextInfraUtilitiesDependencies.dep_name(
                            requirement,
                        )
                    )
                    is not None
                }),
            ),
        )

    @staticmethod
    def release_specifier(version: str) -> p.Result[str]:
        """Return the semver-compatible range (minor line before 1.0, else major).

        Returns:
            The compatible-release specifier for the declared version.

        """
        try:
            parsed = Version(version)
        except InvalidVersion as exc:
            return r[str].fail_op("parse internal dependency version", exc)
        if parsed.major == 0:
            return r[str].ok(f"~={version}")
        return r[str].ok(f">={version},<{parsed.major + 1}")

    @staticmethod
    def release_identity_verdict(
        identity: tuple[str | None, str], expectation: m.Infra.ArtifactExpectation
    ) -> p.Result[bool]:
        """Prove one artifact's core metadata ``(Name, Version)`` identity.

        Returns:
            Success when name and version match the expectation.

        """
        name, raw_version = identity
        project, version = expectation.project, expectation.version
        if name is None or canonicalize_name(name) != canonicalize_name(project):
            return r[bool].fail(
                f"artifact Name mismatch: expected {project}, found {name}"
            )
        try:
            expected, actual = Version(version), Version(raw_version)
        except InvalidVersion as exc:
            return r[bool].fail_op("validate artifact Version", exc)
        if actual != expected:
            return r[bool].fail(
                f"artifact Version mismatch: expected {expected}, found {actual}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def release_requirement_pins_verdict(
        cls, requirements: Sequence[str], versions: Mapping[str, str]
    ) -> p.Result[bool]:
        """Prove every internal ``Requires-Dist`` carries its declared fleet pin.

        Returns:
            Success when every internal requirement is pinned.

        """
        for text in requirements:
            try:
                requirement = Requirement(text)
            except InvalidRequirement as exc:
                return r[bool].fail_op("parse artifact requirement", exc)
            dependency = canonicalize_name(requirement.name)
            # A direct reference is source-declared; only fleet pins derive.
            if requirement.url is not None or not dependency.startswith(
                c.Infra.PKG_PREFIX_HYPHEN,
            ):
                continue
            pin = (
                cls.release_specifier(versions[dependency])
                if dependency in versions
                else r[str].fail(f"internal dependency version unknown: {dependency}")
            )
            if pin.failure or str(requirement.specifier) != pin.value:
                return r[bool].fail(
                    f"artifact contains unpinned FLEXT dependency: {text}",
                )
        return r[bool].ok(value=True)

    @classmethod
    def release_pinned_requirement(
        cls, requirement: str, versions: Mapping[str, str]
    ) -> p.Result[tuple[str, bool]]:
        """Pin one requirement's internal dependency to its declared version.

        Returns:
            The rendered text and whether it keeps a direct reference.

        """
        result_type = r[tuple[str, bool]]
        try:
            parsed = Requirement(requirement)
        except InvalidRequirement as exc:
            return result_type.fail_op("parse release requirement", exc)
        name = canonicalize_name(parsed.name)
        if not name.startswith(c.Infra.PKG_PREFIX_HYPHEN):
            return result_type.ok((requirement.strip(), parsed.url is not None))
        if name not in versions:
            return result_type.fail(
                f"internal dependency version unknown to this release: {name}",
            )
        pin = cls.release_specifier(versions[name])
        if pin.failure:
            return result_type.from_failure(pin)
        extras = f"[{','.join(sorted(parsed.extras))}]" if parsed.extras else ""
        marker = f"; {parsed.marker}" if parsed.marker is not None else ""
        return result_type.ok((f"{parsed.name}{extras}{pin.value}{marker}", False))


__all__: list[str] = ["FlextInfraUtilitiesRelease"]
