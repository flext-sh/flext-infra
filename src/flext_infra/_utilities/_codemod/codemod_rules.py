"""Compose inherited ast-grep rules from FLEXT distribution metadata.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, Sequence
from functools import cache
from pathlib import Path

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t
from flext_infra._utilities._codemod import (
    FlextInfraUtilitiesCodemodRulesDistributions,
    FlextInfraUtilitiesCodemodScopes,
)


class FlextInfraUtilitiesCodemodRules(
    FlextInfraUtilitiesCodemodRulesDistributions,
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
        return FlextInfraUtilitiesCodemodRules._provider_document(
            state.content.decode(c.DEFAULT_ENCODING)
        ).unwrap()

    @staticmethod
    @cache
    def _provider_document(text: str) -> p.Result[t.JsonMapping]:
        """Parse a single provider mapping once per exact current content.

        Returns:
            The native single-document parser's result, including its failure.

        """
        return u.Cli.yaml_parse(text)

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
    @cache
    def _utility_documents(text: str) -> t.SequenceOf[t.JsonMapping]:
        """Parse one utility file's documents once per exact content.

        Every provider and stage reads the same packaged utilities; their
        parse is a pure function of the bytes, so one parse serves the process.

        Returns:
            The file's validated documents in stream order.

        """
        return u.Cli.yaml_parse_documents(text).unwrap()

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
        for document in FlextInfraUtilitiesCodemodRules._utility_documents(
            observed.content.decode(c.DEFAULT_ENCODING)
        ):
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
    def codemod_provider_utility_rule(
        cls, config_path: Path, identity: str
    ) -> t.JsonMapping:
        """Return the native rule of one utility a provider declares.

        Returns:
            The utility document's ``rule`` mapping.

        Raises:
            ValueError: If the provider declares no single such utility.

        """
        rules = cls.codemod_provider_utility_rules(config_path)
        if identity not in rules:
            msg = f"provider {config_path} declares no single utility {identity}"
            raise ValueError(msg)
        return rules[identity]

    @classmethod
    def codemod_provider_utility_rules(
        cls, config_path: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Return the native rule of every utility a provider declares.

        Returns:
            Each utility's ``rule`` mapping keyed by its identity.

        Raises:
            ValueError: If two utilities share one identity.
            TypeError: If a utility document carries no rule mapping.

        """
        rules: dict[str, t.JsonMapping] = {}
        for (_language, declared), document in cls._collect_utility_documents(
            cls._read_provider_declaration(config_path), config_path
        ).items():
            rule = document.get("rule")
            if not isinstance(rule, Mapping):
                msg = f"utility {declared} of {config_path} declares no rule mapping"
                raise TypeError(msg)
            if declared in rules:
                msg = f"provider {config_path} declares utility {declared} twice"
                raise ValueError(msg)
            rules[declared] = rule
        return rules

    @classmethod
    def _project_provider_utilities(
        cls,
        config_path: Path,
        native_config: t.JsonDict,
        aliases: t.MutableMappingKV[Path, t.MutableStrMapping],
        utilities: t.MutableMappingKV[str, t.JsonMapping],
        *,
        stable: bool,
    ) -> None:
        """Project one provider's utilities under their stage identities.

        A catalog provider's utilities are qualified by the provider's content
        so two catalogs never collide. The project's generated provider keeps
        its stable ids: they are the project facts every catalog rule of the
        same stage references through ``matches``.

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
            identity: (
                identity
                if stable
                else u.Cli.sha256_content(namespace + "\0" + identity)
            )
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
        aliases: t.MappingKV[Path, t.MutableStrMapping],
        context: t.Pair[
            t.MappingKV[str, t.StrSequence],
            t.Pair[t.MappingKV[str, t.JsonMapping], frozenset[str]],
        ],
    ) -> t.JsonMapping:
        """Project one elected rule document under its owning provider aliases.

        A document naming ``in``/``not-in`` file scopes under
        ``metadata.scope`` receives them as its native ``files``/``ignores``.
        Explicit labels remain unchanged. Native metavariable captures,
        including relational anchors, remain part of the complete output.
        Every binding-sensitive utility
        the document references is embedded as a local, the only scope in
        which ast-grep shares the rule's metavariables with it.

        Returns:
            The elected native document with its scoped bindings.

        Raises:
            ValueError: If the rule input is absent, its election is
                ambiguous, or it changed before projection.
            TypeError: If projected codemod rule is not a mapping.

        """
        path = rule.resource.resolve()
        if path not in documents:
            observed = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if observed.content is None:
                msg = f"codemod rule input is absent: {path}"
                raise ValueError(msg)
            documents[path] = u.Cli.yaml_parse_documents(
                observed.content.decode(c.DEFAULT_ENCODING)
            ).unwrap()
        elected = [
            document for document in documents[path] if document.get("id") == rule.id
        ]
        if len(elected) != 1:
            msg = f"elected codemod rule document is ambiguous: {path}:{rule.id}"
            raise ValueError(msg)
        document = elected[0]
        canonical = u.Cli.json_dumps(dict(document), sort_keys=True).unwrap()
        if u.Cli.sha256_content(canonical) != rule.digest:
            msg = f"elected codemod rule changed before projection: {path}:{rule.id}"
            raise ValueError(msg)
        owner = max(
            (config for config in aliases if path.is_relative_to(config.parent)),
            key=lambda config: len(config.parent.parts),
        )
        projected = cls._qualified_global_matches(document, aliases[owner])
        if not isinstance(projected, Mapping):
            msg = f"projected codemod rule is not a mapping: {path}:{rule.id}"
            raise TypeError(msg)
        scopes, (bodies, sensitive) = context
        projected = FlextInfraUtilitiesCodemodScopes.codemod_bound_document(
            projected, bodies, sensitive
        )
        return {
            c.Infra.CODEMOD_RULE_LABELS_KEY: {},
            **FlextInfraUtilitiesCodemodScopes.codemod_scoped_document(
                projected, scopes, rule.id
            ),
        }

    @staticmethod
    def codemod_native_documents_text(
        documents: t.SequenceOf[t.JsonMapping],
    ) -> str:
        """Serialize typed mappings as a native JSON-form YAML document stream.

        Returns:
            The exact native document stream.

        Raises:
            ValueError: If no native document was supplied.

        """
        if not documents:
            msg = "native rule document stream must not be empty"
            raise ValueError(msg)
        return (
            c.Infra.CODEMOD_NATIVE_DOCUMENT_SEPARATOR.join(
                u.Cli.json_dumps(dict(document)).unwrap() for document in documents
            )
            + "\n"
        )

    @staticmethod
    def codemod_write_native_documents(
        path: Path, documents: t.SequenceOf[t.JsonMapping]
    ) -> None:
        """Publish the exact native document stream through the atomic owner."""
        owner = FlextInfraUtilitiesCodemodRules
        u.Cli.atomic_write_text_file(
            path, owner.codemod_native_documents_text(documents)
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
        generated = [
            ruleset
            for ruleset in plan.rulesets
            if ruleset.provider == c.Infra.CODEMOD_GENERATED_PROVIDER
        ]
        if len(generated) > 1:
            msg = (
                "one native stage stages one project's generated provider: "
                f"{[str(ruleset.config) for ruleset in generated]}"
            )
            raise ValueError(msg)
        scopes = FlextInfraUtilitiesCodemodScopes.codemod_stage_scopes(
            generated[0].config if generated else None
        )
        for ruleset in plan.rulesets:
            cls._project_provider_utilities(
                ruleset.config.resolve(),
                native_config,
                aliases,
                utilities,
                stable=ruleset.provider == c.Infra.CODEMOD_GENERATED_PROVIDER,
            )
        for digest, document in utilities.items():
            cls.codemod_write_native_documents(
                utility_directory / f"{digest}{c.Infra.CODEMOD_RULE_SUFFIX}",
                (document,),
            )
        for ruleset in plan.rulesets:
            cls.codemod_catalog_rules(
                ruleset.provider, ruleset.config, documents=documents
            ).unwrap()
        bodies: t.MappingKV[str, t.JsonMapping] = {
            str(document["id"]): rule_body
            for document in utilities.values()
            if not document.get("arguments")
            if isinstance(rule_body := document.get("rule"), Mapping)
        }
        sensitive = FlextInfraUtilitiesCodemodScopes.codemod_binding_sensitive(bodies)
        if plan.rules:
            cls.codemod_write_native_documents(
                rule_directory / c.Infra.CODEMOD_NATIVE_RULE_BUNDLE_FILENAME,
                tuple(
                    cls._project_rule_document(
                        rule, documents, aliases, (scopes, (bodies, sensitive))
                    )
                    for rule in plan.rules
                ),
            )
        native_config[c.Infra.CODEMOD_RULE_DIRS_KEY] = [rule_directory.name]
        native_config[c.Infra.CODEMOD_UTIL_DIRS_KEY] = [utility_directory.name]
        config_path = destination / c.Infra.CODEMOD_CONFIG_FILENAME
        cls.codemod_write_native_documents(config_path, (native_config,))
        return m.Infra.CodemodRuleset(
            provider=",".join(plan.provider_order),
            config=config_path,
            rule_ids=tuple(rule.id for rule in plan.rules),
            fixable_rule_ids=tuple(rule.id for rule in plan.rules if rule.fixable),
        )

    @staticmethod
    def codemod_project_targets(
        plan: m.Infra.CodemodRulePlan, targets: t.StrSequence
    ) -> t.SequenceOf[t.Pair[Path, t.StrSequence]]:
        """Assign each scan target to its deepest governed project.

        Each project scans in its own native stage: its generated provider
        owns the stable utility ids its catalog rules reference. Targets are
        relative to the shallowest governed project of the plan.

        Returns:
            Every project with targets, deepest first, with its targets.

        """
        projects = sorted(
            plan.project_rule_ids, key=lambda path: len(path.parts), reverse=True
        )
        base = projects[-1]
        owned: dict[Path, list[str]] = {}
        for target in targets:
            owner = next(
                project
                for project in projects
                if project == base
                or Path(target).is_relative_to(project.relative_to(base))
            )
            owned.setdefault(owner, []).append(target)
        return tuple(
            (project, tuple(owned[project])) for project in projects if project in owned
        )

    @staticmethod
    def codemod_project_plan(
        plan: m.Infra.CodemodRulePlan,
        project: Path,
        rule_ids: frozenset[str] | None = None,
    ) -> m.Infra.CodemodRulePlan:
        """Restrict a composed plan to one governed project's native stage.

        A stage holds the project's elected rules (optionally narrowed to
        ``rule_ids``) and always its own generated provider, whose stable
        utilities the catalog rules reference through ``matches``; another
        project's generated provider never enters it.

        Returns:
            The one-project plan a single stage and scan consume.

        """
        root = project.resolve()
        elected = frozenset(plan.project_rule_ids[root]) & (
            frozenset(plan.project_rule_ids[root]) if rule_ids is None else rule_ids
        )
        rules = tuple(rule for rule in plan.rules if rule.id in elected)
        rulesets = tuple(
            ruleset.model_copy(
                update={
                    field: tuple(
                        item for item in getattr(ruleset, field) if item in elected
                    )
                    for field in ("rule_ids", "fixable_rule_ids")
                }
            )
            for ruleset in plan.rulesets
            if (
                ruleset.config.resolve().is_relative_to(
                    root
                    / c.Infra.MOD_NATIVE_STAGE_RELATIVE_PATH
                    / c.Infra.CODEMOD_GENERATED_PROVIDER
                )
                if ruleset.provider == c.Infra.CODEMOD_GENERATED_PROVIDER
                else bool(elected.intersection(ruleset.rule_ids))
            )
        )
        return m.Infra.CodemodRulePlan(
            provider_order=tuple(ruleset.provider for ruleset in rulesets),
            rules=rules,
            rulesets=rulesets,
            project_rule_ids={root: tuple(rule.id for rule in rules)},
        )

    @classmethod
    def _qualified_utility_call(
        cls,
        value: t.JsonValue | t.JsonMapping,
        aliases: t.StrMapping,
        shadows: frozenset[str],
    ) -> t.JsonValue:
        """Qualify native callees while retaining their argument bindings.

        Returns:
            The same native call with provider-global identities qualified.

        """
        if isinstance(value, str):
            return aliases.get(value, value) if value not in shadows else value
        if isinstance(value, Mapping):
            return {
                (aliases.get(callee, callee) if callee not in shadows else callee): (
                    cls._qualified_global_matches(arguments, aliases, shadows)
                )
                for callee, arguments in value.items()
            }
        return value

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
            arguments = value.get("arguments")
            shadows = (
                local_names
                | frozenset(
                    argument for argument in arguments if isinstance(argument, str)
                )
                if isinstance(arguments, list)
                else local_names
            )
            shadows = (
                shadows | frozenset(local) if isinstance(local, Mapping) else shadows
            )
            qualified_aliases = {
                alias for origin, alias in aliases.items() if origin != alias
            }
            if isinstance(local, Mapping) and qualified_aliases.intersection(local):
                msg = "qualified global utility conflicts with a native local utility"
                raise ValueError(msg)
            return {
                key: (
                    item
                    if key == c.Infra.CODEMOD_RULE_METADATA_KEY
                    else cls._qualified_utility_call(item, aliases, shadows)
                    if key == "matches"
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

    @staticmethod
    def _select_rule_ids(
        plan: m.Infra.CodemodRulePlan,
        rule_ids: t.StrSequence,
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        if not rule_ids or any(not rule_id.strip() for rule_id in rule_ids):
            return r[m.Infra.CodemodRulePlan].fail(
                "codemod rule selection requires non-empty exact rule IDs",
            )
        selected = frozenset(rule_ids)
        if len(selected) != len(rule_ids):
            return r[m.Infra.CodemodRulePlan].fail(
                "duplicate codemod rule IDs in selection",
            )
        unknown = selected.difference(rule.id for rule in plan.rules).difference(
            rule.partition_of for rule in plan.rules
        )
        if unknown:
            return r[m.Infra.CodemodRulePlan].fail(
                "unknown codemod rule IDs: " + ", ".join(sorted(unknown)),
            )
        selected = selected.union(
            rule.id for rule in plan.rules if rule.partition_of in selected
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
            or ruleset.provider == c.Infra.CODEMOD_GENERATED_PROVIDER
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
    def codemod_compose_rule_plan(
        cls,
        root: Path,
        generated: t.MappingKV[Path, t.Pair[str, Path] | None],
        *,
        rule_ids: t.StrSequence | None = None,
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        """Compose one repository's catalogs and generated provider.

        Every call reads the current rule files; parsing is reused only for
        byte-identical catalogs (``_cached_rules``), so an edited rule is never
        served stale, within one process or across processes. ``generated``
        contains only the selected repository and its materialized provider,
        elected after the catalogs. Workspace orchestration visits each
        repository separately as required by ADR-028 Decision 17.

        Returns:
            The resulting ``p.Result[m.Infra.CodemodRulePlan]``.

        """
        resolved_root = root.resolve()
        if set(generated) != {resolved_root}:
            return r[m.Infra.CodemodRulePlan].fail(
                "rule plan requires exactly the selected repository root"
            )
        composed = cls._project_rule_plan(resolved_root, generated[resolved_root])
        if composed.failure or rule_ids is None:
            return composed
        return cls._select_rule_ids(composed.value, rule_ids)

    @classmethod
    def _project_rule_plan(
        cls, root: Path, generated: t.Pair[str, Path] | None
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        """Elect providers against one project's declared runtime dependencies.

        The generated provider is elected last, including utility-only
        providers: its declarations derive from the project's sources of truth.

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
        if generated is not None:
            providers.append(generated)
        return cls._compose(tuple(providers), root_name, runtime_closure, root)

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
        below it never do. A partitioned rule is never elected as authored:
        each project's generated provider renders its per-group documents.

        Returns:
            The resulting ``bool``.

        """
        if rule.partitioned:
            return True
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
        if not elected and provider != c.Infra.CODEMOD_GENERATED_PROVIDER:
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
        *,
        documents: t.MutableMappingKV[Path, t.SequenceOf[t.JsonMapping]] | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        """Read every validated catalog declaration before execution election.

        Returns:
            The resulting ``p.Result[t.SequenceOf[m.Infra.CodemodRule]]``.

        """
        parsed_config = FlextInfraUtilitiesCodemodRules._provider_document(
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
            sources.extend(cls._catalog_file_sources(rule_dir))
        # The memo key must not depend on the composed class that calls it.
        cached = FlextInfraUtilitiesCodemodRules._cached_rules(provider, tuple(sources))
        if documents is not None and cached.success:
            documents.update(cached.value[1])
        return (
            r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(cached)
            if cached.failure
            else r[t.SequenceOf[m.Infra.CodemodRule]].ok(cached.value[0])
        )

    @staticmethod
    def _catalog_file_sources(rule_dir: Path) -> list[t.Pair[Path, str]]:
        """Read the live catalog bytes that select the existing parsed-rule memo.

        Returns:
            Atomic source observations in deterministic resource order.

        Raises:
            ValueError: If a required rule input is absent.

        """
        sources: list[t.Pair[Path, str]] = []
        for resource in sorted(rule_dir.rglob("*.yml")):
            if any(
                part.startswith("_") for part in resource.relative_to(rule_dir).parts
            ):
                continue
            observed = u.Cli.atomic_read_binary_file_state(
                resource, required=True
            ).unwrap()
            if observed.content is None:
                msg = f"codemod rule input is absent: {resource}"
                raise ValueError(msg)
            sources.append((resource, observed.content.decode(c.DEFAULT_ENCODING)))
        return sources

    @classmethod
    @cache
    def _cached_rules(
        cls,
        provider: str,
        sources: t.VariadicTuple[t.Pair[Path, str]],
    ) -> p.Result[
        t.Pair[
            t.SequenceOf[m.Infra.CodemodRule],
            t.MappingKV[Path, t.SequenceOf[t.JsonMapping]],
        ]
    ]:
        """Reuse a provider's rules in memory by exact resource content.

        The same content-keyed entry retains the parsed documents by reference for
        native projection. Callers still read current bytes before selecting it.
        A new process builds its own catalog; no Infra cache is read or written.

        Returns:
            Validated rules and their original parsed document inventory.

        """
        result = r[
            t.Pair[
                t.SequenceOf[m.Infra.CodemodRule],
                t.MappingKV[Path, t.SequenceOf[t.JsonMapping]],
            ]
        ]
        documents: t.MutableMappingKV[Path, t.SequenceOf[t.JsonMapping]] = {}
        for resource, text in sources:
            loaded = u.Cli.yaml_parse_documents(text)
            if loaded.failure:
                return result.from_failure(loaded)
            documents[resource] = loaded.value
        parsed = cls._parse_rules(provider, sources, documents=documents)
        if parsed.failure:
            return result.from_failure(parsed)
        return result.ok((parsed.value, documents))

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
        )
        payload = u.Cli.json_dumps({
            "id": rule_id,
            "digest": u.Cli.sha256_content(canonical_json),
            "provider": provider,
            "resource": str(resource),
            "fixable": "fix" in parsed_rule,
            "owned_path_suffix": declared_metadata.get("owned_path_suffix"),
            "message": parsed_rule.get("message", ""),
            "module_absence": module_absence,
            "expected": declared_receipt[0] if declared_receipt else None,
            "owner": declared_metadata.get(
                c.Infra.CODEMOD_RULE_OWNER_KEY,
            ),
            "consumers_of": declared_metadata.get(
                c.Infra.CODEMOD_RULE_CONSUMERS_OF_KEY,
            ),
            "enforce": declared_metadata.get(c.Infra.CODEMOD_RULE_ENFORCE_KEY, []),
            "disabled": parsed_rule.get(c.Infra.CODEMOD_RULE_SEVERITY_KEY)
            == c.Infra.CODEMOD_RULE_SEVERITY_OFF,
            "partitioned": isinstance(
                scope := declared_metadata.get(c.Infra.CODEMOD_SCOPE_METADATA_KEY),
                Mapping,
            )
            and c.Infra.CODEMOD_SCOPE_PARTITION_KEY in scope,
            "partition_of": declared_metadata.get(c.Infra.CODEMOD_PARTITION_OF_KEY),
            "relocation": declared_metadata.get(
                c.Infra.CODEMOD_RULE_RELOCATION_KEY,
            ),
        })
        if payload.failure:
            return r[m.Infra.CodemodRule].from_failure(payload)
        return r[m.Infra.CodemodRule].ok(
            m.Infra.CodemodRule.model_validate_json(payload.value),
        )

    @classmethod
    def _parse_rules(
        cls,
        provider: str,
        sources: t.VariadicTuple[t.Pair[Path, str]],
        *,
        documents: t.MappingKV[Path, t.SequenceOf[t.JsonMapping]] | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        """Validate one provider's rule documents from their exact text.

        Returns:
            The provider's validated rules, in resource and document order.

        """
        rules: list[m.Infra.CodemodRule] = []
        for resource, text in sources:
            parsed_documents = (
                r[t.SequenceOf[t.JsonMapping]].ok(documents[resource])
                if documents is not None
                else u.Cli.yaml_parse_documents(text)
            )
            if parsed_documents.failure:
                return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(
                    parsed_documents
                )
            for payload in parsed_documents.value:
                validated = cls._validated_document_rule(provider, resource, payload)
                if validated.failure:
                    return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(validated)
                rules.append(validated.value)
        return r[t.SequenceOf[m.Infra.CodemodRule]].ok(tuple(rules))

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
