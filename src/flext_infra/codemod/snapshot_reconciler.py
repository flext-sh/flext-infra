"""Reconcile ast-grep snapshots with the active inherited rule hierarchy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, t, u


class FlextInfraCodemodSnapshotReconciler:
    """Remove generated snapshots whose canonical rule ID no longer exists."""

    @staticmethod
    def config_root(rule: Path) -> Path:
        """Resolve the nearest ast-grep configuration that owns a rule."""
        for ancestor in rule.resolve().parents:
            if (ancestor / c.Infra.CODEMOD_CONFIG_FILENAME).is_file():
                return ancestor
        msg = f"ast-grep rule has no owning sgconfig.yml: {rule}"
        raise ValueError(msg)

    @classmethod
    def reconcile(cls, config_root: Path, active_rule_ids: frozenset[str]) -> int:
        """Delete only stale generated snapshot projections for one owner."""
        config_path = config_root / c.Infra.CODEMOD_CONFIG_FILENAME
        payload = u.Cli.yaml_safe_load(config_path).unwrap()
        raw_test_configs = payload.get(c.Infra.CODEMOD_TEST_CONFIGS_KEY)
        if not isinstance(raw_test_configs, Sequence) or isinstance(
            raw_test_configs, str
        ):
            msg = f"invalid ast-grep testConfigs contract: {config_path}"
            raise ValueError(msg)
        removed = 0
        for raw_test_config in raw_test_configs:
            if not isinstance(raw_test_config, Mapping):
                msg = f"ast-grep testConfig must be a mapping: {config_path}"
                raise ValueError(msg)
            raw_test_dir = raw_test_config.get(c.Infra.CODEMOD_TEST_DIR_KEY)
            if not isinstance(raw_test_dir, str) or not raw_test_dir.strip():
                msg = f"ast-grep testConfig lacks testDir: {config_path}"
                raise ValueError(msg)
            test_dir = Path(raw_test_dir)
            if test_dir.is_absolute() or ".." in test_dir.parts:
                msg = f"ast-grep testDir escapes its owner: {raw_test_dir}"
                raise ValueError(msg)
            snapshot_dir = config_root / test_dir / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            if not snapshot_dir.is_dir():
                continue
            for snapshot in sorted(
                snapshot_dir.glob(f"*{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}")
            ):
                rule_id = snapshot.name.removesuffix(c.Infra.CODEMOD_SNAPSHOT_SUFFIX)
                if rule_id in active_rule_ids:
                    continue
                snapshot.unlink()
                removed += 1
                u.Cli.info(f"mod: removed stale snapshot {snapshot}")
        return removed


__all__: t.StrSequence = ("FlextInfraCodemodSnapshotReconciler",)
