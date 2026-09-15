"""Release automation and override specification models."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import m, u

from ... import t
from ..._constants import FlextInfraConstantsRelease
from .. import FlextInfraModelsDepsToolSettings
from .artifact import FlextInfraConfigModelsArtifact
from .contexts import FlextInfraConfigModelsContexts
from .contract import FlextInfraConfigModelsContract
from .static import FlextInfraConfigModelsStatic


class FlextInfraConfigModelsRelease:
    """Release automation and override specification models."""

    class ReleaseAutomationOverrideSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One distribution's deviation from the shared release contract."""

        release_branch: Annotated[
            t.NonEmptyStr | None,
            m.Field(default=None, description="Branch that produces releases"),
        ] = None
        build_command: Annotated[
            t.NonEmptyStr | None,
            m.Field(default=None, description="Command that produces the artifacts"),
        ] = None
        version_variables: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Extra file:variable version anchors"),
        ] = ()

    class ReleaseAutomationSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Automated semantic versioning, owned by the market tool.

        Why: bump_version/parse_semver and the release orchestrator already
        existed, but nothing DERIVED the bump -- a human passed
        ``bump=minor`` by hand, which is exactly the judgement the commit
        history already encodes and the one a human gets wrong. Conventional
        Commits plus python-semantic-release replace that judgement with a
        rule, and replace local implementation with a maintained dependency.

        Declared once here so every generated pyproject carries the same
        contract. A project that genuinely differs is expressed in
        ``overrides``, never by editing its own pyproject.
        """

        tool: Annotated[
            t.NonEmptyStr, m.Field(description="Release automation distribution")
        ]
        runner: Annotated[
            t.NonEmptyStr, m.Field(description="Command runner that invokes the tool")
        ]
        commit_parser: Annotated[
            t.NonEmptyStr, m.Field(description="Commit convention driving the bump")
        ]
        release_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Branch that produces releases")
        ]
        version_variables: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="file:variable anchors the tool rewrites"),
        ]
        version_toml: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="file:tomlpath anchors the tool rewrites"),
        ]
        build_command: Annotated[
            t.NonEmptyStr, m.Field(description="Command that produces the artifacts")
        ]
        tag_format: Annotated[
            t.NonEmptyStr, m.Field(description="Tag shape, shared with the workflow")
        ]
        changelog_file: Annotated[
            t.NonEmptyStr, m.Field(description="Generated changelog destination")
        ]
        overrides: Annotated[
            Mapping[
                t.NonEmptyStr,
                FlextInfraConfigModelsRelease.ReleaseAutomationOverrideSpec,
            ],
            m.Field(
                default_factory=FlextInfraConfigModelsContract.immutable_empty_mapping,
                description="Per-distribution deviations from the shared contract",
            ),
        ]

        @u.model_validator(mode="after")
        def _validate_anchors(self) -> Self:
            """Every anchor must name a target, or the tool rewrites nothing."""
            for anchor in (*self.version_variables, *self.version_toml):
                if ":" not in anchor:
                    msg = f"release version anchor must be '<file>:<target>': {anchor}"
                    raise ValueError(msg)
            return self

    class ReleasePolicySpec(FlextInfraConfigModelsContract.ConfigContract):
        """The release protocol's declared data: who publishes, what bumps, where.

        Why (aihub-ioijy.9): `ReleaseOrchestrator._build_targets` hardcoded
        `project.name.startswith("flext-")`, so any consumer of this release
        engine whose distribution is not named `flext-*` resolved zero targets
        and died with "release build selected no publishable projects".
        Publishable membership is project policy, not a naming convention.

        `bump_types` maps a Conventional Commits type found in a merged
        pull-request title to the bump it earns; a type absent from the map
        releases nothing, and `!` in the title always earns a major bump. The
        Conventional Commits defaults are the typed default, so a consumer
        repository declares only what differs.
        """

        # The bump map is consumed as enum members by the strict release plan,
        # so the contract base's value coercion is switched off here.
        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            strict=False, frozen=True, extra="forbid", use_enum_values=False
        )

        publishable_prefixes: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description=(
                    "Distribution-name prefixes eligible for build/publish. "
                    "Empty means every resolved project is eligible."
                ),
            ),
        ]
        bump_types: Annotated[
            Mapping[t.NonEmptyStr, FlextInfraConstantsRelease.VersionBump],
            m.Field(
                default_factory=lambda: {
                    "feat": FlextInfraConstantsRelease.VersionBump.MINOR,
                    "fix": FlextInfraConstantsRelease.VersionBump.PATCH,
                    "perf": FlextInfraConstantsRelease.VersionBump.PATCH,
                },
                description="Conventional Commits type -> semantic version bump",
            ),
        ]
        publish_url: Annotated[
            t.NonEmptyStr,
            m.Field(
                default=FlextInfraConstantsRelease.PYPI_UPLOAD_URL,
                description="Package index upload endpoint for verified artifacts",
            ),
        ]
        build_constraints: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsRelease.BuildConstraintSpec],
            m.Field(
                min_length=1,
                description=(
                    "Hash-pinned build-backend requirements every release artifact "
                    "is built with; projected to config/build-constraints.txt"
                ),
            ),
        ]

    class BuildConstraintSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One hash-pinned build requirement (``uv build --require-hashes``)."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        version: Annotated[t.NonEmptyStr, m.Field(description="Exact version")]
        hashes: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(min_length=1, description="Accepted sha256 digests"),
        ]

    class Infra(FlextInfraConfigModelsContract.ConfigContract):
        """Complete flext-infra configuration namespace."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project distribution name")]
        initial_project_version: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Version seeded into a newly scaffolded project's pyproject; "
                    "from then on the release protocol is the only writer"
                )
            ),
        ]
        codegen: Annotated[
            FlextInfraConfigModelsArtifact.CodegenConfigSpec,
            m.Field(description="Unified project and workspace codegen contract"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolSettings.ToolConfigDocument,
            m.Field(description="Validated lint, typecheck, and scaffold policy"),
        ]
        source_scan: Annotated[
            FlextInfraConfigModelsStatic.SourceScanSpec,
            m.Field(description="Production-only source discovery contract"),
        ]
        release: Annotated[
            FlextInfraConfigModelsRelease.ReleasePolicySpec,
            m.Field(description="Release protocol policy: eligibility, bumps, index"),
        ]
        # Static policy is validated data, never detector code.
        enforcement: Annotated[
            FlextInfraConfigModelsStatic.StaticEnforcementSpec,
            m.Field(description="Rope-only static enforcement policy"),
        ]

    class Root(FlextInfraConfigModelsContract.ConfigContract):
        """Root payload deep-merged from flext-infra config files."""

        Infra: Annotated[
            FlextInfraConfigModelsRelease.Infra,
            m.Field(description="Validated flext-infra namespace"),
        ]

    class CodegenOverridesRoot(FlextInfraConfigModelsContract.ConfigContract):
        """Override root mirroring the Infra.codegen structure with override-only fields.

        Every field is optional and defaults to empty so an override file can
        declare only the deltas it needs. The conform system deep-merges this
        onto the immutable ``codegen.yaml`` before Pydantic validation.
        """

        codegen: Annotated[
            FlextInfraConfigModelsRelease._CodegenOverridesSection,
            m.Field(description="Override sections for the codegen namespace"),
        ]

    class _CodegenOverridesSection(FlextInfraConfigModelsContract.ConfigContract):
        """Override deltas that deep-merge onto CodegenConfigSpec fields."""

        checkout_submodules_overrides: Annotated[
            Mapping[str, str],
            m.Field(
                default_factory=FlextInfraConfigModelsContract.immutable_empty_mapping,
                description="Per-distribution checkout submodules overrides",
            ),
        ]
        ci_private_submodules: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(
                default_factory=FlextInfraConfigModelsContract.immutable_empty_mapping,
                description="Per-distribution private submodule deploy-key contracts",
            ),
        ]
        make: Annotated[
            FlextInfraConfigModelsRelease._MakeOverridesSection | None,
            m.Field(default=None, description="Make override deltas"),
        ] = None
        layout: Annotated[
            FlextInfraConfigModelsRelease._LayoutOverridesSection | None,
            m.Field(default=None, description="Layout override deltas"),
        ] = None

    class _MakeOverridesSection(FlextInfraConfigModelsContract.ConfigContract):
        """Override deltas for the generated Make contract."""

        custom_handler_profile_overrides: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(
                default_factory=FlextInfraConfigModelsContract.immutable_empty_mapping,
                description="Per-profile custom handler policy relaxations",
            ),
        ]

    class _LayoutOverridesSection(FlextInfraConfigModelsContract.ConfigContract):
        """Override deltas for the layout conformance contract."""

        project_overrides: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(
                default_factory=FlextInfraConfigModelsContract.immutable_empty_mapping,
                description="Per-project layout deltas",
            ),
        ]

    class CodegenOverridesSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed content of the config overrides layer (config/codegen-overrides.yaml).

        Layer 2 of the hierarchical architecture: project-specific parameters
        that sit on top of the immutable codegen.yaml business rules. Every field
        here is a delta applied to the base config; the overrides file never
        duplicates immutable rules.
        """

        Infra: Annotated[
            FlextInfraConfigModelsRelease.CodegenOverridesRoot,
            m.Field(description="flext-infra override namespace"),
        ]

    class UvEnvironmentPlan(FlextInfraConfigModelsContract.ConfigContract):
        """One deterministic uv environment operation plan."""

        project_root: Annotated[Path, m.Field(description="Selected project root")]
        environment_root: Annotated[
            Path, m.Field(description="Project supplying the active .venv")
        ]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Mise/Python version selector")
        ]
        groups: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Ordered dependency groups synchronized by setup"),
        ]
        editable_repositories: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsContexts.RepositoryRef],
            m.Field(description="Local repositories installed by setup"),
        ] = ()
