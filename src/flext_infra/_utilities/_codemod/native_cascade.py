"""Native ast-grep cascade: one staged sgconfig per stage, to a fixed point.

Every fixable rule that is neither an owned-path rule nor a rope relocation
applies through ast-grep's own ``scan --update-all``. The engine stages one
native configuration per declared stage under the project's
``.reports/codemod/native/<stage>``, so
``ast-grep scan -c <that sgconfig.yml> --update-all`` reproduces the stage by
hand. The cascade runs every stage in the declared order over one staged
preview of the project's authored sources, repeats the sequence until no byte
changes, and returns the changed sources for a single publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import concurrent.futures
import difflib
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from itertools import islice
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, settings
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesMiseBinary,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProtectedEditLinting,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodRules


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
    def codemod_native_eligible(rule: p.Infra.CodemodRule) -> bool:
        """Whether ast-grep alone applies the rule: a fix and no engine step.

        Returns:
            True for a fixable rule without an owned path or a relocation.

        """
        return (
            rule.fixable and rule.owned_path_suffix is None and rule.relocation is None
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
    def _stage_claims(cls, stage: p.Infra.ModStageConfig, rule_id: str) -> bool:
        """Whether a native stage owns one rule id.

        A stage with shapes owns exactly those generated shapes; the catalog
        stage owns every id no shaped stage claims.

        Returns:
            True when the id belongs to the stage.

        """
        shape = cls._rule_shape(rule_id)
        if stage.shapes:
            return shape in stage.shapes
        return not any(
            shape in other.shapes for other in config.Infra.tooling.mod.phases.stages
        )

    @classmethod
    def codemod_native_stage(
        cls,
        project: Path,
        plan: p.Infra.CodemodRulePlan,
        stage: p.Infra.ModStageConfig,
    ) -> p.Infra.CodemodRuleset | None:
        """Write one stage's native configuration under the project's reports.

        The stage directory holds the elected rules the stage owns, catalog
        and generated providers alike, with their provider utilities. It
        replaces the previous stage directory in one rename; a stage that
        owns no rule leaves no directory behind.

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
        reports = root / c.Infra.MOD_NATIVE_STAGE_RELATIVE_PATH
        final = reports / stage.name
        u.Cli.ensure_dir(reports).unwrap()
        if not rules:
            if final.exists():
                shutil.rmtree(final)
            return None
        rule_ids = frozenset(rule.id for rule in rules)
        staging = Path(tempfile.mkdtemp(prefix=f".{stage.name}-", dir=reports))
        FlextInfraUtilitiesCodemodRules.codemod_stage_scan_ruleset(
            FlextInfraUtilitiesCodemodRules.project_plan(plan, root, rule_ids),
            staging,
        )
        retired = reports / f".{stage.name}-retired"
        if final.exists():
            final.replace(retired)
        staging.replace(final)
        if retired.exists():
            shutil.rmtree(retired)
        staged_ids = tuple(sorted(rule_ids))
        return m.Infra.CodemodRuleset(
            provider=stage.name,
            config=final / c.Infra.CODEMOD_CONFIG_FILENAME,
            rule_ids=staged_ids,
            fixable_rule_ids=staged_ids,
        )

    @staticmethod
    def _preview_contents(preview: Path) -> Mapping[Path, bytes]:
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
        cls, preview: Path, binary: Path, ruleset: p.Infra.CodemodRuleset
    ) -> None:
        """Apply one staged ruleset through ``--update-all`` until it settles.

        One ``--update-all`` applies a single fix per overlapping range: the
        generated header documents all anchor on a module's first import, so
        each run binds one more name. The stage therefore reruns until a run
        changes no byte. Every fix of a converging ruleset removes its own
        match, so a ruleset settles within one run per rule; a repeated
        preview state, or a run past that bound, is an oscillation.

        Raises:
            RuntimeError: If ast-grep does not exit successfully, or the
                ruleset does not settle.

        """
        threads = getattr(
            getattr(getattr(config.Infra, "tooling", None), "mod", None),
            "scan_threads",
            getattr(
                getattr(getattr(config.Infra, "codegen", None), "make", None),
                "scan_threads",
                4,
            ),
        )
        command = FlextInfraUtilitiesBase.ast_grep_scan_command(
            ruleset.config,
            rule_ids=ruleset.rule_ids,
            targets=(".",),
            update_all=True,
            threads=threads,
        )
        current = cls._preview_contents(preview)
        seen = {frozenset(current.items())}
        # Why: a nested match needs one pass per nesting level, so the
        # one-run-per-rule bound is not a fixed-point ceiling. The repeated
        # state check still rejects a real oscillation.
        pass_ceiling = max(len(ruleset.rule_ids) + 1, c.Infra.NATIVE_CASCADE_MAX_PASSES)
        changed: tuple[Path, ...] = ()
        for _run in range(pass_ceiling):
            executed = u.Cli.run_raw((str(binary), *command[1:]), cwd=preview).unwrap()
            if not u.Cli.process_succeeded(executed.outcome):
                msg = (
                    f"ast-grep native stage {ruleset.provider} failed "
                    f"(exit {executed.outcome.raw_return_code}): "
                    f"{(executed.stderr or executed.stdout).strip()}"
                )
                raise RuntimeError(msg)
            settled = cls._preview_contents(preview)
            if settled == current:
                return
            changed = tuple(
                path for path in settled if settled[path] != current.get(path)
            )
            state = frozenset(settled.items())
            if state in seen:
                break
            seen.add(state)
            current = settled
        rewriting = sorted(cls._matching_rule_ids(preview, binary, ruleset, changed))
        msg = (
            f"ast-grep native stage {ruleset.provider} does not settle: "
            f"rules {rewriting} keep rewriting "
            f"{[path.as_posix() for path in changed]}"
        )
        raise RuntimeError(msg)

    @staticmethod
    def _matching_rule_ids(
        preview: Path,
        binary: Path,
        ruleset: p.Infra.CodemodRuleset,
        paths: Sequence[Path],
    ) -> frozenset[str]:
        """Name the staged rules that still match the files of the last pass.

        Returns:
            The rule ids ast-grep reports on ``paths``, without rewriting.

        """
        if not paths:
            return frozenset()
        threads = getattr(
            getattr(getattr(config.Infra, "tooling", None), "mod", None),
            "scan_threads",
            getattr(
                getattr(getattr(config.Infra, "codegen", None), "make", None),
                "scan_threads",
                4,
            ),
        )
        command = FlextInfraUtilitiesBase.ast_grep_scan_command(
            ruleset.config,
            rule_ids=ruleset.rule_ids,
            targets=tuple(path.as_posix() for path in paths),
            json_stream=True,
            threads=threads,
        )
        executed = u.Cli.run_raw((str(binary), *command[1:]), cwd=preview).unwrap()
        return frozenset(
            str(u.Cli.json_as_mapping(u.Cli.json_loads(line).unwrap())["ruleId"])
            for line in (executed.stdout or "").splitlines()
            if line.strip()
        )

    @staticmethod
    def _run_ruff_stage(
        project: Path,
        preview: Path,
        stage: p.Infra.ModStageConfig,
        originals: Mapping[Path, bytes],
    ) -> None:
        """Repair the selected Ruff codes on every source the cascade changed.

        Ruff reads each source on stdin under its live destination name, so
        the owning project's configuration decides first-party imports.
        Independent calls use the configured lint worker bound. Results and
        preview writes retain source order; the executor joins every worker
        before the stage returns or propagates an error.

        """

        def repair(relative: Path, original: bytes) -> p.Result[str] | None:
            path = preview / relative
            current = path.read_bytes()
            if current == original:
                return None
            return FlextInfraUtilitiesProtectedEditLinting.ruff_select_fix(
                project / relative,
                current.decode(c.DEFAULT_ENCODING),
                stage.select,
            )

        workers = config.Infra.codegen.lint_snapshot_workers
        pending = iter(originals.items())
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            while batch := tuple(islice(pending, workers)):
                futures = tuple(
                    (relative, pool.submit(repair, relative, original))
                    for relative, original in batch
                )
                for relative, future in futures:
                    repaired = future.result()
                    if repaired is not None:
                        (preview / relative).write_bytes(
                            repaired.unwrap().encode(c.DEFAULT_ENCODING)
                        )

    @classmethod
    def native_cascade(
        cls,
        project: Path,
        plan: p.Infra.CodemodRulePlan,
        sources: Mapping[Path, bytes],
    ) -> Mapping[Path, bytes]:
        """Run every declared stage over a staged preview to its fixed point.

        ``sources`` are the project's authored Python sources (absolute path
        to current bytes); generated projections and stubs never enter the
        preview. The plan carries the project's generated provider, so its
        rendered rules stage with the catalogs. The stage sequence repeats
        until one whole pass changes no byte; ``mod.phases.pass-cap`` passes
        without that fixed point fail.

        Returns:
            Absolute path to new bytes for every source the cascade changed.

        Raises:
            RuntimeError: If the cascade does not converge within the cap.

        """
        root = project.absolute()
        phases = config.Infra.tooling.mod.phases
        staged = [
            (stage, cls.codemod_native_stage(root, plan, stage))
            if stage.kind == c.Infra.ModStageKind.NATIVE
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
            if stage.kind == c.Infra.ModStageKind.NATIVE
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
            before = after = cls._preview_contents(preview)
            for _pass in range(phases.pass_cap):
                before = after
                for stage, ruleset in staged:
                    if ruleset is not None:
                        cls._run_native_stage(preview, binary, ruleset)
                    elif stage.kind == c.Infra.ModStageKind.RUFF:
                        cls._run_ruff_stage(root, preview, stage, originals)
                after = cls._preview_contents(preview)
                if after == before:
                    return {
                        root / relative: content
                        for relative, content in after.items()
                        if originals[relative] != content
                    }
            oscillating = sorted(
                relative
                for relative, content in after.items()
                if before.get(relative) != content
            )
            first = oscillating[0]
            last_pass = "".join(
                difflib.unified_diff(
                    before[first].decode(c.DEFAULT_ENCODING).splitlines(keepends=True),
                    after[first].decode(c.DEFAULT_ENCODING).splitlines(keepends=True),
                    fromfile=f"{first.as_posix()} (pass start)",
                    tofile=f"{first.as_posix()} (pass end)",
                )
            )
        msg = (
            f"native cascade did not reach its fixed point within "
            f"{phases.pass_cap} passes: {root}; still changing in the last "
            f"pass: {', '.join(item.as_posix() for item in oscillating)}\n"
            f"{last_pass}"
        )
        raise RuntimeError(msg)


__all__: list[str] = ["FlextInfraUtilitiesCodemodNativeCascade"]
