"""Compose inherited ast-grep rules from FLEXT distribution metadata.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, Sequence
from functools import lru_cache
from pathlib import Path

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesResourceLimits,
)
from flext_infra._utilities._codemod_rules_distributions import (
    FlextInfraUtilitiesCodemodRulesDistributionsMixin,
)


class FlextInfraUtilitiesCodemodRules(
    FlextInfraUtilitiesCodemodRulesDistributionsMixin,
):
    """Resolve universal, runtime-transitive, and local ast-grep rule layers."""

    @staticmethod
    def _read_provider_declaration(config_path: Path) -> t.JsonMapping:
        """Read and parse one provider's codemod config declaration.

        Returns:
            The parsed provider declaration mapping.

        Raises:
            ValueError: If the provider config content is absent.


        """
        state = u.Cli.atomic_read_binary_file_state(config_path, required=True).unwrap()
        if state.content is None:
            msg = f"codemod provider config is absent: {config_path}"
            raise ValueError(msg)
        return u.Cli.yaml_parse(state.content.decode(c.DEFAULT_ENCODING)).unwrap()

    @staticmethod
    def _merge_native_config(
        native_config: t.JsonDict,
        declaration: t.JsonMapping,
        config_path: Path,
    ) -> None:
        """Merge the declaration's non-projected keys into the native config.

        Raises:
            ValueError: If two providers declare conflicting native values.

        """
        projected_inputs = {
            c.Infra.CODEMOD_RULE_DIRS_KEY,
            c.Infra.CODEMOD_UTIL_DIRS_KEY,
            c.Infra.CODEMOD_TEST_CONFIGS_KEY,
            c.Infra.CODEMOD_SCOPE_KEY,
        }
        for key, value in declaration.items():
            if key in projected_inputs:
                continue
            if key in native_config and native_config[key] != value:
                msg = f"native codemod configuration conflicts for {key}: {config_path}"
                raise ValueError(msg)
            native_config[key] = value

    @staticmethod
    def _validated_utility_directories(
        raw_directories: t.JsonValue,
        config_path: Path,
    ) -> t.VariadicTuple[Path]:
        """Validate and resolve one declaration's utility directories.

        Returns:
            The resolved utility directories contained in the provider owner.

        Raises:
            ValueError: If the directories are not a sequence of existing
                paths inside the provider owner.
            TypeError: If codemod utility directories are not a sequence; or if codemod
                utility directory is not a path.

        """
        if not isinstance(raw_directories, Sequence) or isinstance(
            raw_directories, str
        ):
            msg = f"codemod utility directories are not a sequence: {config_path}"
            raise TypeError(msg)
        directories: list[Path] = []
        for relative in raw_directories:
            if not isinstance(relative, str):
                msg = f"codemod utility directory is not a path: {config_path}"
                raise TypeError(msg)
            directory = (config_path.parent / relative).resolve()
            if not directory.is_relative_to(config_path.parent):
                msg = f"codemod utility directory escapes its owner: {directory}"
                raise ValueError(msg)
            if not directory.is_dir():
                msg = f"codemod utility directory is absent: {directory}"
                raise ValueError(msg)
            directories.append(directory)
        return tuple(directories)

    @staticmethod
    def _admit_utility_documents(
        path: Path,
        global_documents: t.MutableMappingKV[tuple[str, str], t.JsonMapping],
    ) -> None:
        """Admit one utility file's documents under a unique identity.

        Raises:
            ValueError: If the utility input is absent or one of its
                documents lacks a unique native identity and language.
            TypeError: If codemod utility lacks native identity/language.

        """
        observed = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
        if observed.content is None:
            msg = f"codemod utility input is absent: {path}"
            raise ValueError(msg)
        for document in FlextInfraUtilitiesCodemodRules.parse_yaml_documents(
            observed.content.decode(c.DEFAULT_ENCODING)
        ).unwrap():
            identity = document.get("id")
            language = document.get("language")
            if not isinstance(identity, str) or not isinstance(language, str):
                msg = f"codemod utility lacks native identity/language: {path}"
                raise TypeError(msg)
            key = (language, identity)
            if key in global_documents and global_documents[key] != document:
                msg = f"codemod utility identity is ambiguous: {path}:{identity}"
                raise ValueError(msg)
            global_documents[key] = document

    @classmethod
    def _collect_utility_documents(
        cls,
        declaration: t.JsonMapping,
        config_path: Path,
    ) -> t.MutableMappingKV[tuple[str, str], t.JsonMapping]:
        """Collect one provider's utility documents by language and identity.

        Returns:
            The provider's utility documents keyed by (language, identity).
            Malformed directories or ambiguous documents fail through the
            validation helpers with ``ValueError``.

        """
        global_documents: t.MutableMappingKV[tuple[str, str], t.JsonMapping] = {}
        raw_directories = declaration.get(c.Infra.CODEMOD_UTIL_DIRS_KEY)
        if raw_directories is None:
            return global_documents
        for directory in cls._validated_utility_directories(
            raw_directories, config_path
        ):
            for path in sorted(directory.rglob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}")):
                cls._admit_utility_documents(path, global_documents)
        return global_documents

    @classmethod
    def _project_provider_utilities(
        cls,
        config_path: Path,
        native_config: t.JsonDict,
        aliases: t.MutableMappingKV[Path, t.MutableStrMapping],
        utilities: t.MutableMappingKV[str, t.JsonMapping],
    ) -> None:
        """Project one provider's utilities under qualified global identities.

        Raises:
            TypeError: If projected codemod utility is not a mapping.

        """
        declaration = cls._read_provider_declaration(config_path)
        cls._merge_native_config(native_config, declaration, config_path)
        global_documents = cls._collect_utility_documents(declaration, config_path)
        namespace = u.Cli.sha256_content(
            u.Cli.json_dumps(
                [dict(global_documents[key]) for key in sorted(global_documents)],
                sort_keys=True,
            ).unwrap()
        )
        qualified = {
            identity: u.Cli.sha256_content(namespace + "\0" + identity)
            for _language, identity in global_documents
        }
        aliases[config_path] = qualified
        for document in global_documents.values():
            projected = cls._qualified_global_matches(document, qualified)
            if not isinstance(projected, Mapping):
                msg = "projected codemod utility is not a mapping"
                raise TypeError(msg)
            projected = {**projected, "id": qualified[str(document["id"])]}
            serialized = u.Cli.json_dumps(projected, sort_keys=True).unwrap()
            utilities[u.Cli.sha256_content(serialized)] = projected

    @classmethod
    def _project_rule_document(
        cls,
        rule: m.Infra.CodemodRule,
        documents: t.MutableMappingKV[Path, t.SequenceOf[t.JsonMapping]],
        rule_directory: Path,
        aliases: t.MappingKV[Path, t.MutableStrMapping],
    ) -> None:
        """Project one elected rule document under its owning provider aliases.

        Raises:
            ValueError: If the rule input is absent, its election is
                ambiguous, or it changed before projection.

        """
        path = rule.resource.resolve()
        if path not in documents:
            observed = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if observed.content is None:
                msg = f"codemod rule input is absent: {path}"
                raise ValueError(msg)
            documents[path] = cls.parse_yaml_documents(
                observed.content.decode(c.DEFAULT_ENCODING)
            ).unwrap()
        elected = [
            document for document in documents[path] if document.get("id") == rule.id
        ]
        if len(elected) != 1:
            msg = f"elected codemod rule document is ambiguous: {path}:{rule.id}"
            raise ValueError(msg)
        document = elected[0]
        declared = cls._validated_document_rule(rule.provider, path, document).unwrap()
        if declared.digest != rule.digest:
            msg = f"elected codemod rule changed before projection: {path}:{rule.id}"
            raise ValueError(msg)
        owner = max(
            (config for config in aliases if path.is_relative_to(config.parent)),
            key=lambda config: len(config.parent.parts),
        )
        projected = cls._qualified_global_matches(document, aliases[owner])
        u.Cli.yaml_dump(
            rule_directory
            / f"{u.Cli.sha256_content(rule.id)}{c.Infra.CODEMOD_RULE_SUFFIX}",
            projected,
        ).unwrap()

    @classmethod
    def codemod_stage_scan_ruleset(
        cls, plan: m.Infra.CodemodRulePlan, destination: Path
    ) -> m.Infra.CodemodRuleset:
        """Project elected documents and scoped utilities into one native scan.

        Absent inputs, conflicting native configuration, ambiguous utility
        identities, and rule drift fail through the validation helpers with
        ``ValueError``.

        Returns:
            The staged native scan ruleset and its projected configuration.

        Raises:
            ValueError: If native rule IDs collide across the elected providers.

        """
        if len({rule.id for rule in plan.rules}) != len(plan.rules):
            msg = "native codemod rule IDs must be unique across providers"
            raise ValueError(msg)
        rule_directory = destination / c.Infra.CODEMOD_RULE_DIRS_KEY
        utility_directory = destination / c.Infra.CODEMOD_UTIL_DIRS_KEY
        u.Cli.ensure_dir(rule_directory).unwrap()
        u.Cli.ensure_dir(utility_directory).unwrap()
        native_config: t.JsonDict = {}
        aliases: t.MutableMappingKV[Path, t.MutableStrMapping] = {}
        documents: t.MutableMappingKV[Path, t.SequenceOf[t.JsonMapping]] = {}
        utilities: t.MutableMappingKV[str, t.JsonMapping] = {}
        for ruleset in plan.rulesets:
            cls._project_provider_utilities(
                ruleset.config.resolve(),
                native_config,
                aliases,
                utilities,
            )
        for digest, document in utilities.items():
            u.Cli.yaml_dump(
                utility_directory / f"{digest}{c.Infra.CODEMOD_RULE_SUFFIX}", document
            ).unwrap()
        for rule in plan.rules:
            cls._project_rule_document(rule, documents, rule_directory, aliases)
        native_config[c.Infra.CODEMOD_RULE_DIRS_KEY] = [rule_directory.name]
        native_config[c.Infra.CODEMOD_UTIL_DIRS_KEY] = [utility_directory.name]
        config_path = destination / c.Infra.CODEMOD_CONFIG_FILENAME
        u.Cli.yaml_dump(config_path, native_config).unwrap()
        return m.Infra.CodemodRuleset(
            provider=",".join(plan.provider_order),
            config=config_path,
            rule_ids=tuple(rule.id for rule in plan.rules),
            fixable_rule_ids=tuple(rule.id for rule in plan.rules if rule.fixable),
        )

    @classmethod
    def _qualified_global_matches(
        cls,
        value: t.JsonMapping | t.JsonValue,
        aliases: t.StrMapping,
        local_names: frozenset[str] = frozenset(),
    ) -> t.JsonValue:
        """Preserve native local utility shadows while qualifying provider globals.

        Returns:
            The value with provider-global ``matches`` references qualified.

        Raises:
            ValueError: If a qualified global utility conflicts with a
                native local utility.

        """
        if isinstance(value, Mapping):
            local = value.get("utils")
            shadows = (
                local_names | frozenset(local) if u.mapping(local) else local_names
            )
            if u.mapping(local) and set(aliases.values()).intersection(local):
                msg = "qualified global utility conflicts with a native local utility"
                raise ValueError(msg)
            return {
                key: (
                    item
                    if key == c.Infra.CODEMOD_RULE_METADATA_KEY
                    else aliases[item]
                    if key == "matches"
                    and isinstance(item, str)
                    and item in aliases
                    and item not in shadows
                    else cls._qualified_global_matches(item, aliases, shadows)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                cls._qualified_global_matches(item, aliases, local_names)
                for item in value
            ]
        return value

    @classmethod
    def codemod_rule_plan(
        cls,
        root: Path,
        *,
        rule_ids: t.StrSequence | None = None,
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        """Build the sole executable rule plan for check and mutation.

        Every call reads the current rule files; parsing is reused only for
        byte-identical catalogs (``_cached_rules``), so an edited rule is never
        served stale, within one process or across processes.

        Returns:
            The resulting ``p.Result[m.Infra.CodemodRulePlan]``.

        """
        plans: list[m.Infra.CodemodRulePlan] = []
        for project_root in FlextInfraUtilitiesProjectDiscovery.governed_project_roots(
            root
        ):
            planned = cls._project_rule_plan(project_root)
            if planned.failure:
                return r[m.Infra.CodemodRulePlan].from_failure(planned)
            plans.append(planned.value)
        composed = cls._union_plans(tuple(plans))
        if composed.failure or rule_ids is None:
            return composed
        if not rule_ids or any(not rule_id.strip() for rule_id in rule_ids):
            return r[m.Infra.CodemodRulePlan].fail(
                "codemod rule selection requires non-empty exact rule IDs",
            )
        selected = frozenset(rule_ids)
        if len(selected) != len(rule_ids):
            return r[m.Infra.CodemodRulePlan].fail(
                "duplicate codemod rule IDs in selection",
            )
        plan = composed.value
        unknown = selected.difference(rule.id for rule in plan.rules)
        if unknown:
            return r[m.Infra.CodemodRulePlan].fail(
                "unknown codemod rule IDs: " + ", ".join(sorted(unknown)),
            )
        rulesets = tuple(
            ruleset.model_copy(
                update={
                    field: tuple(
                        rule_id
                        for rule_id in getattr(ruleset, field)
                        if rule_id in selected
                    )
                    for field in ("rule_ids", "fixable_rule_ids")
                }
            )
            for ruleset in plan.rulesets
            if selected.intersection(ruleset.rule_ids)
        )
        return r[m.Infra.CodemodRulePlan].ok(
            plan.model_copy(
                update={
                    "provider_order": tuple(ruleset.provider for ruleset in rulesets),
                    "rules": tuple(rule for rule in plan.rules if rule.id in selected),
                    "rulesets": rulesets,
                    "project_rule_ids": {
                        project: tuple(rule for rule in rules if rule in selected)
                        for project, rules in plan.project_rule_ids.items()
                    },
                }
            ),
        )

    @classmethod
    def _project_rule_plan(cls, root: Path) -> p.Result[m.Infra.CodemodRulePlan]:
        """Elect providers against one project's declared runtime dependencies.

        Returns:
            The project's applicable rule plan.

        """
        project = cls.codemod_project_requirements(root)
        if project.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(project)
        root_name, direct_runtime = project.value
        paths = cls._import_paths()
        indexed = cls._indexed_distributions(paths)
        discovered = cls._indexed_provider_configs(paths)
        runtime_closure = cls.codemod_runtime_closure(direct_runtime, indexed)
        # Universal scope is a fleet law: it applies to every project,
        # the provider's own home repository included. Runtime scope is
        # consumer-targeting (see the provider sgconfig contract), so a
        # distribution never elects itself through its consumers' graph.
        universal_result = cls._providers(
            discovered,
            scope=c.Infra.CODEMOD_SCOPE_UNIVERSAL,
            selected=frozenset(indexed),
        )
        if universal_result.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(universal_result)
        runtime_result = cls._providers(
            discovered,
            scope=c.Infra.CODEMOD_SCOPE_RUNTIME,
            selected=runtime_closure.difference({root_name}),
        )
        if runtime_result.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(runtime_result)
        universal, runtime = universal_result.value, runtime_result.value
        providers: list[t.Pair[str, Path]] = []
        for name in (
            *cls._provider_order(universal, indexed),
            *cls._provider_order(runtime, indexed),
        ):
            provider_config = universal.get(name) or runtime.get(name)
            if provider_config is None:
                return r[m.Infra.CodemodRulePlan].fail(
                    f"codemod provider disappeared from resolved graph: {name}",
                )
            providers.append((name, provider_config))
        local_config = root / c.Infra.CODEMOD_CONFIG_RELPATH
        if local_config.is_file():
            providers = [
                (name, local_config if name == root_name else provider_config)
                for name, provider_config in providers
            ]
            if all(name != root_name for name, _config in providers):
                providers.append((root_name, local_config))
        return cls._compose(tuple(providers), root_name, runtime_closure, root)

    @staticmethod
    def _union_plans(
        plans: t.SequenceOf[m.Infra.CodemodRulePlan],
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        """Scan shared catalogs once while retaining each project's election.

        Returns:
            The conflict-free union with project-specific applicability.

        """
        rules: t.MutableMappingKV[str, m.Infra.CodemodRule] = {}
        rulesets: t.MutableMappingKV[Path, m.Infra.CodemodRuleset] = {}
        projects: t.MutableMappingKV[Path, t.StrSequence] = {}
        for plan in plans:
            projects.update(plan.project_rule_ids)
            for rule in plan.rules:
                previous = rules.get(rule.id)
                if previous is not None and previous.digest != rule.digest:
                    return r[m.Infra.CodemodRulePlan].fail(
                        f"conflicting governed codemod rule {rule.id}: "
                        f"{previous.resource} != {rule.resource}",
                    )
                rules.setdefault(rule.id, rule)
            for ruleset in plan.rulesets:
                elected = tuple(
                    rule_id
                    for rule_id in ruleset.rule_ids
                    if rules[rule_id].provider == ruleset.provider
                )
                if not elected:
                    continue
                elected_ruleset = ruleset.model_copy(
                    update={
                        "rule_ids": elected,
                        "fixable_rule_ids": tuple(
                            rule_id
                            for rule_id in ruleset.fixable_rule_ids
                            if rule_id in elected
                        ),
                    }
                )
                key = elected_ruleset.config.resolve()
                previous = rulesets.get(key)
                rulesets[key] = (
                    elected_ruleset
                    if previous is None
                    else previous.model_copy(
                        update={
                            field: tuple(
                                dict.fromkeys(
                                    (
                                        *getattr(previous, field),
                                        *getattr(elected_ruleset, field),
                                    ),
                                )
                            )
                            for field in ("rule_ids", "fixable_rule_ids")
                        }
                    )
                )
        return r[m.Infra.CodemodRulePlan].ok(
            m.Infra.CodemodRulePlan(
                provider_order=tuple(ruleset.provider for ruleset in rulesets.values()),
                rules=tuple(rules.values()),
                rulesets=tuple(rulesets.values()),
                project_rule_ids=projects,
            ),
        )

    @staticmethod
    def codemod_rule_filter(rule_ids: t.StrSequence) -> str:
        """Return one exact ast-grep rule-ID filter for an elected ruleset.

        Returns:
            One exact ast-grep rule-ID filter for an elected ruleset.

        Raises:
            ValueError: If codemod rule filter requires at least one rule ID.

        """
        if not rule_ids:
            msg = "codemod rule filter requires at least one rule ID"
            raise ValueError(msg)
        return "^(?:" + "|".join(re.escape(rule_id) for rule_id in rule_ids) + ")$"

    @staticmethod
    def _rule_out_of_scope(
        rule: m.Infra.CodemodRule,
        root_name: str,
        runtime_closure: frozenset[str],
    ) -> bool:
        """Whether one rule's declared distribution excludes this plan.

        A rule that bans a library outside its owning project declares the
        owner's distribution under ``metadata.owner``: the owner's own plan
        never elects it, every other project's plan does. A rule that binds
        only the consumers of a facade declares that distribution under
        ``metadata.consumers_of``: a plan elects it only when the facade is in
        the project's runtime closure, so the facade itself and the projects
        below it never do.

        Returns:
            The resulting ``bool``.

        """
        if rule.owner is not None and canonicalize_name(rule.owner) == root_name:
            return True
        return (
            rule.consumers_of is not None
            and canonicalize_name(rule.consumers_of) not in runtime_closure
        )

    @staticmethod
    def _existing_rule_conflict(
        previous: m.Infra.CodemodRule,
        rule: m.Infra.CodemodRule,
        provider: str,
    ) -> str | None:
        """Return the conflict message when a selected rule id clashes.

        Returns:
            The resulting ``str | None``.

        """
        if previous.provider == provider:
            return f"duplicate codemod rule id in {provider}: {rule.id}"
        if previous.digest != rule.digest:
            return (
                "conflicting codemod rule id "
                f"{rule.id}: {previous.provider}:{previous.resource} "
                f"({previous.digest}) != {rule.provider}:{rule.resource} "
                f"({rule.digest})"
            )
        return None

    @classmethod
    def _provider_ruleset(
        cls,
        provider: str,
        provider_config: Path,
        selected: t.MutableMappingKV[str, m.Infra.CodemodRule],
        root_name: str,
        runtime_closure: frozenset[str],
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRuleset]]:
        """Elect one provider's rules into its zero-or-one ruleset sequence.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodemodRuleset]]``.

        """
        parsed = cls.codemod_catalog_rules(provider, provider_config)
        if parsed.failure:
            return r[t.SequenceOf[m.Infra.CodemodRuleset]].from_failure(parsed)
        elected: list[str] = []
        fixable: list[str] = []
        for rule in parsed.value:
            if cls._rule_out_of_scope(rule, root_name, runtime_closure):
                continue
            previous = selected.get(rule.id)
            if previous is not None:
                conflict = cls._existing_rule_conflict(previous, rule, provider)
                if conflict is not None:
                    return r[t.SequenceOf[m.Infra.CodemodRuleset]].fail(conflict)
                continue
            selected[rule.id] = rule
            elected.append(rule.id)
            if rule.fixable:
                fixable.append(rule.id)
        if not elected:
            return r[t.SequenceOf[m.Infra.CodemodRuleset]].ok(())
        return r[t.SequenceOf[m.Infra.CodemodRuleset]].ok(
            (
                m.Infra.CodemodRuleset(
                    provider=provider,
                    config=provider_config,
                    rule_ids=tuple(elected),
                    fixable_rule_ids=tuple(fixable),
                ),
            ),
        )

    @classmethod
    def _compose(
        cls,
        providers: t.SequenceOf[t.Pair[str, Path]],
        root_name: str,
        runtime_closure: frozenset[str],
        root: Path,
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        """Elect every provider rule once, honouring each rule's declared scope.

        Returns:
            The resulting ``p.Result[m.Infra.CodemodRulePlan]``.

        """
        selected: MutableMapping[str, m.Infra.CodemodRule] = {}
        rulesets: list[m.Infra.CodemodRuleset] = []
        provider_order: list[str] = []
        for provider, provider_config in providers:
            if provider in provider_order:
                return r[m.Infra.CodemodRulePlan].fail(
                    f"codemod provider declared more than once: {provider}",
                )
            provider_order.append(provider)
            ruleset = cls._provider_ruleset(
                provider,
                provider_config,
                selected,
                root_name,
                runtime_closure,
            )
            if ruleset.failure:
                return r[m.Infra.CodemodRulePlan].from_failure(ruleset)
            rulesets.extend(ruleset.value)
        if not selected:
            return r[m.Infra.CodemodRulePlan].fail("no ast-grep rules discovered")
        return r[m.Infra.CodemodRulePlan].ok(
            m.Infra.CodemodRulePlan(
                provider_order=tuple(provider_order),
                rules=tuple(selected.values()),
                rulesets=tuple(rulesets),
                project_rule_ids={root.resolve(): tuple(selected)},
            ),
        )

    @classmethod
    def codemod_catalog_rules(
        cls,
        provider: str,
        config: Path,
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        """Read every validated catalog declaration before execution election.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodemodRule]]``.

        """
        parsed_config = u.Cli.yaml_parse(
            config.read_text(encoding=c.DEFAULT_ENCODING),
        )
        if parsed_config.failure:
            return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(parsed_config)
        raw_dirs = parsed_config.value.get(c.Infra.CODEMOD_RULE_DIRS_KEY)
        if not isinstance(raw_dirs, Sequence) or isinstance(raw_dirs, str):
            return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                f"codemod config ruleDirs must be a sequence: {config}",
            )
        sources: list[t.Pair[Path, str]] = []
        config_root = config.parent.resolve()
        for raw_dir in raw_dirs:
            if not isinstance(raw_dir, str) or not raw_dir.strip():
                return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                    f"codemod config has invalid ruleDirs entry: {config}",
                )
            rule_dir = (config_root / raw_dir).resolve()
            if not rule_dir.is_relative_to(config_root):
                return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                    f"codemod ruleDirs escapes provider root: {rule_dir}",
                )
            if not rule_dir.is_dir():
                return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                    f"codemod ruleDirs entry is missing: {rule_dir}",
                )
            sources.extend(
                (resource, resource.read_text(encoding=c.DEFAULT_ENCODING))
                for resource in sorted(rule_dir.rglob("*.yml"))
                if not any(
                    part.startswith("_")
                    for part in resource.relative_to(rule_dir).parts
                )
            )
        return cls._cached_rules(provider, tuple(sources))

    @staticmethod
    def _write_rule_cache(
        cache_file: Path,
        parsed: p.Result[t.SequenceOf[m.Infra.CodemodRule]],
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        """Persist parsed rules to the cache and return the parse result.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodemodRule]]``.

        """
        if parsed.failure:
            return parsed
        payload = u.type_adapter(tuple[m.Infra.CodemodRule, ...]).dump_json(
            tuple(parsed.value),
        )
        directory = u.Cli.ensure_dir(cache_file.parent)
        if directory.failure:
            return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(directory)
        written = u.Cli.atomic_write_text_file(
            cache_file,
            payload.decode(c.DEFAULT_ENCODING),
        )
        if written.failure:
            return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(written)
        return parsed

    @classmethod
    @lru_cache(maxsize=16)
    def _cached_rules(
        cls,
        provider: str,
        sources: t.VariadicTuple[t.Pair[Path, str]],
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        """Serve a provider's rules from the content-keyed persistent cache.

        The key is the sha256 of the provider, every rule file's path and
        text, and this parser's own source: a catalog is parsed once for all
        processes, and any edit to a rule or to the parser is a new key.

        Returns:
            The provider's validated rules, in resource and document order.

        """
        identity = u.Cli.json_dumps([
            provider,
            Path(__file__).read_text(encoding=c.DEFAULT_ENCODING),
            [[str(resource), text] for resource, text in sources],
        ])
        if identity.failure:
            return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(identity)
        cache_file = (
            FlextInfraUtilitiesResourceLimits.external_cache_directory(
                config.Infra.codegen.make.codemod_rules_cache,
            )
            / f"{u.Cli.sha256_content(identity.value)}.json"
        )
        if cache_file.is_file():
            return r[t.SequenceOf[m.Infra.CodemodRule]].ok(
                u.type_adapter(tuple[m.Infra.CodemodRule, ...]).validate_json(
                    cache_file.read_text(encoding=c.DEFAULT_ENCODING),
                ),
            )
        parsed = cls._parse_rules(provider, sources)
        return cls._write_rule_cache(cache_file, parsed)

    @classmethod
    def _rule_binding_result(
        cls,
        parsed_rule: t.JsonMapping,
        context: t.VariadicTuple[m.Infra.CodemodContextCondition],
        rule_id: str,
    ) -> p.Result[str]:
        """Return the rule body when every context variable is captured in it.

        Returns:
            The resulting ``p.Result[str]``.

        """
        body = u.Cli.json_dumps({
            key: value
            for key, value in parsed_rule.items()
            if key != c.Infra.CODEMOD_RULE_METADATA_KEY
        })
        if body.failure:
            return r[str].from_failure(body)
        unbound = sorted(
            variable
            for condition in context
            for variable in (condition.variable, condition.of)
            if variable is not None and f"${variable}" not in body.value
        )
        if unbound:
            return r[str].fail(
                f"ast-grep rule {rule_id} context names variables "
                f"its rule never captures {unbound}",
            )
        return body

    @classmethod
    def _validated_rule_identity(
        cls,
        parsed_rule: t.JsonMapping,
        resource: Path,
    ) -> p.Result[t.Triple[str, str, t.VariadicTuple[int]]]:
        """Validate the rule id, canonical form and declared finding receipt.

        Returns:
            The rule id with its canonical JSON and declared receipt, or the
            first validation failure.

        """
        rule_id = parsed_rule.get("id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            return r[t.Triple[str, str, t.VariadicTuple[int]]].fail(
                f"ast-grep rule document missing id: {resource}",
            )
        canonical = u.Cli.json_dumps(
            dict(parsed_rule),
            sort_keys=True,
        )
        if canonical.failure:
            return r[t.Triple[str, str, t.VariadicTuple[int]]].from_failure(canonical)
        declared = cls._declared_expected(parsed_rule)
        if declared.failure:
            return r[t.Triple[str, str, t.VariadicTuple[int]]].fail(
                f"{declared.error}: {resource}",
            )
        return r[t.Triple[str, str, t.VariadicTuple[int]]].ok(
            (rule_id, canonical.value, declared.value),
        )

    @classmethod
    def _validated_document_rule(
        cls,
        provider: str,
        resource: Path,
        parsed_rule: t.JsonMapping,
    ) -> p.Result[m.Infra.CodemodRule]:
        """Validate one parsed rule document and build its rule record.

        Returns:
            The resulting ``p.Result[m.Infra.CodemodRule]``.

        """
        identity = cls._validated_rule_identity(parsed_rule, resource)
        if identity.failure:
            return r[m.Infra.CodemodRule].from_failure(identity)
        rule_id, canonical_json, declared_receipt = identity.value
        metadata = parsed_rule.get(c.Infra.CODEMOD_RULE_METADATA_KEY)
        declared_metadata: t.JsonMapping = (
            metadata if isinstance(metadata, Mapping) else {}
        )
        context = cls._declared_context(
            declared_metadata.get(c.Infra.CODEMOD_RULE_CONTEXT_KEY),
        )
        if context.failure:
            return r[m.Infra.CodemodRule].fail(f"{context.error}: {resource}")
        binding = cls._rule_binding_result(parsed_rule, context.value, rule_id)
        if binding.failure:
            return r[m.Infra.CodemodRule].fail(f"{binding.error}: {resource}")
        detector = parsed_rule.get("rule")
        negative = detector.get("not") if isinstance(detector, Mapping) else None
        alternatives = negative.get("any") if isinstance(negative, Mapping) else None
        module_absence = (
            isinstance(detector, Mapping)
            and str(parsed_rule["language"]).casefold() == "python"
            and set(detector) == {"kind", "not"}
            and detector.get("kind") == "module"
            and isinstance(negative, Mapping)
            and (
                (set(negative) == {"has"} and isinstance(negative.get("has"), Mapping))
                or (
                    set(negative) == {"any"}
                    and isinstance(alternatives, list)
                    and bool(alternatives)
                    and all(
                        isinstance(item, Mapping)
                        and set(item) == {"has"}
                        and isinstance(item.get("has"), Mapping)
                        for item in alternatives
                    )
                )
            )
            and not context.value
        )
        payload = u.Cli.json_dumps({
            "id": rule_id,
            "digest": u.Cli.sha256_content(canonical_json),
            "provider": provider,
            "resource": str(resource),
            "fixable": "fix" in parsed_rule,
            "module_absence": module_absence,
            "expected": declared_receipt[0] if declared_receipt else None,
            "owner": declared_metadata.get(
                c.Infra.CODEMOD_RULE_OWNER_KEY,
            ),
            "consumers_of": declared_metadata.get(
                c.Infra.CODEMOD_RULE_CONSUMERS_OF_KEY,
            ),
            "relocation": declared_metadata.get(
                c.Infra.CODEMOD_RULE_RELOCATION_KEY,
            ),
            "context": [item.model_dump(mode="json") for item in context.value],
        })
        if payload.failure:
            return r[m.Infra.CodemodRule].from_failure(payload)
        return r[m.Infra.CodemodRule].ok(
            m.Infra.CodemodRule.model_validate_json(payload.value),
        )

    @staticmethod
    @lru_cache(maxsize=None)
    def _yaml_documents_json(text: str) -> p.Result[str]:
        """Memoize immutable canonical documents from the shared YAML ingress.

        Returns:
            Serialized validated documents or the original parsing failure.

        """
        parsed = u.Cli.yaml_parse_documents(text)
        if parsed.failure:
            return r[str].from_failure(parsed)
        return u.Cli.json_dumps(parsed.value)

    @classmethod
    def parse_yaml_documents(
        cls,
        text: str,
    ) -> p.Result[t.SequenceOf[t.JsonMapping]]:
        """Parse mapping documents without changing YAML scalar boundaries.

        Returns:
            The resulting ``p.Result[t.SequenceOf[t.JsonMapping]]``.

        """
        parsed = cls._yaml_documents_json(text)
        if parsed.failure:
            return r[t.SequenceOf[t.JsonMapping]].from_failure(parsed)
        return r[t.SequenceOf[t.JsonMapping]].ok(
            u.type_adapter(tuple[t.JsonMapping, ...]).validate_json(parsed.value)
        )

    @classmethod
    def _parse_rules(
        cls,
        provider: str,
        sources: t.VariadicTuple[t.Pair[Path, str]],
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        """Validate one provider's rule documents from their exact text.

        Returns:
            The provider's validated rules, in resource and document order.

        """
        rules: list[m.Infra.CodemodRule] = []
        for resource, text in sources:
            documents = cls.parse_yaml_documents(text)
            if documents.failure:
                return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(documents)
            for payload in documents.value:
                validated = cls._validated_document_rule(provider, resource, payload)
                if validated.failure:
                    return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(validated)
                rules.append(validated.value)
        return r[t.SequenceOf[m.Infra.CodemodRule]].ok(tuple(rules))

    @classmethod
    def _declared_context(
        cls,
        raw: t.JsonValue | None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodemodContextCondition]]:
        """Read ``metadata.context``: ``{VAR: {is|not: predicate[, of: VAR]}}``.

        Each entry binds one captured metavariable (single or transformed) to
        one project predicate, or to a sequence of them, that must hold
        (``is``) or fail (``not``), optionally evaluated against the module
        another capture names (``of``). Absence is the empty tuple; any other
        shape is a malformed rule document.

        Returns:
            The resulting
                ``p.Result[t.VariadicTuple[m.Infra.CodemodContextCondition]]``.

        """
        conditions = r[t.VariadicTuple[m.Infra.CodemodContextCondition]]
        if raw is None:
            return conditions.ok(())
        if not isinstance(raw, Mapping) or not raw:
            return conditions.fail(
                "ast-grep rule metadata.context must be a non-empty mapping",
            )
        verdicts = {
            c.Infra.CODEMOD_CONTEXT_HOLDS_KEY,
            c.Infra.CODEMOD_CONTEXT_FAILS_KEY,
        }
        parsed: list[m.Infra.CodemodContextCondition] = []
        for variable, declared in raw.items():
            entries = (
                declared
                if isinstance(declared, Sequence) and not isinstance(declared, str)
                else (declared,)
            )
            for condition in entries:
                if not isinstance(condition, Mapping):
                    return conditions.fail(
                        f"ast-grep rule context ${variable} must be a mapping "
                        "or a sequence of mappings",
                    )
                verdict = cls._context_verdict(variable, condition, verdicts)
                if verdict.failure:
                    return conditions.from_failure(verdict)
                payload = u.Cli.json_dumps({
                    "variable": variable,
                    "predicate": condition[verdict.value],
                    "holds": verdict.value == c.Infra.CODEMOD_CONTEXT_HOLDS_KEY,
                    "of": condition.get(c.Infra.CODEMOD_CONTEXT_OF_KEY),
                    "arg": list[t.JsonValue](
                        str(
                            condition.get(c.Infra.CODEMOD_CONTEXT_ARG_KEY, ""),
                        ).split(),
                    ),
                    "as_": list[t.JsonValue](
                        str(
                            condition.get(c.Infra.CODEMOD_CONTEXT_AS_KEY, ""),
                        ).split(),
                    ),
                })
                if payload.failure:
                    return conditions.from_failure(payload)
                parsed.append(
                    m.Infra.CodemodContextCondition.model_validate_json(payload.value),
                )
        return conditions.ok(tuple(parsed))

    @staticmethod
    def _context_verdict(
        variable: str,
        condition: t.JsonMapping,
        verdicts: t.StrSequence | set[str],
    ) -> p.Result[str]:
        """Return the one verdict key (``is``/``not``) of a context condition.

        Returns:
            The one verdict key (``is``/``not``) of a context condition.

        """
        keys = set(condition)
        verdict = keys.intersection(verdicts)
        operands = {
            c.Infra.CODEMOD_CONTEXT_OF_KEY,
            c.Infra.CODEMOD_CONTEXT_ARG_KEY,
            c.Infra.CODEMOD_CONTEXT_AS_KEY,
        }
        if len(verdict) != 1 or keys - set(verdicts) - operands:
            return r[str].fail(
                f"ast-grep rule context ${variable} must hold exactly one of "
                f"{sorted(verdicts)} and at most {sorted(operands)}",
            )
        return r[str].ok(verdict.pop())

    @staticmethod
    def _declared_expected(
        document: t.MappingKV[str, t.JsonValue],
    ) -> p.Result[t.VariadicTuple[int]]:
        """Read one rule's declared finding-count receipt from its metadata.

        The receipt is the same contract the sed-by-list phase already owns
        (``ModTextRule.expected``): a rule that declares how many findings it
        must produce turns a silent drift — a guard that stopped matching, a
        pattern that started over-matching — into a loud failure. ast-grep
        rejects unknown top-level keys, so the declaration lives under the
        ``metadata`` mapping it does accept. Absence is the empty tuple: a
        declared `expected: 0` is a real receipt ("this rule must never match
        again") and must not collapse into "no receipt declared".

        Returns:
            The resulting ``p.Result[t.VariadicTuple[int]]``.

        """
        metadata = document.get(c.Infra.CODEMOD_RULE_METADATA_KEY)
        if metadata is None:
            return r[t.VariadicTuple[int]].ok(())
        if not isinstance(metadata, Mapping):
            return r[t.VariadicTuple[int]].fail(
                "ast-grep rule metadata must be a mapping",
            )
        expected = metadata.get(c.Infra.CODEMOD_TEXT_KEY_EXPECTED)
        if expected is None:
            return r[t.VariadicTuple[int]].ok(())
        if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
            return r[t.VariadicTuple[int]].fail(
                "ast-grep rule expected receipt must be a non-negative integer",
            )
        return r[t.VariadicTuple[int]].ok((expected,))


__all__: list[str] = ["FlextInfraUtilitiesCodemodRules"]
