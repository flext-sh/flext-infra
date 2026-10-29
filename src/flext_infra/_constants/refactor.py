"""Constants namespace for flext_infra.refactor.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from enum import StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, Literal

from flext_core import c

from flext_infra._constants import (
    FlextInfraConstantsBase,
    FlextInfraConstantsCensus,
    FlextInfraConstantsSourceCode,
)

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsRefactor:
    """Shared constants for refactor modules."""

    @unique
    class NativeRuleSeverity(StrEnum):
        """Severity values in the native scanner diagnostic wire protocol."""

        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
        HINT = "hint"

    MOD_SCAN_REPORT_RELATIVE_PATH: ClassVar[Path] = (
        Path(FlextInfraConstantsSourceCode.REPORTS_DIR_NAME)
        / "refactor"
        / "mod-findings.json"
    )
    "Canonical single-file evidence snapshot for the latest mod scan."
    MOD_NATIVE_STAGE_RELATIVE_PATH: ClassVar[Path] = (
        Path(FlextInfraConstantsSourceCode.REPORTS_DIR_NAME) / "codemod" / "native"
    )
    "Per-stage staged sgconfig roots a native ``ast-grep scan -c`` reproduces."
    MOD_NATIVE_CASCADE_CHANGE: ClassVar[str] = "native-cascade"
    "Change label of a syntax plan the native ast-grep cascade produced."
    MOD_SCAN_REPORT_SCHEMA_VERSION: ClassVar[int] = 5
    "Exact structured mod evidence schema version."
    MOD_SCAN_SOURCE_DRIFT_ERROR_CODE: ClassVar[str] = "MOD_SCAN_SOURCE_DRIFT"
    "Typed failure code: one finding's source bytes changed during scanning."
    MOD_SCAN_REPORT_MODE: ClassVar[int] = 0o644
    "Canonical permission bits for structured mod evidence."
    ACCESSOR_MIGRATION_REPORT_RELATIVE_PATH: ClassVar[Path] = (
        Path(FlextInfraConstantsSourceCode.REPORTS_DIR_NAME)
        / "refactor"
        / "accessor-migration.json"
    )
    "Canonical single-file evidence snapshot for the latest accessor migration."
    NAMESPACE_ENFORCE_REPORT_RELATIVE_PATH: ClassVar[Path] = (
        Path(FlextInfraConstantsSourceCode.REPORTS_DIR_NAME)
        / "refactor"
        / "namespace-enforce.json"
    )
    "Canonical single-file evidence snapshot for the latest namespace enforcement."
    VIOLATIONS_SWEEP_ROUTE_NAME: ClassVar[str] = "violations-sweep"
    "Canonical refactor CLI verb that repairs and proves the always-reducing law."
    VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH: ClassVar[Path] = (
        Path(FlextInfraConstantsSourceCode.REPORTS_DIR_NAME)
        / "refactor"
        / "violations-sweep.json"
    )
    "Canonical single-file receipt for the latest violations sweep."
    VIOLATIONS_SWEEP_REPORT_SCHEMA_VERSION: ClassVar[Literal[1]] = 1
    "Exact structured violations-sweep report schema version."
    LINT_REPORT_COUNT_LINE: ClassVar[t.RegexPattern] = re.compile(
        r"^- lint: (?:PASS|FAIL) \((\d+) issues\)$",
        re.MULTILINE,
    )
    """The check report's generated lint line; its count is the repo's lint column."""
    AST_GREP_ERROR_FINDING_RECEIPT: ClassVar[str] = (
        "Error: {count} error(s) found in code."
    )
    "Exact first stderr line emitted for error-severity JSONL findings."
    AST_GREP_ERROR_FINDING_HELP: ClassVar[str] = (
        "Help: Scan succeeded and found error level diagnostics in the codebase."
    )
    "Exact second stderr line emitted for error-severity JSONL findings."
    IMPORT_NORMALIZATION_MAX_PASSES: ClassVar[int] = 24
    "Fixed-point pass ceiling for import normalization."
    IMPORT_LAW_OTHER_LAYER: ClassVar[str] = "other"
    "Import-layer slot of a module whose path names no declared layer."
    IMPORT_LAW_BASE_LAYER: ClassVar[str] = "base"
    "Import-layer slot every runtime alias that names no layer stands for."
    IMPORT_LAW_ROOT_SINGLETONS: ClassVar[frozenset[str]] = frozenset({
        "config",
        "settings",
    })
    "Root singletons and import layers of the config/settings law (ADR-005)."
    IMPORT_LAW_LAYER_ZERO_ROOTS: ClassVar[frozenset[str]] = (
        IMPORT_LAW_ROOT_SINGLETONS | frozenset({"lazy"})
    )
    """Module roots classified layer zero: the root singletons and the lazy loader.

    The lazy loader bootstraps every package, the facades included, so it
    cannot import them without a cycle; ADR-028 declares it the one documented
    layer-zero exception beside config/settings. It is not an importable root
    singleton, so alias routing keeps reading ``IMPORT_LAW_ROOT_SINGLETONS``.
    """
    IMPORT_LAW_PYTEST_PLUGIN_GROUP: ClassVar[str] = "pytest11"
    """Entry-point group whose registered modules are layer zero for pytest.

    pytest loads these plugin modules before any project facade exists, so
    they import pytest/hypothesis directly (ADR-028 Decision 10 ruling). The
    module set is read from the installed distributions, never listed.
    """
    IMPORT_LAW_GUARD_ERRORS: ClassVar[frozenset[str]] = frozenset({
        "ImportError",
        "ModuleNotFoundError",
    })
    "Exceptions whose handlers make a ``try`` around imports an import guard."
    IMPORT_LAW_FAMILY_BASE_FILE: ClassVar[str] = "base.py"
    "File name of a private family's leaf base module."

    @unique
    class ImportPlacement(StrEnum):
        """Where the import law places one imported binding."""

        RUNTIME = "runtime"
        "The module import block."
        TYPING = "typing"
        "The module ``if TYPE_CHECKING:`` block (typing-only reverse edge)."
        BOUND = "bound"
        "Nowhere new: an equal module-level import already binds it."
        STAY = "stay"
        "Its current place: a reverse runtime use or a foreign binding."

    @unique
    class ModScanCommand(StrEnum):
        """Public mod scan modes recorded in structured evidence."""

        SCAN = "scan"
        APPLY = "apply"

    @unique
    class ModStageKind(StrEnum):
        """Executor of one ordered stage of the native make mod cascade."""

        NATIVE = "native"
        "ast-grep applies the stage's rules with its own --update-all."
        RUFF = "ruff"
        "Ruff repairs the selected import codes on the changed sources."

    @unique
    class ModFindingOrigin(StrEnum):
        """Native producer provenance retained by scan findings."""

        AST_GREP = "ast-grep"
        OWNED_PATH = "owned-path"

    @unique
    class FamilyFlattenOperation(StrEnum):
        """Closed semantic operations admitted by installed family rules."""

        FLATTEN_SINGLE_WRAPPER = "flatten-single-wrapper"

    @unique
    class FamilyCollisionPolicy(StrEnum):
        """Closed member-name collision policies for family transformations."""

        PREFIX_WRAPPER = "prefix-wrapper"

    @unique
    class ModScanFindingClass(StrEnum):
        """Mutability class derived from one ast-grep rule contract."""

        ACTIONABLE = "actionable"
        DETECTION_ONLY = "detection_only"
        NON_ACTIONABLE_WITH_FIX = "non_actionable_with_fix"
        DEFERRED_SOURCE_DRIFT = "deferred_source_drift"

    MOD_SCAN_CLASS_COUNT_FIELDS: ClassVar[Mapping[ModScanFindingClass, str]] = (
        MappingProxyType({
            ModScanFindingClass.ACTIONABLE: "actionable",
            ModScanFindingClass.DETECTION_ONLY: "detection_only",
            ModScanFindingClass.NON_ACTIONABLE_WITH_FIX: "non_actionable_with_fix",
            ModScanFindingClass.DEFERRED_SOURCE_DRIFT: "deferred",
        })
    )
    """Sole authority mapping one finding class to its report count field.

    Every count writer and validator derives from this map; adding a class
    member extends this map once, never a second hand-written list.
    """

    @unique
    class CodemodRelocation(StrEnum):
        """Rope relocation a detection-only rule names in its metadata.

        The engine's own capability set: a rule declares which relocation
        repairs its findings, and the namespace phase runs that relocation
        over what the rule captured:

        - ``protocol`` / ``typing-alias``: move the declaration ``$NAME`` to
          its family owner;
        - ``future-annotations``: add the future import to the file;
        - ``module-import``: hoist the matched import statement to the
          module import block;
        - ``package-root-import``: rebind ``$NAME`` from ``$MODULE`` to that
          module's top-level package;
        - ``own-package-import``: rebind ``$NAME`` from ``$MODULE`` to the
          project's own package;
        - ``facade-class``: move class ``$NAME`` to the module of facade
          family ``$FAMILY``.
        """

        PROTOCOL = "protocol"
        TYPING_ALIAS = "typing-alias"
        FUTURE_ANNOTATIONS = "future-annotations"
        MODULE_IMPORT = "module-import"
        PACKAGE_ROOT_IMPORT = "package-root-import"
        OWN_PACKAGE_IMPORT = "own-package-import"
        FACADE_CLASS = "facade-class"

    PRIMITIVE_OWNER_OPERAND_COUNT: ClassVar[int] = 2
    "Exact operand count of a primitive owner: its module and public expression."

    @unique
    class FacadeMemberKind(StrEnum):
        """Kind of runtime object a facade member binds; config maps it to an owner."""

        EXCEPTION = "exception"
        ENUM = "enum"
        CONSTANT = "constant"
        PROTOCOL = "protocol"
        MODEL = "model"
        MODEL_DECLARATION = "model-declaration"
        TYPE = "type"
        FUNCTION = "function"

    FACADE_MEMBER_TYPING_MODULES: ClassVar[frozenset[str]] = frozenset({
        "typing",
        "types",
        "typing_extensions",
    })
    "Modules whose objects are typing forms (unions, literals, generic aliases)."

    @unique
    class FacadeMemberPlacement(StrEnum):
        """Whether a foreign facade member's owner already exposes it."""

        EXPOSED = "exposed"
        MISSING = "missing"

    FACADE_MEMBER_RELOCATE_SHAPE: ClassVar[str] = "relocate-facade-member"
    "Generated rule shape moving every foreign reference to its owner letter."
    FACADE_COMPONENT_RELOCATE_SHAPE: ClassVar[str] = "relocate-facade-component"
    "Generated rule shape moving a family-class namespace read to its letter."
    FACADE_LIBRARY_MEMBER_SHAPE: ClassVar[str] = "ban-library-named-facade-member"
    "Generated rule shape banning a library-named facade member outside families."
    FACADE_MEMBER_RETIRE_SHAPE: ClassVar[str] = "retire-foreign-facade-member"
    "Generated rule shape deleting the duplicate a non-owner letter declares."
    FACADE_MEMBER_WRONG_LAYER_SHAPE: ClassVar[str] = "facade-member-wrong-layer"
    "Generated rule shape guiding a declaration whose owner binds nothing yet."
    FACADE_MEMBER_REFERENCE_VAR: ClassVar[str] = "REF"
    "Metavariable binding a ``letter.member`` reference in relocation rules."
    FACADE_MEMBER_NAME_VAR: ClassVar[str] = "NAME"
    "Metavariable binding a declared member name in retirement rules."

    FAMILY_COMPOSE_MODULES: ClassVar[Sequence[str]] = (
        "constants",
        "models",
        "protocols",
        "typings",
        "utilities",
    )
    "Public family compose module leaves the family-shape amendment sanctions."

    CODEMOD_COMPOSE_MODULE_LEAVES: ClassVar[frozenset[str]] = frozenset({
        "constants",
        "models",
        "protocols",
        "typings",
        "utilities",
    })
    "Canonical public family compose leaf names (the static compose surface)."

    @unique
    class RopeContractOperation(StrEnum):
        """Closed operations admitted by the native contract catalog."""

        RESTRUCTURE = "restructure"
        MATERIALIZE_DELEGATIONS = "materialize-delegations"
        RETIRE_GENERIC_TYPING_WRAPPERS = "retire-generic-typing-wrappers"
        NORMALIZE_EXHAUSTIVE_ENUM = "normalize-exhaustive-enum"

    @unique
    class SemanticCutoverPhase(StrEnum):
        """Semantic ``make mod`` cutovers planned by ``u.Infra``."""

        DECLARATION_RELOCATION = "declaration-relocation"
        CLASS_NESTING = "class-nesting"
        CONSTANT_CONSUMERS = FlextInfraConstantsCensus.CensusRule.CONSTANT_CONSUMERS
        CONTRACT_NORMALIZATION = "contract-normalization"
        COMPAT_ALIAS = "compat-alias"
        PRIVATE_IMPORT = "private-import"
        FACADE_BASE = "facade-base"
        MODEL_FIELDS = "model-fields"
        DYNAMIC_ENVIRONMENT = "dynamic-environment"
        MODULE_END = "module-end"
        NOTICE_LAST = "notice-last"

    SEMANTIC_CUTOVER_RULE_IDS: ClassVar[Mapping[str, t.StrTuple]] = MappingProxyType({
        SemanticCutoverPhase.DECLARATION_RELOCATION: (
            "ban-nested-payload-outside-models",
        ),
        SemanticCutoverPhase.COMPAT_ALIAS: ("ban-compat-alias",),
        SemanticCutoverPhase.PRIVATE_IMPORT: ("ban-private-import",),
        SemanticCutoverPhase.FACADE_BASE: (
            "facade-base-by-class-name",
            "require-facade-mro-completeness",
        ),
        SemanticCutoverPhase.MODEL_FIELDS: (
            "rewire-getattr-model-fields-to-direct-access",
        ),
        SemanticCutoverPhase.DYNAMIC_ENVIRONMENT: ("ban-ambient-environ-read",),
        SemanticCutoverPhase.MODULE_END: ("require-all-last",),
        SemanticCutoverPhase.NOTICE_LAST: ("require-notice-last",),
    })
    "Distinct ast-grep laws whose findings share a semantic cutover stage."

    RK_FORBIDDEN_IMPORTS: ClassVar[str] = "forbidden_imports"
    RK_REDUNDANT_TYPE_TARGETS: ClassVar[str] = "redundant_type_targets"
    RK_TARGET_MODULES: ClassVar[str] = "target_modules"
    RK_MODULE_RENAMES: ClassVar[str] = "module_renames"
    RK_IMPORT_SYMBOL_RENAMES: ClassVar[str] = "import_symbol_renames"
    RK_SIGNATURE_MIGRATIONS: ClassVar[str] = "signature_migrations"
    RK_METHOD_ORDER: ClassVar[str] = "method_order"
    RK_ORDER: ClassVar[str] = "order"
    RK_ALLOW_ALIASES: ClassVar[str] = "allow_aliases"
    RK_ALLOW_TARGET_SUFFIXES: ClassVar[str] = "allow_target_suffixes"
    CODEMOD_RULE_SUFFIX: ClassVar[str] = ".yml"
    CODEMOD_NATIVE_RULE_BUNDLE_FILENAME: ClassVar[str] = "rules.yml"
    CODEMOD_NATIVE_DOCUMENT_SEPARATOR: ClassVar[str] = "\n---\n"
    # Native ast-grep language of every generated utility rule.
    CODEMOD_PYTHON_LANGUAGE: ClassVar[str] = "Python"
    # Rust-regex pattern that matches no text: a generated utility whose
    # source of truth is empty still exists, so a referencing rule loads.
    CODEMOD_NEVER_MATCH_REGEX: ClassVar[str] = r"\b\B"
    # Separator of a generated rule id: '<shape>--<qualifier>'.
    CODEMOD_GENERATED_ID_SEPARATOR: ClassVar[str] = "--"
    # Generated utility id prefix of a package's exports: 'exports--<package>'.
    CODEMOD_PACKAGE_EXPORTS_UTILITY: ClassVar[str] = "exports"
    # Generated utility id of the project's facade-family private packages.
    CODEMOD_FACADE_FAMILY_PACKAGE_UTILITY: ClassVar[str] = "facade-family-package"
    # Generated rule shape that rewires an inline type set to the constant
    # declaring it: 'type-set--<constant path>'.
    CODEMOD_TYPE_SET_SHAPE: ClassVar[str] = "type-set"
    # Generated rule shape that fails and rewires every read of a constant
    # whose annotation carries the stdlib compat marker: 'compat-read'.
    CODEMOD_COMPAT_READ_SHAPE: ClassVar[str] = "compat-read"
    # Message grammar of the compat marker (operator-ruling-2026-10-24-
    # deprecated-signature-window): "compat: <old> -> <new>; fix: <rewire>".
    CODEMOD_COMPAT_MESSAGE_PATTERN: ClassVar[str] = (
        r"^compat: (?P<old>[A-Za-z_][\w.]*) -> (?P<new>[A-Za-z_][\w.]*); fix: .+$"
    )
    # Generated shapes of the layer-zero import boundary: a settings/config
    # module imports neither its own root facade nor its own modules.
    CODEMOD_LAYER_ZERO_FACADE_IMPORT_SHAPE: ClassVar[str] = (
        "ban-settings-config-own-facade-import"
    )
    CODEMOD_LAYER_ZERO_MODULE_IMPORT_SHAPE: ClassVar[str] = (
        "ban-settings-config-own-module-import"
    )
    # Role the import-law classifier gives a layer-zero module.
    IMPORT_LAW_LAYER_ZERO_ROLE: ClassVar[str] = "layer0"
    # Universal catalog utility the layer-zero shape embeds locally: the
    # imported identity of an absolute root import.
    CODEMOD_ROOT_IMPORTED_NAME_UTILITY: ClassVar[str] = "root-imported-name"
    # Generated shape of the facade boundary: a library import outside the
    # c/t/p/m/u families (ADR-028, ENFORCE-070/093).
    CODEMOD_EXTERNAL_IMPORT_SHAPE: ClassVar[str] = (
        "ban-external-import-outside-facade-family"
    )
    # Universal catalog utilities the facade-boundary shape embeds locally.
    CODEMOD_LIBRARY_IMPORT_NAME_UTILITY: ClassVar[str] = "library-import-name"
    CODEMOD_TYPE_CHECKING_GUARD_UTILITY: ClassVar[str] = "inside-type-checking-guard"
    # Role the import-law classifier gives a facade-family module.
    IMPORT_LAW_FAMILY_ROLE: ClassVar[str] = "family"
    # Generated shape of the typings boundary: a library type named inline
    # outside the typings family (ADR-028).
    CODEMOD_LIBRARY_TYPE_SHAPE: ClassVar[str] = (
        "ban-library-type-reference-outside-typings"
    )
    # The typings family: its private package and its compose module.
    CODEMOD_TYPINGS_FAMILY_GLOBS: ClassVar[tuple[str, ...]] = (
        "**/_typings/**",
        "**/typings.py",
    )
    # The protocols family: it may name a library's protocol types (ADR-028),
    # never its other types.
    CODEMOD_PROTOCOLS_FAMILY_GLOBS: ClassVar[tuple[str, ...]] = (
        "**/_protocols/**",
        "**/protocols.py",
    )
    # Generated rule shape that inserts the canonical package import of names
    # a module uses bare without binding them: 'import-header--<package>'.
    CODEMOD_IMPORT_HEADER_SHAPE: ClassVar[str] = "import-header"
    # Generated rule shape that reaches a member through its package import
    # instead of a module object: 'module-member--<package>'.
    CODEMOD_MODULE_MEMBER_SHAPE: ClassVar[str] = "module-member"
    # Generated rule shape that rebinds a one-name import from a module to the
    # nearest package publishing the name: 'deep-import--<package>'.
    CODEMOD_DEEP_IMPORT_SHAPE: ClassVar[str] = "deep-import"
    # Provider of a project's rendered rules and utilities, materialized as a
    # native sgconfig root under MOD_NATIVE_STAGE_RELATIVE_PATH/<provider> and
    # elected into the rule plan after the catalogs.
    CODEMOD_GENERATED_PROVIDER: ClassVar[str] = "generated"
    # Generated rule shape that fails a real os.environ/os.getenv read outside
    # the project's layer-zero and isolated-execution files:
    # 'ban-ambient-environ-read--<package>'.
    CODEMOD_AMBIENT_ENVIRON_SHAPE: ClassVar[str] = "ban-ambient-environ-read"
    # Generated rule shape that drops a bare runtime facade alias used as a
    # class base outside the facade families and api.py:
    # 'ban-facade-alias-base--<package>'.
    CODEMOD_FACADE_ALIAS_BASE_SHAPE: ClassVar[str] = "ban-facade-alias-base"
    # Issue code of a module the project's runtime import graph places in a
    # cycle (ENFORCE-006); the graph, not a syntax rule, decides it.
    CODEMOD_IMPORT_CYCLE_CODE: ClassVar[str] = "ban-cyclic-import"
    # Generated rule shapes of the import-layer direction law, one document
    # per importing layer: '<shape>--<package>--<layer>'.
    CODEMOD_REVERSE_IMPORT_SHAPE: ClassVar[str] = "ban-reverse-runtime-import"
    CODEMOD_REVERSE_IMPORT_SETTINGS_SHAPE: ClassVar[str] = (
        "ban-reverse-runtime-import-settings"
    )
    CODEMOD_SETTINGS_PROTOCOLS_SHAPE: ClassVar[str] = (
        "ban-runtime-protocols-in-settings"
    )
    # Stable project-fact utilities catalog rules reference through matches.
    CODEMOD_OWN_PACKAGE_UTILITY: ClassVar[str] = "own-package"
    "Stable utility matching the project's own top-level import packages."
    CODEMOD_STDLIB_MODULE_UTILITY: ClassVar[str] = "stdlib-module"
    "Stable utility matching standard-library and declared backport modules."
    CODEMOD_GENERATED_MODULE_UTILITY: ClassVar[str] = "generated-module"
    "Stable utility matching a module that opens with the generator header."
    CODEMOD_RUNTIME_PACKAGE_UTILITY: ClassVar[str] = "runtime-package"
    "Stable utility matching an import package of the runtime closure."
    CODEMOD_FACADE_PACKAGE_UTILITY: ClassVar[str] = "facade-package"
    CODEMOD_LOCAL_ALIAS_UTILITY: ClassVar[str] = "local-alias"
    CODEMOD_RUNTIME_ALIAS_UTILITY: ClassVar[str] = "runtime-alias"
    CODEMOD_PACKAGE_EXPORT_UTILITY: ClassVar[str] = "package-export"
    CODEMOD_COMPOSE_MODULE_UTILITY: ClassVar[str] = "compose-module"
    # File scopes a catalog rule names under metadata.scope; the generated
    # provider publishes them in its scopes file.
    CODEMOD_SCOPE_METADATA_KEY: ClassVar[str] = "scope"
    CODEMOD_SCOPE_IN_KEY: ClassVar[str] = "in"
    CODEMOD_SCOPE_NOT_IN_KEY: ClassVar[str] = "not-in"
    CODEMOD_SCOPE_PARTITION_KEY: ClassVar[str] = "partition"
    CODEMOD_METAVARIABLE_PATTERN: ClassVar[str] = r"\$\$?\$?[A-Z_][A-Z0-9_]*"
    "An ast-grep metavariable; a utility naming one is binding-sensitive."
    CODEMOD_RULE_LABELS_KEY: ClassVar[str] = "labels"
    "Native label set; a staged rule that declares none reports no labels."
    CODEMOD_PARTITION_OF_KEY: ClassVar[str] = "partition_of"
    "Metadata key naming the catalog rule a generated partition renders."
    CODEMOD_PARTITION_KEY_IDENTITY_PATTERN: ClassVar[str] = r"[A-Za-z0-9_.,]{1,64}"
    CODEMOD_PARTITION_KEY_DIGEST_LENGTH: ClassVar[int] = 12
    CODEMOD_PARTITION_KEY_PLACEHOLDER: ClassVar[str] = "{key}"
    "Partition pattern placeholder for the escaped key."
    CODEMOD_PARTITION_RAW_PLACEHOLDER: ClassVar[str] = "{raw}"
    "Partition pattern placeholder for the key published as a regex."
    CODEMOD_PARTITION_ALTERNATIVES_PLACEHOLDER: ClassVar[str] = "{alternatives}"
    "Partition pattern placeholder for the escaped comma-separated key parts."
    CODEMOD_PARTITION_DEFAULT_PATTERN: ClassVar[str] = "^{key}$"
    "Partition pattern of a key that names its value exactly."
    CODEMOD_SCOPES_FILENAME: ClassVar[str] = "scopes.json"
    CODEMOD_SCOPE_FACTS: ClassVar[str] = "codemod_scope_facts"
    "Facts producer a generation seeds with its file scopes for the renderers."
    CODEMOD_LAYER_ZERO_SCOPE: ClassVar[str] = "layer-zero"
    CODEMOD_FACADE_MODULE_SCOPE: ClassVar[str] = "facade-module"
    CODEMOD_FAMILY_SCOPE_PREFIX: ClassVar[str] = "facade-family-"
    CODEMOD_PRIVATE_FAMILY_SCOPE_PREFIX: ClassVar[str] = "private-family-"
    CODEMOD_LACKS_LAYER_SCOPE_PREFIX: ClassVar[str] = "lacks-layer-"
    CODEMOD_FAMILY_WITHOUT_BASE_SCOPE: ClassVar[str] = "family-without-base"
    CODEMOD_FAMILY_BASE_SCOPE: ClassVar[str] = "family-base-file"
    CODEMOD_FAMILY_ROLE_SCOPE: ClassVar[str] = "family-role"
    CODEMOD_CLASS_STEM_SCOPE_PREFIX: ClassVar[str] = "class-stem-"
    CODEMOD_FAMILY_PEER_SCOPE_PREFIX: ClassVar[str] = "family-peer-"
    CODEMOD_MODEL_CLASS_SCOPE_PREFIX: ClassVar[str] = "model-class-"
    CODEMOD_IMPLEMENTATION_OWNER_SCOPE_PREFIX: ClassVar[str] = "implementation-owner-"
    CODEMOD_LIBRARY_MEMBER_OWNER_UTILITY_PREFIX: ClassVar[str] = "library-member-owner-"
    CODEMOD_GENERIC_SPECIALIZATION_UTILITY: ClassVar[str] = "generic-specialization"
    CODEMOD_PAYLOAD_CLASS_SCOPE_PREFIX: ClassVar[str] = "payload-class-"
    CODEMOD_INCOMPLETE_COMPOSITION_SCOPE_PREFIX: ClassVar[str] = (
        "incomplete-composition-"
    )
    # Catalog utility a generated import rule embeds to skip annotation-only
    # imports under `if TYPE_CHECKING:`.
    # An import statement binding exactly one plain name, so a rewrite of the
    # module path never drops another imported name.
    CODEMOD_SINGLE_NAME_IMPORT_REGEX: ClassVar[str] = (
        r"^from\s+[A-Za-z0-9_.]+\s+import\s+"
        r"(?:[A-Za-z_][A-Za-z0-9_]*|\(\s*[A-Za-z_][A-Za-z0-9_]*\s*,?\s*\))$"
    )
    # Universal catalog utility the generated shapes embed as their local
    # utility: an identifier that binds a name in its module.
    CODEMOD_NAME_BINDING_UTILITY: ClassVar[str] = "name-binding"
    CODEMOD_CONFIG_FILENAME: ClassVar[str] = "sgconfig.yml"
    # Static rules are data under the one rule root, config/rules: the
    # ast-grep corpus (sgconfig, rules, utils, tests with snapshots) and the
    # rope phase data. The same relative path names a governed checkout's
    # catalog and the copy a distribution ships as <pkg>/config.
    CODEMOD_RULES_RELPATH: ClassVar[Path] = Path("config") / "rules"
    CODEMOD_CONFIG_RELPATH: ClassVar[Path] = (
        CODEMOD_RULES_RELPATH / "ast-grep" / CODEMOD_CONFIG_FILENAME
    )
    CODEMOD_ROPE_RULES_RELPATH: ClassVar[Path] = CODEMOD_RULES_RELPATH / "rope"
    # Rope contract catalogue: the packaged universal rules, then the optional
    # same-path overlay a governed repository declares for its own symbols.
    CODEMOD_ROPE_CONTRACTS_RELPATH: ClassVar[Path] = (
        CODEMOD_ROPE_RULES_RELPATH / "contracts.yaml"
    )
    # Accessor renames and field normalizations the accessor migration proves.
    CODEMOD_ROPE_ACCESSOR_MIGRATIONS_RELPATH: ClassVar[Path] = (
        CODEMOD_ROPE_RULES_RELPATH / "accessor-migrations.yaml"
    )
    # Static enforcement catalog: one row per enforcement law and its owners.
    # Rope restructure argument that binds a capture to one qualified identity.
    ROPE_NAME_CONSTRAINT_PREFIX: ClassVar[str] = "name="
    # Rope restructure argument that types a capture by one builtin class:
    # Rope evaluates builtins through its ``__builtins__`` namespace.
    ROPE_BUILTIN_TYPE_CONSTRAINT_PREFIX: ClassVar[str] = "type=__builtins__."
    CODEMOD_RULE_DIRS_KEY: ClassVar[str] = "ruleDirs"
    CODEMOD_UTIL_DIRS_KEY: ClassVar[str] = "utilDirs"
    CODEMOD_FIXTURE_UTILS_DIRNAME: ClassVar[str] = "fixture-utils"
    "Catalog directory of fixture values for the stable generated utilities."
    CODEMOD_TEST_CONFIGS_KEY: ClassVar[str] = "testConfigs"
    CODEMOD_TEST_DIR_KEY: ClassVar[str] = "testDir"
    CODEMOD_SCOPE_KEY: ClassVar[str] = "scope"
    CODEMOD_SCOPE_UNIVERSAL: ClassVar[str] = "universal"
    CODEMOD_SCOPE_RUNTIME: ClassVar[str] = "runtime"
    # Declarative sed-by-list rules: one list entry drives one regex rewrite
    # across the governed scan surface with an exact expected-count receipt.
    # The sed-by-list catalogue has one declared owner per governed repository:
    # config/rules/mod/sed.yaml, whose schema the file itself documents. The
    # engine previously looked for a `text_rules.yml` that exists nowhere in
    # the tree, so the phase was wired but inert and the declared catalogue was
    # read by nothing.
    CODEMOD_TEXT_RULES_FILENAME: ClassVar[str] = "sed.yaml"
    # Declarative text-rule path derived from the filename SSOT.
    CODEMOD_TEXT_RULES_RELPATH: ClassVar[Path] = (
        CODEMOD_RULES_RELPATH / "mod" / CODEMOD_TEXT_RULES_FILENAME
    )
    CODEMOD_TEXT_RULES_KEY: ClassVar[str] = "rules"
    CODEMOD_TEXT_KEY_ID: ClassVar[str] = "id"
    CODEMOD_TEXT_KEY_DESCRIPTION: ClassVar[str] = "description"
    CODEMOD_TEXT_KEY_INCLUDE: ClassVar[str] = "include"
    CODEMOD_TEXT_KEY_EXCLUDE: ClassVar[str] = "exclude"
    CODEMOD_TEXT_KEY_DISTRIBUTIONS: ClassVar[str] = "distributions"
    CODEMOD_TEXT_KEY_FIND: ClassVar[str] = "find"
    CODEMOD_TEXT_KEY_REPLACE: ClassVar[str] = c.MergeStrategy.REPLACE
    CODEMOD_TEXT_KEY_FLAGS: ClassVar[str] = "flags"
    CODEMOD_TEXT_KEY_EXPECTED: ClassVar[str] = "expected"
    CODEMOD_TEXT_KEY_CAPTURE_EQUALS: ClassVar[str] = "capture_equals"
    # ast-grep rejects unknown top-level keys, so an ast-grep rule declares
    # its finding-count receipt under the `metadata` mapping it does accept.
    CODEMOD_RULE_METADATA_KEY: ClassVar[str] = "metadata"
    # A rule scoped to everything but its owning project names that project's
    # distribution under `metadata.owner`; the plan of the owner drops it.
    CODEMOD_RULE_OWNER_KEY: ClassVar[str] = "owner"
    # A rule that binds only the consumers of a facade distribution names it
    # under `metadata.consumers_of`; a plan whose runtime closure lacks that
    # distribution (the owner itself and its own dependencies) drops it.
    CODEMOD_RULE_CONSUMERS_OF_KEY: ClassVar[str] = "consumers_of"
    # A rule that enforces a catalog law names its stable law ids under
    # `metadata.enforce`; the enforcement catalog is derived from these claims.
    CODEMOD_RULE_ENFORCE_KEY: ClassVar[str] = "enforce"
    # ast-grep's own severity that switches a rule off; its claims are inactive.
    CODEMOD_RULE_SEVERITY_KEY: ClassVar[str] = "severity"
    CODEMOD_RULE_SEVERITY_OFF: ClassVar[str] = "off"
    # A detection-only rule names the rope relocation that repairs it under
    # `metadata.relocation` and captures the relocated symbol as `$NAME`.
    CODEMOD_RULE_RELOCATION_KEY: ClassVar[str] = "relocation"
    CODEMOD_RULE_NAME_METAVARIABLE: ClassVar[str] = "NAME"
    CODEMOD_RULE_MODULE_METAVARIABLE: ClassVar[str] = "MODULE"
    CODEMOD_RULE_FAMILY_METAVARIABLE: ClassVar[str] = "FAMILY"
    CODEMOD_TEXT_FLAG_NAMES: ClassVar[Mapping[str, int]] = MappingProxyType({
        "IGNORECASE": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "DOTALL": re.DOTALL,
    })
    CODEMOD_SNAPSHOT_DIRNAME: ClassVar[str] = "__snapshots__"
    CODEMOD_SNAPSHOT_SUFFIX: ClassVar[str] = "-snapshot.yml"
    # ast-grep rule-test protocol keys: a test names its rule and lists the
    # invalid cases; a snapshot file maps each invalid case to its projection.
    CODEMOD_RULE_TEST_ID_KEY: ClassVar[str] = "id"
    CODEMOD_RULE_TEST_INVALID_KEY: ClassVar[str] = "invalid"
    CODEMOD_SNAPSHOTS_KEY: ClassVar[str] = "snapshots"
    # `make mod` only verifies committed snapshots; the regeneration is its own
    # verb so every snapshot change lands as a reviewed commit.
    CODEMOD_SNAPSHOT_REFRESH_HINT: ClassVar[str] = (
        "ast-grep snapshots are projections of the rule tests: run "
        "`make mod-snapshots`, review the snapshot diff and commit it"
    )
    CODEMOD_EPHEMERAL_DIRNAME: ClassVar[str] = "__pycache__"
    TYPING_DEFINITION_FILES: ClassVar[frozenset[str]] = frozenset({
        "constants.py",
        "_constants",
        "typings.py",
        "_typings",
        "protocols.py",
        "_protocols",
    })
    """Declaration layers where a runtime ``t`` dependency would invert layering."""
    TYPING_INLINE_UNION_CANONICAL_MAP: ClassVar[Mapping[frozenset[str], str]] = (
        MappingProxyType({
            frozenset({"str", "int", "float", "bool"}): "t.Primitives",
            frozenset({"int", "float"}): "t.Numeric",
            frozenset({"str", "int", "float", "bool", "datetime"}): "t.Scalar",
        })
    )

    RULE_TABLE_HEADERS: ClassVar[Sequence[str]] = (
        FlextInfraConstantsBase.RK_ID,
        FlextInfraConstantsBase.NAME,
        FlextInfraConstantsBase.RK_DESCRIPTION,
        FlextInfraConstantsBase.RK_ENABLED,
        FlextInfraConstantsBase.RK_SEVERITY,
    )
    # NOTE: DOMAIN_PACKAGES/PLATFORM_PACKAGES were removed: member layers
    # derive from the declared per-member `flext-layer` attribute in
    # .gitmodules through u.Infra.workspace_member_layer_names (standalone
    # = no members, same topology contract as the modernizer). The
    # violation-classification token/priority lists had zero consumers and
    # were exterminated.
    INTEGRATION_CLASS_PREFIXES: ClassVar[tuple[str, ...]] = (
        "FlextTap",
        "FlextTarget",
        "FlextDbt",
    )
    "Class name prefixes that identify integration projects."
    MIN_PATH_DEPTH: int = 2
    "Minimum relative path depth for module prefix detection."

    TYPING_FACTORY_ASSIGN_RE: ClassVar[t.RegexPattern] = re.compile(
        r"^(\w+)\s*=\s*(?:(?:\w+\.)*)?"
        r"(?:TypeVar|ParamSpec|TypeVarTuple|NewType)\s*\(",
        re.MULTILINE,
    )
    "Matches TypeVar/ParamSpec/TypeVarTuple/NewType assignments."
    MIN_METHODS_FOR_REORDER: ClassVar[int] = 2
    "Minimum method count before class method reordering is attempted."

    # --- Method category StrEnum (was: plain class MethodCategory) ---
    @unique
    class MethodCategory(StrEnum):
        """Canonical method category identifiers for FLEXT reordering."""

        MAGIC = "magic"
        PROPERTY = "property"
        STATIC = "static"
        CLASS = "class"
        PUBLIC = "public"
        PROTECTED = "protected"
        PRIVATE = "private"

    NAMESPACE_PRIVATE_BASE_MODULE: ClassVar[str] = "_base.py"
    "Private base module name allowed to host private FLEXT base contracts."
    NAMESPACE_PYTEST_MODULE_PREFIX: ClassVar[str] = "test_"
    "Pytest module prefix exempt from production loose-object structure checks."
    NAMESPACE_PYTEST_MODULE_SUFFIXES: ClassVar[frozenset[str]] = frozenset({
        "_test.py",
        "_tests.py",
    })
    "Pytest module suffixes exempt from production loose-object structure checks."

    ACCESSOR_WARNING_PREFIXES: ClassVar[frozenset[str]] = frozenset({
        "get_",
        "set_",
        "is_",
    })
    "Public accessor prefixes to rename (drop the prefix or use a canonical name)."

    # --- Symbol/identifier patterns ---
    IDENTIFIER_PATTERN: ClassVar[t.RegexPattern] = re.compile(r"\b[A-Za-z_]\w*\b")
    "Regex: Python identifier word boundary match."


__all__: list[str] = ["FlextInfraConstantsRefactor"]
