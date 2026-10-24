"""Native ast-grep cascade: one staged sgconfig per stage, applied to a fixed point.

Every fixable rule that carries no ``metadata.context`` (and is neither an
owned-path rule nor a rope relocation) applies through ast-grep's own
``scan --update-all``. The engine stages one native configuration per
declared stage under the project's ``.reports/codemod/native/<stage>``, so
``ast-grep scan -c <that sgconfig.yml> --update-all`` reproduces the stage by
hand. The cascade runs every stage in the declared order over one staged
preview of the project's authored sources, repeats the sequence until no byte
changes, and returns the changed sources for a single publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, settings, t
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.codemod_rules import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities.mise_binary import FlextInfraUtilitiesMiseBinary
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.protected_edit_linting import (
    FlextInfraUtilitiesProtectedEditLinting,
)


class FlextInfraUtilitiesCodemodNativeCascade:
    """Stage and run the native ast-grep cascade of ``make mod``."""

    @staticmethod
    def codemod_tool_binary(name: str) -> Path:
        """Resolve one declared tool from the invocation's own runtime owner.

        Consumer scratch directories never own the invocation's runtime tools,
        so the owner is the runtime environment of the current invocation.

        Returns:
            The absolute managed executable, never a PATH shim.

        """
        owner_root = FlextInfraUtilitiesProjectDiscovery.runtime_environment_dir(
            Path.cwd(),
            runtime_root=type(settings).fetch_global().Infra.runtime_root,
        ).parent
        return FlextInfraUtilitiesMiseBinary.managed_mise_binary(
            name, owner_root
        ).unwrap()

    @staticmethod
    def codemod_native_eligible(rule: m.Infra.CodemodRule) -> bool:
        """Whether ast-grep alone applies the rule: a fix and no engine predicate.

        Returns:
            True for a fixable rule without context, owned path or relocation.

        """
        return (
            rule.fixable
            and not rule.context
            and rule.owned_path_suffix is None
            and rule.relocation is None
        )

    @staticmethod
    def _rule_shape(rule_id: str) -> str | None:
        """The generated shape a rule id declares before the id separator.

        Returns:
            The shape, or ``None`` for a catalog rule id without a separator.

        """
        shape, separator, _rest = rule_id.partition(
            c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        )
        return shape if separator else None

    @classmethod
    def _stage_claims(cls, stage: m.Infra.ModStageConfig, rule_id: str) -> bool:
        """Whether a native stage owns one rule id.

        A stage with shapes owns exactly those generated shapes; the catalog
        stage owns every id no shaped stage claims.

        Returns:
            True when the id belongs to the stage.

        """
        shape = cls._rule_shape(rule_id)
        if stage.shapes:
            return shape in stage.shapes
        claimed = {
            claimed_shape
            for other in config.Infra.tooling.mod.phases.stages
            for claimed_shape in other.shapes
        }
        return shape not in claimed

    @classmethod
    def codemod_native_stage(
        cls,
        project: Path,
        plan: m.Infra.CodemodRulePlan,
        stage: m.Infra.ModStageConfig,
        generated: m.Infra.CodemodNativeGenerated,
    ) -> m.Infra.CodemodRuleset | None:
        """Write one stage's native configuration under the project's reports.

        The stage directory holds the elected catalog rules the stage owns,
        their provider utilities, the project's generated utilities and the
        generated rule documents of the stage's shapes, rendered in memory
        from the same producers ``make gen`` projects. It replaces the
        previous stage directory in one rename; a stage that owns no rule
        leaves no directory behind.

        Returns:
            The staged ruleset, or ``None`` when the stage owns no rule.

        """
        root = project.absolute()
        elected = frozenset(plan.project_rule_ids[root])
        rules = tuple(
            rule
            for rule in plan.rules
            if rule.id in elected
            and cls.codemod_native_eligible(rule)
            and cls._stage_claims(stage, rule.id)
        )
        generated_rules = {
            identity: document
            for identity, document in generated.rules.items()
            if cls._stage_claims(stage, identity)
        }
        reports = root / c.Infra.MOD_NATIVE_STAGE_RELATIVE_PATH
        final = reports / stage.name
        u.Cli.ensure_dir(reports).unwrap()
        if not rules and not generated_rules:
            if final.exists():
                shutil.rmtree(final)
            return None
        rule_ids = frozenset(rule.id for rule in rules)
        rulesets = tuple(
            m.Infra.CodemodRuleset(
                provider=ruleset.provider,
                config=ruleset.config,
                rule_ids=tuple(item for item in ruleset.rule_ids if item in rule_ids),
                fixable_rule_ids=tuple(
                    item for item in ruleset.fixable_rule_ids if item in rule_ids
                ),
            )
            for ruleset in plan.rulesets
            if rule_ids.intersection(ruleset.rule_ids)
        )
        staging = Path(tempfile.mkdtemp(prefix=f".{stage.name}-", dir=reports))
        FlextInfraUtilitiesCodemodRules.codemod_stage_scan_ruleset(
            m.Infra.CodemodRulePlan(
                provider_order=tuple(ruleset.provider for ruleset in rulesets),
                rules=rules,
                rulesets=rulesets,
                project_rule_ids={root: tuple(sorted(rule_ids))},
            ),
            staging,
        )
        cls.codemod_write_generated(staging, generated, frozenset(generated_rules))
        retired = reports / f".{stage.name}-retired"
        if final.exists():
            Path(final).replace(retired)
        Path(staging).replace(final)
        if retired.exists():
            shutil.rmtree(retired)
        staged_ids = tuple(sorted({*rule_ids, *generated_rules}))
        return m.Infra.CodemodRuleset(
            provider=stage.name,
            config=final / c.Infra.CODEMOD_CONFIG_FILENAME,
            rule_ids=staged_ids,
            fixable_rule_ids=staged_ids,
        )

    @staticmethod
    def codemod_write_generated(
        staging: Path,
        generated: m.Infra.CodemodNativeGenerated,
        rule_ids: frozenset[str],
    ) -> None:
        """Write the generated utilities and the selected generated rules natively.

        A staged native configuration (a cascade stage or a fixture root)
        sees every generated utility under its ``utilDirs`` entry and the
        selected generated rules under its ``ruleDirs`` entry, by identity.

        """
        utilities = staging / c.Infra.CODEMOD_UTIL_DIRS_KEY
        rules = staging / c.Infra.CODEMOD_RULE_DIRS_KEY
        u.Cli.ensure_dir(utilities).unwrap()
        u.Cli.ensure_dir(rules).unwrap()
        for identity, document in generated.utilities.items():
            u.Cli.yaml_dump(
                utilities / f"{identity}{c.Infra.CODEMOD_RULE_SUFFIX}", document
            ).unwrap()
        for identity in sorted(rule_ids):
            u.Cli.yaml_dump(
                rules / f"{identity}{c.Infra.CODEMOD_RULE_SUFFIX}",
                generated.rules[identity],
            ).unwrap()

    @staticmethod
    def _preview_contents(preview: Path) -> t.MappingKV[Path, bytes]:
        """Read every Python source of the staged preview by relative path.

        Returns:
            Relative path to its current bytes.

        """
        return {
            path.relative_to(preview): path.read_bytes()
            for path in sorted(preview.rglob(f"*{c.Infra.EXT_PYTHON}"))
        }

    @classmethod
    def _run_native_stage(
        cls, preview: Path, binary: Path, ruleset: m.Infra.CodemodRuleset
    ) -> None:
        """Apply one staged ruleset with ast-grep's own ``--update-all``.

        Raises:
            RuntimeError: If ast-grep does not exit successfully.

        """
        command = FlextInfraUtilitiesBase.ast_grep_scan_command(
            ruleset.config,
            rule_ids=ruleset.rule_ids,
            targets=(".",),
            update_all=True,
        )
        executed = u.Cli.run_raw((str(binary), *command[1:]), cwd=preview).unwrap()
        if not u.Cli.process_succeeded(executed.outcome):
            msg = (
                f"ast-grep native stage {ruleset.provider} failed "
                f"(exit {executed.outcome.raw_return_code}): "
                f"{(executed.stderr or executed.stdout).strip()}"
            )
            raise RuntimeError(msg)

    @staticmethod
    def _run_ruff_stage(
        project: Path,
        preview: Path,
        stage: m.Infra.ModStageConfig,
        originals: t.MappingKV[Path, bytes],
    ) -> None:
        """Repair the selected Ruff codes on every source the cascade changed.

        Ruff reads each source on stdin under its live destination name, so
        the owning project's configuration decides first-party imports.

        """
        for relative, original in originals.items():
            path = preview / relative
            current = path.read_bytes()
            if current == original:
                continue
            repaired = FlextInfraUtilitiesProtectedEditLinting.ruff_select_fix(
                project / relative,
                current.decode(c.DEFAULT_ENCODING),
                stage.select,
            ).unwrap()
            path.write_bytes(repaired.encode(c.DEFAULT_ENCODING))

    @classmethod
    def codemod_native_cascade(
        cls,
        project: Path,
        plan: m.Infra.CodemodRulePlan,
        sources: t.MappingKV[Path, bytes],
        generated: m.Infra.CodemodNativeGenerated,
    ) -> t.MappingKV[Path, bytes]:
        """Run every declared stage over a staged preview to its fixed point.

        ``sources`` are the project's authored Python sources (absolute path
        to current bytes); generated projections and stubs never enter the
        preview. ``generated`` holds the project's generated utilities and
        rules rendered in memory. The stage sequence repeats until one whole
        pass changes no byte; ``mod.phases.pass-cap`` passes without that
        fixed point fail.

        Returns:
            Absolute path to new bytes for every source the cascade changed.

        Raises:
            RuntimeError: If the cascade does not converge within the cap.

        """
        root = project.absolute()
        phases = config.Infra.tooling.mod.phases
        staged = [
            (stage, cls.codemod_native_stage(root, plan, stage, generated))
            if stage.kind is c.Infra.ModStageKind.NATIVE
            else (stage, None)
            for stage in phases.stages
        ]
        originals = {
            path.relative_to(root): content
            for path, content in sorted(sources.items())
            if path.suffix == c.Infra.EXT_PYTHON
            and path.is_relative_to(root)
            and not content.startswith(
                c.Infra.AUTOGEN_HEADER.encode(c.DEFAULT_ENCODING)
            )
        }
        if not originals or all(
            ruleset is None
            for stage, ruleset in staged
            if stage.kind is c.Infra.ModStageKind.NATIVE
        ):
            return {}
        binary = cls.codemod_tool_binary(c.Infra.SG)
        u.Cli.ensure_dir(settings.work_dir).unwrap()
        with tempfile.TemporaryDirectory(
            prefix="mod-native-cascade-", dir=settings.work_dir
        ) as directory:
            preview = Path(directory)
            for relative, content in originals.items():
                u.Cli.ensure_dir((preview / relative).parent).unwrap()
                (preview / relative).write_bytes(content)
            for _pass in range(phases.pass_cap):
                before = cls._preview_contents(preview)
                for stage, ruleset in staged:
                    if ruleset is not None:
                        cls._run_native_stage(preview, binary, ruleset)
                    elif stage.kind is c.Infra.ModStageKind.RUFF:
                        cls._run_ruff_stage(root, preview, stage, originals)
                after = cls._preview_contents(preview)
                if after == before:
                    return {
                        root / relative: content
                        for relative, content in after.items()
                        if originals[relative] != content
                    }
        msg = (
            f"native cascade did not reach its fixed point within "
            f"{phases.pass_cap} passes: {root}"
        )
        raise RuntimeError(msg)


__all__: list[str] = ["FlextInfraUtilitiesCodemodNativeCascade"]
