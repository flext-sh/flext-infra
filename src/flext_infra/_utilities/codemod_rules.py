"""Compose inherited ast-grep rules from FLEXT distribution metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from importlib.metadata import Distribution, distributions, packages_distributions
from importlib.util import find_spec
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t, u
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies


class FlextInfraUtilitiesCodemodRules:
    """Resolve universal, runtime-transitive, and local ast-grep rule layers."""

    @classmethod
    def codemod_rule_plan(cls, root: Path) -> p.Result[m.Infra.CodemodRulePlan]:
        """Build the sole executable rule plan for check and mutation."""
        project = cls._project(root)
        if project.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(project)
        root_name, direct_runtime = project.value
        indexed = cls._distributions()
        package_index = packages_distributions()
        runtime_closure = cls._runtime_closure(direct_runtime, indexed)
        universal = cls._providers(
            indexed,
            package_index,
            scope=c.Infra.CODEMOD_SCOPE_UNIVERSAL,
            selected=frozenset(indexed).difference({root_name}),
        )
        runtime = cls._providers(
            indexed,
            package_index,
            scope=c.Infra.CODEMOD_SCOPE_RUNTIME,
            selected=runtime_closure.difference({root_name}),
        )
        universal_order = cls._provider_order(universal, indexed)
        if universal_order.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(universal_order)
        runtime_order = cls._provider_order(runtime, indexed)
        if runtime_order.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(runtime_order)
        providers: list[tuple[str, Path]] = []
        for name in (*universal_order.value, *runtime_order.value):
            config = universal.get(name) or runtime.get(name)
            if config is None:
                return r[m.Infra.CodemodRulePlan].fail(
                    f"codemod provider disappeared from resolved graph: {name}"
                )
            providers.append((name, config))
        local_packages = cls._local_package_configs(root, root_name)
        if local_packages.failure:
            return r[m.Infra.CodemodRulePlan].from_failure(local_packages)
        providers.extend(local_packages.value)
        local_config = root / "sgconfig.yml"
        if local_config.is_file():
            providers.append((f"{root_name}:local", local_config))
        return cls._compose(tuple(providers))

    @staticmethod
    def codemod_rule_filter(rule_ids: t.StrSequence) -> str:
        """Return one exact ast-grep rule-ID filter for an elected ruleset."""
        if not rule_ids:
            msg = "codemod rule filter requires at least one rule ID"
            raise ValueError(msg)
        return "^(?:" + "|".join(re.escape(rule_id) for rule_id in rule_ids) + ")$"

    @staticmethod
    def _project(root: Path) -> p.Result[t.Pair[str, t.StrSequence]]:
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        document = u.Cli.toml_read_document(pyproject)
        if document.failure:
            return r[t.Pair[str, t.StrSequence]].from_failure(document)
        payload = u.Cli.toml_as_mapping(document.value)
        project = payload.get(c.Infra.PROJECT) if payload else None
        if not isinstance(project, Mapping):
            return r[t.Pair[str, t.StrSequence]].fail(
                f"missing [project] table: {pyproject}"
            )
        raw_name = project.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            return r[t.Pair[str, t.StrSequence]].fail(
                f"missing project.name: {pyproject}"
            )
        raw_dependencies = project.get(c.Infra.DEPENDENCIES)
        if not isinstance(raw_dependencies, Sequence) or isinstance(
            raw_dependencies, str
        ):
            return r[t.Pair[str, t.StrSequence]].fail(
                f"project.dependencies must be a sequence: {pyproject}"
            )
        dependencies: set[str] = set()
        for raw in raw_dependencies:
            if not isinstance(raw, str):
                return r[t.Pair[str, t.StrSequence]].fail(
                    f"project dependency must be a string: {pyproject}"
                )
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate():
                dependencies.add(canonicalize_name(requirement.name))
        return r[t.Pair[str, t.StrSequence]].ok((
            canonicalize_name(raw_name),
            tuple(sorted(dependencies)),
        ))

    @staticmethod
    def _distributions() -> dict[str, Distribution]:
        indexed: dict[str, Distribution] = {}
        for installed in distributions():
            raw_name = installed.metadata.get("Name")
            if not isinstance(raw_name, str) or not raw_name.strip():
                continue
            name = canonicalize_name(raw_name)
            if name in indexed:
                msg = f"duplicate installed distribution metadata: {name}"
                raise ValueError(msg)
            indexed[name] = installed
        return indexed

    @classmethod
    def _runtime_closure(
        cls, direct: t.StrSequence, indexed: t.MappingKV[str, Distribution]
    ) -> frozenset[str]:
        pending = list(direct)
        resolved: set[str] = set()
        while pending:
            name = pending.pop()
            if name in resolved:
                continue
            installed = indexed.get(name)
            if installed is None:
                msg = f"required runtime distribution is not installed: {name}"
                raise ValueError(msg)
            resolved.add(name)
            pending.extend(cls._requirements(installed))
        return frozenset(resolved)

    @staticmethod
    def _requirements(installed: Distribution) -> t.StrSequence:
        requirements: set[str] = set()
        for raw in installed.requires or ():
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate():
                requirements.add(canonicalize_name(requirement.name))
        return tuple(sorted(requirements))

    @classmethod
    def _providers(
        cls,
        indexed: t.MappingKV[str, Distribution],
        package_index: Mapping[str, Sequence[str]],
        *,
        scope: str,
        selected: frozenset[str],
    ) -> dict[str, Path]:
        providers: dict[str, Path] = {}
        for name in sorted(selected):
            if name not in indexed:
                continue
            configs = cls._provider_configs(name, package_index)
            if configs.failure:
                raise ValueError(configs.error or f"resolve codemod provider: {name}")
            if not configs.value:
                continue
            config = configs.value[0]
            declared_scope = cls._config_scope(config)
            if declared_scope.failure:
                raise ValueError(
                    declared_scope.error or f"resolve codemod scope: {config}"
                )
            if declared_scope.value == scope:
                providers[name] = config
        return providers

    @classmethod
    def _provider_order(
        cls, providers: t.MappingKV[str, Path], indexed: t.MappingKV[str, Distribution]
    ) -> p.Result[t.StrSequence]:
        selected = frozenset(providers)
        edges = {
            name: tuple(
                dependency
                for dependency in cls._requirements(indexed[name])
                if dependency in selected
            )
            for name in selected
        }
        try:
            ordered = FlextInfraUtilitiesDependencies.dependency_order(
                tuple(selected), dependencies=lambda name: edges.get(name, ())
            )
        except ValueError as exc:
            return r[t.StrSequence].fail(f"codemod provider cycle: {exc}")
        return r[t.StrSequence].ok(ordered)

    @staticmethod
    def _provider_configs(
        distribution_name: str, package_index: Mapping[str, Sequence[str]]
    ) -> p.Result[t.SequenceOf[Path]]:
        configs: set[Path] = set()
        for package_name, raw_distributions in package_index.items():
            if distribution_name not in {
                canonicalize_name(name) for name in raw_distributions
            }:
                continue
            spec = find_spec(package_name)
            if spec is None:
                return r[t.SequenceOf[Path]].fail(
                    f"distribution package is not importable: {package_name}"
                )
            roots = tuple(Path(path) for path in spec.submodule_search_locations or ())
            if not roots and spec.origin is not None:
                roots = (Path(spec.origin).parent,)
            configs.update(
                root / c.Infra.CODEMOD_CONFIG_RELPATH
                for root in roots
                if (root / c.Infra.CODEMOD_CONFIG_RELPATH).is_file()
            )
        if len(configs) > 1:
            return r[t.SequenceOf[Path]].fail(
                f"distribution exports multiple codemod configs: {distribution_name}"
            )
        return r[t.SequenceOf[Path]].ok(tuple(sorted(configs)))

    @classmethod
    def _local_package_configs(
        cls, root: Path, root_name: str
    ) -> p.Result[t.SequenceOf[t.Pair[str, Path]]]:
        configs = tuple(sorted((root / "src").glob("*/codemod/sgconfig.yml")))
        for config in configs:
            scope = cls._config_scope(config)
            if scope.failure:
                return r[t.SequenceOf[t.Pair[str, Path]]].from_failure(scope)
        return r[t.SequenceOf[t.Pair[str, Path]]].ok(
            tuple(
                (f"{root_name}:{config.parents[1].name}", config) for config in configs
            )
        )

    @staticmethod
    def _config_scope(config: Path) -> p.Result[str]:
        parsed = u.Cli.yaml_parse(config.read_text(encoding=c.Cli.ENCODING_DEFAULT))
        if parsed.failure:
            return r[str].from_failure(parsed)
        scope = parsed.value.get(c.Infra.CODEMOD_SCOPE_KEY)
        if not isinstance(scope, str) or scope not in {
            c.Infra.CODEMOD_SCOPE_UNIVERSAL,
            c.Infra.CODEMOD_SCOPE_RUNTIME,
        }:
            return r[str].fail(f"codemod config has invalid scope: {config}")
        return r[str].ok(scope)

    @classmethod
    def _compose(
        cls, providers: t.SequenceOf[t.Pair[str, Path]]
    ) -> p.Result[m.Infra.CodemodRulePlan]:
        selected: dict[str, m.Infra.CodemodRule] = {}
        rulesets: list[m.Infra.CodemodRuleset] = []
        provider_order: list[str] = []
        for provider, config in providers:
            if provider in provider_order:
                return r[m.Infra.CodemodRulePlan].fail(
                    f"codemod provider declared more than once: {provider}"
                )
            provider_order.append(provider)
            parsed = cls._rules(provider, config)
            if parsed.failure:
                return r[m.Infra.CodemodRulePlan].from_failure(parsed)
            elected: list[str] = []
            fixable: list[str] = []
            for rule in parsed.value:
                previous = selected.get(rule.id)
                if previous is not None:
                    if previous.provider == provider:
                        return r[m.Infra.CodemodRulePlan].fail(
                            f"duplicate codemod rule id in {provider}: {rule.id}"
                        )
                    if previous.digest != rule.digest:
                        return r[m.Infra.CodemodRulePlan].fail(
                            "conflicting codemod rule id "
                            f"{rule.id}: {previous.provider}:{previous.resource} "
                            f"({previous.digest}) != {rule.provider}:{rule.resource} "
                            f"({rule.digest})"
                        )
                    continue
                selected[rule.id] = rule
                elected.append(rule.id)
                if rule.fixable:
                    fixable.append(rule.id)
            if elected:
                rulesets.append(
                    m.Infra.CodemodRuleset(
                        provider=provider,
                        config=config,
                        rule_ids=tuple(elected),
                        fixable_rule_ids=tuple(fixable),
                    )
                )
        if not selected:
            return r[m.Infra.CodemodRulePlan].fail("no ast-grep rules discovered")
        return r[m.Infra.CodemodRulePlan].ok(
            m.Infra.CodemodRulePlan(
                provider_order=tuple(provider_order),
                rules=tuple(selected.values()),
                rulesets=tuple(rulesets),
            )
        )

    @classmethod
    def _rules(
        cls, provider: str, config: Path
    ) -> p.Result[t.SequenceOf[m.Infra.CodemodRule]]:
        parsed_config = u.Cli.yaml_parse(
            config.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        )
        if parsed_config.failure:
            return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(parsed_config)
        raw_dirs = parsed_config.value.get(c.Infra.CODEMOD_RULE_DIRS_KEY)
        if not isinstance(raw_dirs, Sequence) or isinstance(raw_dirs, str):
            return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                f"codemod config ruleDirs must be a sequence: {config}"
            )
        rules: list[m.Infra.CodemodRule] = []
        config_root = config.parent.resolve()
        for raw_dir in raw_dirs:
            if not isinstance(raw_dir, str) or not raw_dir.strip():
                return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                    f"codemod config has invalid ruleDirs entry: {config}"
                )
            rule_dir = (config_root / raw_dir).resolve()
            if not rule_dir.is_relative_to(config_root):
                return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                    f"codemod ruleDirs escapes provider root: {rule_dir}"
                )
            if not rule_dir.is_dir():
                return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                    f"codemod ruleDirs entry is missing: {rule_dir}"
                )
            for resource in sorted(rule_dir.rglob("*.yml")):
                relative = resource.relative_to(rule_dir)
                if any(part.startswith("_") for part in relative.parts):
                    continue
                documents = c.Infra.CODEMOD_DOCUMENT_SEPARATOR_RE.split(
                    resource.read_text(encoding=c.Cli.ENCODING_DEFAULT)
                )
                for raw_document in documents:
                    if not any(
                        line.strip() and not line.lstrip().startswith("#")
                        for line in raw_document.splitlines()
                    ):
                        continue
                    parsed_rule = u.Cli.yaml_parse(raw_document)
                    if parsed_rule.failure:
                        return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(
                            parsed_rule
                        )
                    rule_id = parsed_rule.value.get("id")
                    if not isinstance(rule_id, str) or not rule_id.strip():
                        return r[t.SequenceOf[m.Infra.CodemodRule]].fail(
                            f"ast-grep rule document missing id: {resource}"
                        )
                    canonical = u.Cli.json_dumps(
                        dict(parsed_rule.value), sort_keys=True
                    )
                    if canonical.failure:
                        return r[t.SequenceOf[m.Infra.CodemodRule]].from_failure(
                            canonical
                        )
                    rules.append(
                        m.Infra.CodemodRule(
                            id=rule_id,
                            digest=u.Cli.sha256_content(canonical.value),
                            provider=provider,
                            resource=resource,
                            fixable="fix" in parsed_rule.value,
                        )
                    )
        return r[t.SequenceOf[m.Infra.CodemodRule]].ok(tuple(rules))


__all__: list[str] = ["FlextInfraUtilitiesCodemodRules"]
