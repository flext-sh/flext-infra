"""Rule fixture staging, validation, and snapshot regeneration for codemods.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import shutil
import stat
import tempfile
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod import FlextInfraCodemodSnapshotReconciler
from flext_infra.codemod._gates import FlextInfraModGateRunner


class FlextInfraModGateFixtures(FlextInfraModGateRunner):
    """Validate ast-grep rule fixtures against snapshots and refresh owned ones."""

    @classmethod
    def validate_rule_fixtures(
        cls,
        root: Path,
        rules: Sequence[Path],
        *,
        rule_ids: Sequence[str] = (),
    ) -> p.Result[bool]:
        """Verify the selected rules' fixtures against their snapshots; never rewrite.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for config_root, owner_rules, owner_is_governed in cls._fixture_owners(
            root,
            rules,
        ):
            selected = (
                frozenset(rule_ids)
                if rule_ids
                else frozenset(
                    rule_id
                    for rule in owner_rules
                    for rule_id in u.Infra.ast_grep_rule_contract(rule)[0]
                )
            )
            if owner_is_governed:
                stale = FlextInfraCodemodSnapshotReconciler.stale_snapshots(
                    config_root,
                    selected,
                )
                if stale:
                    return r[bool].fail(
                        "ast-grep snapshots record no current rule test:\n"
                        + "\n".join(stale)
                        + f"\n{c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT}",
                    )
            with tempfile.TemporaryDirectory(
                prefix="mod-rule-fixtures-",
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                cls.stage_rule_fixture_root(
                    config_root=config_root,
                    temp_root=temp_root,
                )
                cls._materialize_native_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                pattern = "|".join(re.escape(rule_id) for rule_id in sorted(selected))
                tested = cls._sg_test(
                    temp_root,
                    root,
                    c.Infra.SG_FILTER_FLAG,
                    f"^(?:{pattern})$",
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
        rules: Sequence[Path],
        *,
        apply: bool,
    ) -> p.Result[Sequence[str]]:
        """Regenerate every governed owner's snapshots from its rule tests.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

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
            ) as temp_dir:
                temp_root = Path(temp_dir) / config_root.name
                cls.stage_rule_fixture_root(
                    config_root=config_root,
                    temp_root=temp_root,
                    regenerate_snapshots=True,
                )
                cls._materialize_native_rule_files(
                    config_root=config_root,
                    temp_root=temp_root,
                    owner_rules=owner_rules,
                )
                cls._sg_test(temp_root, root, c.Infra.SG_UPDATE_ALL).unwrap()
                cls._sg_test(temp_root, root).unwrap()
                changes.extend(
                    cls._publish_regenerated_snapshots(
                        config_root=config_root,
                        temp_root=temp_root,
                        apply=apply,
                    ),
                )
        return r[Sequence[str]].ok(tuple(changes))

    @staticmethod
    def _governs(governed_root: Path, config_root: Path) -> bool:
        """Whether the governed repository itself tracks this rule provider.

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
        rules: Sequence[Path],
    ) -> Sequence[tuple[Path, Sequence[Path], bool]]:
        """Group rules by fixture owner and mark the owners this root governs.

        Returns:
            The resulting ``Sequence[tuple[Path, Sequence[Path], bool]]``.

        Raises:
            ValueError: If rule fixture scratch lies inside its source root.

        """
        governed_roots = tuple(
            project.resolve() for project in u.Infra.governed_project_roots(root)
        )
        rules_by_owner: MutableMapping[Path, list[Path]] = {}
        for rule in rules:
            owner = FlextInfraCodemodSnapshotReconciler.config_root(rule)
            rules_by_owner.setdefault(owner, []).append(rule)
        scratch = Path(tempfile.gettempdir())
        owners: list[tuple[Path, Sequence[Path], bool]] = []
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
            TypeError: If ast-grep utilDirs must be a list.

        """
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        snapshot_roots = {
            directory / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            for directory in directories.test_dirs
        }
        fixture_utils = config_root / c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME
        pending = [config_root / c.Infra.CODEMOD_CONFIG_FILENAME]
        pending.extend((
            *directories.rule_dirs,
            *directories.util_dirs,
            *directories.test_dirs,
            *((fixture_utils,) if fixture_utils.is_dir() else ()),
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
                continue
            shutil.copy2(
                source,
                temp_root / source.relative_to(config_root),
                follow_symlinks=False,
            )
        if fixture_utils.is_dir():
            staged_config = temp_root / c.Infra.CODEMOD_CONFIG_FILENAME
            payload = dict(u.Cli.yaml_safe_load(staged_config).unwrap())
            declared = payload.get(c.Infra.CODEMOD_UTIL_DIRS_KEY, [])
            if not isinstance(declared, list):
                msg = f"ast-grep utilDirs must be a list: {staged_config}"
                raise TypeError(msg)
            payload[c.Infra.CODEMOD_UTIL_DIRS_KEY] = (
                [*declared, c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME]
                if c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME not in declared
                else declared
            )
            u.Cli.yaml_dump(staged_config, payload).unwrap()

    @classmethod
    def _materialize_native_rule_files(
        cls,
        *,
        config_root: Path,
        temp_root: Path,
        owner_rules: Sequence[Path],
    ) -> None:
        """Stage bound native documents under their owning catalog filenames.

        Raises:
            RuntimeError: If an ast-grep rule document has no id.
            ValueError: If the fixture owner declares no rule directory.

        """
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
            config_root,
        )
        if not directories.rule_dirs:
            msg = f"fixture owner declares no native rule directory: {config_root}"
            raise ValueError(msg)
        source_rules = set(owner_rules)
        for directory in directories.rule_dirs:
            source_rules.update(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}"))
        cls._split_utility_files(config_root, temp_root, directories.util_dirs)
        bodies = cls._staged_utility_bodies((
            *(
                temp_root / item.relative_to(config_root)
                for item in directories.util_dirs
            ),
            temp_root / c.Infra.CODEMOD_FIXTURE_UTILS_DIRNAME,
        ))
        sensitive = u.Infra.codemod_binding_sensitive(bodies)
        for rule in sorted(source_rules):
            documents = u.Cli.yaml_parse_documents(
                u.Cli.files_read_text(rule).unwrap()
            ).unwrap()
            temp_rule = temp_root / rule.relative_to(config_root)
            rendered: list[t.JsonMapping] = []
            for document in documents:
                rule_id = document.get(c.Infra.CODEMOD_RULE_TEST_ID_KEY)
                if not isinstance(rule_id, str) or not rule_id:
                    msg = f"ast-grep rule document missing required id: {rule}"
                    raise RuntimeError(msg)
                rendered.append(
                    u.Infra.codemod_bound_document(document, bodies, sensitive)
                )
            u.Infra.codemod_write_native_documents(
                temp_rule,
                tuple(rendered),
                atomic=False,
            )

    @staticmethod
    def _split_utility_files(
        config_root: Path, temp_root: Path, util_dirs: Sequence[Path]
    ) -> None:
        """Replace each staged multi-document utility file with one file per id."""
        for directory in util_dirs:
            for utility in sorted(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}")):
                documents = u.Cli.yaml_parse_documents(
                    u.Cli.files_read_text(utility).unwrap()
                ).unwrap()
                if len(documents) <= 1:
                    continue
                temp_utility = temp_root / utility.relative_to(config_root)
                temp_utility.unlink()
                for document in documents:
                    u.Infra.codemod_write_native_documents(
                        temp_utility.with_name(
                            f"{document['id']}{c.Infra.CODEMOD_RULE_SUFFIX}"
                        ),
                        (document,),
                        atomic=False,
                    )

    @staticmethod
    def _staged_utility_bodies(
        directories: Sequence[Path],
    ) -> Mapping[str, t.JsonMapping]:
        """Read the rule body of every staged utility by its identity.

        Returns:
            Each utility's rule body keyed by its id.

        """
        bodies: MutableMapping[str, t.JsonMapping] = {}
        for directory in directories:
            if not directory.is_dir():
                continue
            for utility in sorted(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}")):
                for document in u.Cli.yaml_parse_documents(
                    u.Cli.files_read_text(utility).unwrap()
                ).unwrap():
                    body = document.get("rule")
                    if isinstance(body, Mapping):
                        bodies[str(document["id"])] = body
        return bodies

    @staticmethod
    def _publish_regenerated_snapshots(
        *,
        config_root: Path,
        temp_root: Path,
        apply: bool,
    ) -> Sequence[str]:
        """Mirror only regenerated snapshot files back to source; report each change.

        Returns:
            The resulting ``Sequence[str]``.

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
                native = produced.read_text(encoding=c.DEFAULT_ENCODING)
                normalized = "\n".join(line.rstrip() for line in native.splitlines())
                normalized = f"{normalized}\n" if native.endswith("\n") else normalized
                recorded = u.Cli.yaml_parse(native).unwrap()
                content = (
                    normalized
                    if u.Cli.yaml_parse(normalized).unwrap() == recorded
                    else u.Cli.yaml_dump_str(recorded)
                )
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

    @classmethod
    def _sg_test(
        cls,
        temp_root: Path,
        artifact_root: Path,
        *flags: str,
    ) -> p.Result[p.Cli.ProcessOutcome]:
        """Run ``sg test`` against one staged rule-fixture root.

        Returns:
            The fully reaped ``sg test`` outcome.

        """
        return cls._run_tool(
            temp_root,
            (
                c.Infra.SG,
                c.Infra.TEST,
                c.Infra.SG_INCLUDE_OFF_FLAG,
                *flags,
                c.Infra.SG_CONFIG_FLAG,
                str(temp_root / c.Infra.CODEMOD_CONFIG_FILENAME),
            ),
            outputs=(
                temp_root.parent / "stdout",
                temp_root.parent / "stderr",
                artifact_root,
            ),
        )


__all__: list[str] = ["FlextInfraModGateFixtures"]
