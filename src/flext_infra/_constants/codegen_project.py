"""Project-scaffold manifest (data) for ``flext-infra codegen new``.

Per ADR-005 this is the single source of truth describing *which* templates make
up a new project and *where* each lands. The engine (``u.Cli.template_render_dir``,
flext-cli) is policy-free; this manifest + the rope-derived context carry all the
FLEXT naming policy. Template-backed artifacts use ``.j2`` sources; typed
manifest artifacts serialize their Pydantic contract in the scaffold cycle.

Output paths use ``{token}`` placeholders (resolved by the service from rope) so
the engine never sees FLEXT naming. NOTE: the large-row form migrates to
``config/codegen/project_manifest.yaml`` in the ``conform`` slice (ADR-005 SSOT).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, Literal

from flext_core import c

from flext_infra._constants import FlextInfraConstantsSharedInfra
from flext_infra._constants.config import FlextInfraConstantsConfig

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegenProject(FlextInfraConstantsConfig):
    """Manifest + naming constants for project creation (flat in ``c.Infra.*``)."""

    CODEGEN_CLI_MODULE_FILENAME: ClassVar[str] = "cli.py"
    GITHUB_WORKFLOWS_RELATIVE_PATH: ClassVar[str] = ".github/workflows"
    CUSTOM_MAKE_FILENAME: ClassVar[str] = "custom.mk"
    """Operator-owned Make include rendered beside the generated Makefile."""
    CODEGEN_CONFIG_DIR: ClassVar[str] = "config"
    """Directory name for flext-infra config files relative to the package root."""
    CODEGEN_LOCAL_OVERRIDES_FILENAME: ClassVar[str] = "codegen-overrides.local.yaml"
    """Local operator override file name, excluded from the tracked baseline."""
    # These enums define the
    # one public conform contract shared by new and existing repositories. The
    # declarative values live in config/codegen.yaml; constants only type the
    # closed vocabulary used by models and CLI dispatch.

    @unique
    class CodegenConformScope(StrEnum):
        """Repository selection accepted by ``codegen conform`` and ``check run``.

        ``check run`` accepts ``self`` (the invoked repository) and ``all``
        (the repository plus its governed workspace members in one pass).
        """

        SELF = "self"
        DECLARED = "declared_repositories"
        ALL = "all"

    @unique
    class CodegenConformMode(StrEnum):
        """Read-only or write mode accepted by ``codegen conform``."""

        CHECK = "check"
        APPLY = "apply"

    @unique
    class CodegenStagedFilePhase(StrEnum):
        """Generation phase that owns one codegen staged publication.

        The closed vocabulary the journal models and the stager accept in
        ``phase``: every publication and staging site names its owner
        through this enum instead of a string literal, so the phase
        contract is code-owned in one declaration.
        """

        CANDIDATE_BOOTSTRAP = "candidate-bootstrap"
        CONFORM = "conform"
        CONFORM_BOOTSTRAP = "conform-bootstrap"
        DOCS = "docs"
        DOCS_COLLECTION = "docs-collection"
        LAZY_INIT = "lazy-init"
        LAYOUT = "layout"
        MISE = "mise"
        MOD_TEXT = "mod-text"
        RECOVERY = "recovery"
        SCAFFOLD = "scaffold"
        SEMANTIC = "semantic"
        TRANSACTION = "transaction"
        VERSION_FILE = "version-file"

    @unique
    class MiseResolutionMode(StrEnum):
        """How an apply-mode ``codegen conform`` resolves the Mise toolchain.

        ``AUTO`` probes the declared release endpoint once in preflight and
        becomes ``ONLINE`` (the newest Mise release and every moving tool
        selector are resolved and published) or ``OFFLINE`` (the published
        launchers and lock are kept byte-identical). The explicit values pin
        one path; none of them is a fallback taken after a failed effect.
        """

        AUTO = "auto"
        ONLINE = "online"
        OFFLINE = "offline"

    @unique
    class CheckoutKind(StrEnum):
        """Physical checkout topology for one repository."""

        ROOT = "root"
        SUBMODULE = "submodule"
        INDEPENDENT = "independent"

    BEADS_CONFIG_FILENAME: ClassVar[str] = "beads.yaml"
    BEADS_DIRNAME: ClassVar[str] = ".beads"
    BEADS_DIRECTORY_MODE: ClassVar[int] = 0o700
    BEADS_LOCAL_VERSION_FILENAME: ClassVar[str] = ".local_version"
    BEADS_LAST_TOUCHED_FILENAME: ClassVar[str] = "last-touched"
    BEADS_RUNTIME_ENTRY_NAMES: ClassVar[frozenset[str]] = frozenset({
        # Provenance: bd's own `.beads/.gitignore`. These are the live Dolt
        # server and daemon runtime entries bd writes beside the ledger: they
        # are projections of ledger truth, never composed output, so the
        # composed-project verify must tolerate them exactly as it tolerates
        # the passive `issues.jsonl`/`interactions.jsonl` exports.
        "dolt",
        "embeddeddolt",
        "proxieddb",
        "bd.sock",
        "bd.sock.startlock",
        "sync-state.json",
        "push-state.json",
        "daemon.lock",
        "daemon.log",
        "daemon.pid",
        "ephemeral.sqlite3",
        "ephemeral.sqlite3-journal",
        "ephemeral.sqlite3-shm",
        "ephemeral.sqlite3-wal",
        "dolt-server.activity",
        "dolt-server-config.yaml",
        "dolt-server.lock",
        "dolt-server.log",
        "dolt-server.pid",
        "dolt-server.port",
        "dolt-pprof",
        "proxied_server_client_info.json",
        ".env",
        ".exclusive-lock",
        ".sync.lock",
        # The bd client serializes every gate transaction through this marker
        # beside the ledger (measured: a members' gen failed composition on a
        # hours-stale zero-byte `dolt.gate.lock` whose holder had died). Same
        # class as `.exclusive-lock`/`.sync.lock`: a projection of ledger
        # operation, never composed output.
        "dolt.gate.lock",
    })
    "bd-owned Dolt/daemon runtime entries the composed-project verify tolerates."
    BEADS_CONFIG_VERSION: ClassVar[Literal[1]] = 1
    CONFORM_NAMESPACE_TABLE: ClassVar[t.VariadicTuple[str]] = (
        "tool",
        "flext",
        "namespace",
    )
    """Table the conform pipeline writes from the project SSOT.

    One owner for the path, consumed by the writer and by the managed-file
    declaration that must be able to recover it from a merge conflict. They
    drifted apart once, and the superproject merge then dead-ended on the
    owner's own output. The dotted spelling is derived through
    ``u.Cli.toml_dot_path``; it is never written a second time.
    """

    CONFIG_SNAPSHOT_ROOT_RACE_MARKER: ClassVar[str] = (
        "project root changed during config snapshot"
    )
    """Emitted by ``snapshot_config_sources`` when the project directory's
    physical state changes while its managed-artifact config is snapshotted."""
    CONFIG_SNAPSHOT_TOPOLOGY_RACE_MARKER: ClassVar[str] = (
        "project config source topology changed"
    )
    """Emitted by ``snapshot_config_sources`` when the ``config/*.yaml`` set
    changes while its managed-artifact config is snapshotted."""
    WORKSPACE_MANIFEST_FILENAME: ClassVar[str] = "workspace.yaml"
    UV_LOCK_FILENAME: ClassVar[str] = "uv.lock"
    MISE_LOCK_FILENAME: ClassVar[str] = "mise.lock"
    MISE_LOCK_JOURNAL_FILENAME: ClassVar[str] = "transaction.json"
    "Staged journal the mise.lock publisher commits before the lock rename."
    MISE_LOCK_NEW_FILENAME: ClassVar[str] = "new.lock"
    "Staged replacement lock published only after its sidecars match."
    MISE_LOCK_OLD_FILENAME: ClassVar[str] = "old.lock"
    "Previous lock retained until the staged replacement is published."
    MAKEFILE_BOOTSTRAP_DESTINATIONS: ClassVar[frozenset[str]] = frozenset({
        FlextInfraConstantsSharedInfra.MAKEFILE_FILENAME,
    })
    "The Makefile surface: the generated Makefile alone."
    MISE_LOCK_ANNOTATION: ClassVar[str] = "~"
    "Lockfile cache-key fragment (``<version>~<hash>``); never a selector."
    MISE_MOVING_SELECTOR: ClassVar[str] = "latest"
    "Selector resolved only by ``make upg`` into the committed ``mise.lock``."
    MISE_VERSION_PLACEHOLDER: ClassVar[str] = "{version}"
    "Placeholder a toolchain version_probe pattern carries for the lock version."
    MISE_IDENTITY_PROBE_ENVIRONMENT: ClassVar[t.StrMapping] = MappingProxyType({
        "MISE_DISABLE_UPDATE_WARNING": c.ParserBooleanToken.ONE,
    })
    """Environment of the mise version-identity probes, and of nothing else.

    ``mise --version`` prints a daily "newer mise available" notice on stderr;
    mise moves only through ``mise.lock`` under the supply-chain cooldown, so
    the notice is not actionable and the strict probes would fail on it.
    Documented mise setting since 2026.9.5 (tracker memory
    operator-ruling-2026-10-09-mise-update-notice-probes).
    """
    MISE_LOCK_PLATFORM_KEY: ClassVar[str] = "platforms.{platform}"
    "mise.lock per-platform table key of one locked tool version."
    MISE_PLATFORM_BY_HOST: ClassVar[t.MappingKV[t.StrPair, str]] = MappingProxyType({
        ("Linux", "x86_64"): "linux-x64",
        ("Linux", "aarch64"): "linux-arm64",
        ("Darwin", "x86_64"): "macos-x64",
        ("Darwin", "arm64"): "macos-arm64",
        ("Windows", "AMD64"): "windows-x64",
    })
    "Host (platform.system(), platform.machine()) -> mise.lock platform name."
    MISE_MUSL_PLATFORM_SUFFIX: ClassVar[str] = "-musl"
    "mise.lock platform suffix of a Linux host without glibc."
    GIT_URL_SUFFIX: ClassVar[str] = ".git"
    "Canonical clone-URL suffix every governed RepositoryRef URL carries."
    CUSTOM_CI_STEPS_FILENAME: ClassVar[str] = ".github/ci-custom-steps.yml"
    """Project-owned steps injected into generated CI, symmetric to custom.mk.

    It sits beside the workflows rather than inside them: GitHub parses every
    file under ``.github/workflows`` as a workflow, and a bare step list is not
    one, so a file placed there would surface as a permanent syntax error.
    These steps run before the approval verbs (runtimes the gates need).
    """
    CUSTOM_CI_POST_STEPS_FILENAME: ClassVar[str] = ".github/ci-custom-post-steps.yml"
    """Project-owned steps injected after the approval verbs.

    A ``failure()`` diagnostic only fires after the step it diagnoses, so it
    belongs here, never in the pre-approval file.
    """
    CUSTOM_HANDLER_PREFIX: ClassVar[str] = "_custom_"
    TEMPLATE_MODULE_SKELETON: ClassVar[str] = "module_skeleton.py.j2"
    "Scaffold module-skeleton template (replaces the legacy f-string)."
    TEMPLATE_TEST_MODULE_SKELETON: ClassVar[str] = "test_module_skeleton.py.j2"
    "Scaffold template for canonical test c/t/p/m/u facades."
    CODEGEN_CONFIG_FILENAME: ClassVar[str] = "codegen.yaml"
    INFRA_CONFIG_FILENAME: ClassVar[str] = "infra.yaml"
    CODEGEN_GEN_FILENAME: ClassVar[str] = "codegen.gen.yaml"
    CODEGEN_GEN_SUFFIX: ClassVar[str] = ".gen.yaml"
    "File suffix for generation requirements contract files managed by conform."

    # One base catalog serves both profiles;
    # workspace topology is read only from each repository's own .gitmodules.


__all__: list[str] = ["FlextInfraConstantsCodegenProject"]
