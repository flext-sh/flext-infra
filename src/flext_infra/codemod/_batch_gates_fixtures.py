"""Rule-fixture verification and snapshot regeneration for the mod gate engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import stat
import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, settings, t, u
from flext_infra.codemod import FlextInfraCodemodSnapshotReconciler


class FlextInfraModGateEngineFixturesMixin:
    """Stage, verify and regenerate ast-grep rule fixtures and snapshots."""

    if TYPE_CHECKING:

        @staticmethod
        def _run_tool(
            root: Path,
            command: t.StrSequence,
            *,
            streams: t.Pair[Path, Path],
            artifact_root: Path,
            finding_exit_code: int | None = None,
        ) -> p.Result[p.Cli.ProcessOutcome]: ...

    @classmethod
    def validate_rule_fixtures(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
    ) -> p.Result[bool]:
        """Verify every fixture against its committed snapshots; never rewrite them.

        A drifted or missing snapshot fails ``ast-grep test``; a snapshot of a
        removed rule or deleted test case fails the owned-inventory check. The
        change they record is made explicit by ``make mod-snapshots`` and lands
        as a reviewed commit, so ``make mod`` cannot accept rewritten output.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for config_root, owner_rules, owner_is_governed in cls._fixture_owners(
            root,
            rules,
        ):
            if owner_is_governed:
                stale = FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                    config_root,
                )
                if stale:
                    return r[bool].fail(
                        "ast-grep snapshots record no current rule test:\n"
                        + "\n".join(stale)
                        + f"\n{c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT}",
                    )
            with tempfile.TemporaryDirectory(
                prefix="mod-rule-fixtures-",
                dir=settings.work_dir,
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                cls.stage_rule_fixture_root(
                    config_root=config_root,
                    temp_root=temp_root,
                )
                cls._materialize_split_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                tested = cls._run_tool(
                    temp_root,
                    (
                        c.Infra.SG,
                        c.Infra.TEST,
                        c.Infra.SG_CONFIG_FLAG,
                        str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
                    ),
                    streams=(Path(temp_dir) / "stdout", Path(temp_dir) / "stderr"),
                    artifact_root=root,
                )
                if tested.failure:
                    remedy = (
                        c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT
                        if owner_is_governed
                        else (
                            f"inherited rule provider {config_root} ships these "
                            "fixtures; repair them in its owner repository"
                        )
                    )
                    return r[bool].fail(f"{tested.error}\n{remedy}")
        return r.ok(value=True)

    @classmethod
    def refresh_rule_snapshots(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
        *,
        apply: bool,
    ) -> p.Result[t.StrSequence]:
        """Regenerate every governed owner's snapshots from its rule tests.

        The explicit counterpart of the verifying ``validate_rule_fixtures``:
        snapshots are projections of the declared test cases, rebuilt from
        scratch so removed rules and deleted cases leave no residue. The
        returned changes are the reviewed diff; inherited providers keep the
        snapshots their owner ships.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        changes: list[str] = []
        for config_root, owner_rules, owner_is_governed in cls._fixture_owners(
            root,
            rules,
        ):
            if not owner_is_governed:
                continue
            with tempfile.TemporaryDirectory(
                prefix="mod-rule-snapshots-",
                dir=settings.work_dir,
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                cls.stage_rule_fixture_root(
                    config_root=config_root,
                    temp_root=temp_root,
                    regenerate_snapshots=True,
                )
                cls._materialize_split_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                # Regenerate every snapshot, then verify the regenerated set.
                for update in ((c.Infra.SG_UPDATE_ALL,), ()):
                    cls._run_tool(
                        temp_root,
                        (
                            c.Infra.SG,
                            c.Infra.TEST,
                            *update,
                            c.Infra.SG_CONFIG_FLAG,
                            str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
                        ),
                        streams=(Path(temp_dir) / "stdout", Path(temp_dir) / "stderr"),
                        artifact_root=root,
                    ).unwrap()
                changes.extend(
                    cls._publish_regenerated_snapshots(
                        config_root=config_root,
                        temp_root=temp_root,
                        apply=apply,
                    ),
                )
        return r[t.StrSequence].ok(tuple(changes))

    @staticmethod
    def _governs(governed_root: Path, config_root: Path) -> bool:
        """Whether the governed repository itself tracks this rule provider.

        Git owns the answer for each declared first-party repository. Installed
        providers remain read-only; a workspace can refresh the catalogs its
        declared member repositories track.

        Returns:
            The resulting ``bool``.

        """
        provider = (config_root / c.Infra.CODEMOD_CONFIG_FILENAME).resolve()
        for owner in sorted(
            u.Infra.governed_project_roots(governed_root),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            if provider.is_relative_to(owner):
                return (
                    u.Infra
                    .git_is_tracked(
                        m.Infra.GitRelativePathRequest(
                            repo_root=owner,
                            relative_path=provider.relative_to(owner).as_posix(),
                        ),
                    )
                    .unwrap()
                    .value
                )
        return False

    @classmethod
    def _fixture_owners(
        cls,
        root: Path,
        rules: t.SequenceOf[Path],
    ) -> t.SequenceOf[t.Triple[Path, t.SequenceOf[Path], bool]]:
        """Group rules by fixture owner and mark the owners this root governs.

        Returns:
            The resulting ``t.SequenceOf[t.Triple[Path, t.SequenceOf[Path], bool]]``.

        Raises:
            ValueError: If discovered ast-grep rules have no fixture owner; or if rule
                fixture scratch must be outside its source root.

        """
        governed_roots = tuple(
            project.resolve() for project in u.Infra.governed_project_roots(root)
        )
        rules_by_owner: MutableMapping[Path, list[Path]] = {}
        for rule in rules:
            owner = FlextInfraCodemodSnapshotReconciler.config_root(rule)
            rules_by_owner.setdefault(owner, []).append(rule)
        if not rules_by_owner:
            msg = "discovered ast-grep rules have no fixture owner"
            raise ValueError(msg)
        scratch = settings.work_dir
        owners: list[t.Triple[Path, t.SequenceOf[Path], bool]] = []
        for config_root, owner_rules in sorted(rules_by_owner.items()):
            if scratch.resolve().is_relative_to(config_root.resolve()):
                msg = "rule fixture scratch must be outside its source root"
                raise ValueError(msg)
            owners.append((
                config_root,
                tuple(owner_rules),
                any(
                    cls._governs(governed_root, config_root)
                    for governed_root in governed_roots
                ),
            ))
        scratch.mkdir(parents=True, exist_ok=True)
        return tuple(owners)

    @staticmethod
    def stage_rule_fixture_root(
        *,
        config_root: Path,
        temp_root: Path,
        regenerate_snapshots: bool = False,
    ) -> None:
        """Copy declared ast-grep inputs only, rejecting links and special files.

        Raises:
            ValueError: If ast-grep fixture must be a regular file or directory.

        """
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        snapshot_roots = {
            directory / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            for directory in directories.test_dirs
        }
        pending = [config_root / c.Infra.CODEMOD_CONFIG_FILENAME]
        pending.extend((
            *directories.rule_dirs,
            *directories.util_dirs,
            *directories.test_dirs,
        ))
        files: set[Path] = set()
        folders: set[Path] = set()
        while pending:
            path = pending.pop()
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                if path in folders:
                    continue
                folders.add(path)
                pending.extend(path.iterdir())
            elif stat.S_ISREG(mode):
                files.add(path)
            else:
                msg = f"ast-grep fixture must be a regular file or directory: {path}"
                raise ValueError(msg)
        temp_root.mkdir()
        for directory in sorted(folders):
            (temp_root / directory.relative_to(config_root)).mkdir(
                parents=True,
                exist_ok=True,
            )
        for source in sorted(files):
            if (
                regenerate_snapshots
                and source.parent in snapshot_roots
                and source.name.endswith(c.Infra.CODEMOD_SNAPSHOT_SUFFIX)
            ):
                # Owned projections are regenerated from all declared test cases.
                # Foreign providers retain their snapshots for verification.
                continue
            shutil.copy2(
                source,
                temp_root / source.relative_to(config_root),
                follow_symlinks=False,
            )

    @classmethod
    def _materialize_split_rule_files(
        cls,
        *,
        config_root: Path,
        temp_root: Path,
        owner_rules: t.SequenceOf[Path],
    ) -> None:
        """Replace multi-document rule files with single-document temp copies.

        Raises:
            RuntimeError: If ``parsed.failure``; or if ast-grep rule document missing
                required id.

        """
        source_rules = set(owner_rules)
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        for directory in (*directories.rule_dirs, *directories.util_dirs):
            source_rules.update(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}"))
        for rule in sorted(source_rules):
            documents = u.Cli.yaml_parse_documents(
                u.Cli.files_read_text(rule).unwrap()
            ).unwrap()
            if len(documents) <= 1:
                continue
            temp_rule = temp_root / rule.relative_to(config_root)
            temp_rule.unlink()
            for document in documents:
                rule_id = document.get(c.Infra.CODEMOD_RULE_TEST_ID_KEY)
                if not isinstance(rule_id, str) or not rule_id:
                    msg = f"ast-grep rule document missing required id: {rule}"
                    raise RuntimeError(msg)
                u.Cli.yaml_dump(
                    temp_rule.with_name(f"{rule_id}{c.Infra.CODEMOD_RULE_SUFFIX}"),
                    document,
                ).unwrap()

    @staticmethod
    def _publish_regenerated_snapshots(
        *,
        config_root: Path,
        temp_root: Path,
        apply: bool,
    ) -> t.StrSequence:
        """Mirror only regenerated snapshot files back to source; report each change.

        Rules, utilities and tests are inputs of the regeneration and are never
        written back. A committed snapshot the regeneration did not produce
        belongs to a removed rule or test and is removed with the rest.

        Returns:
            The resulting ``t.StrSequence``.

        """
        pattern = f"*{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}"
        changes: list[str] = []
        for test_dir in FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        ).test_dirs:
            source_dir = test_dir / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            regenerated_dir = temp_root / source_dir.relative_to(config_root)
            regenerated = {path.name: path for path in regenerated_dir.glob(pattern)}
            committed = {path.name: path for path in source_dir.glob(pattern)}
            for name in sorted(regenerated.keys() | committed.keys()):
                target = source_dir / name
                produced = regenerated.get(name)
                if produced is None:
                    changes.append(f"removed {target}")
                    if apply:
                        target.unlink()
                    continue
                content = produced.read_text(encoding=c.DEFAULT_ENCODING)
                current = committed.get(name)
                if current is not None and (
                    current.read_text(encoding=c.DEFAULT_ENCODING) == content
                ):
                    continue
                changes.append(
                    f"{'created' if current is None else 'updated'} {target}",
                )
                if apply:
                    u.Cli.atomic_write_text_file(target, content).unwrap()
        return tuple(changes)


__all__: list[str] = ["FlextInfraModGateEngineFixturesMixin"]
