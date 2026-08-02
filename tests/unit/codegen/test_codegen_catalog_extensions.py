"""Repository-local workspace manifests are the sole consumer authority."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u


def _repository(
    name: str,
    *,
    path: str,
    role: c.Infra.RepositoryRole,
    state: c.Infra.RepositoryState = c.Infra.RepositoryState.ACTIVE,
) -> m.Infra.RepositoryRef:
    provider = config.Infra.codegen.providers[0]
    return m.Infra.RepositoryRef(
        name=name,
        distribution=name,
        provider=provider.name,
        url=f"{provider.base_url}/{name}.git",
        path=Path(path),
        role=role,
        state=state,
        branch=provider.branch,
        checkout=(
            c.Infra.CheckoutKind.ROOT
            if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        editable=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        read_only=False,
    )


class TestsCodegenCatalogExtensions:
    def test_beads_toolchain_uses_an_immutable_release_selector(self) -> None:
        selector = config.Infra.codegen.toolchain.beads.version

        version_parts = selector.split(".")
        is_semver = len(version_parts) == 3 and all(
            part.isdecimal() for part in version_parts
        )
        is_commit = len(selector) == 40 and all(
            char in "0123456789abcdef" for char in selector
        )
        tm.that(is_semver or is_commit, eq=True)

    def test_bootstrap_toolchain_uses_immutable_release_selectors(self) -> None:
        toolchain = config.Infra.codegen.toolchain

        # uv is supplied by the caller environment and is deliberately not pinned;
        # only the mise binary and the Beads CLI installed through mise declare
        # immutable selectors: a semver release for mise, and either a semver
        # release or a full commit for the Beads go-module pin.
        mise_parts = toolchain.mise_version.split(".")
        tm.that(len(mise_parts), eq=3)
        tm.that(all(part.isdecimal() for part in mise_parts), eq=True)
        beads_version = toolchain.beads.version
        beads_parts = beads_version.split(".")
        beads_is_semver = len(beads_parts) == 3 and all(
            part.isdecimal() for part in beads_parts
        )
        beads_is_commit = len(beads_version) == 40 and all(
            char in "0123456789abcdef" for char in beads_version
        )
        tm.that(beads_is_semver or beads_is_commit, eq=True)

    def test_beads_gate_compares_the_binary_reported_version(self) -> None:
        """The conform preflight gate uses the binary's self-reported version.

        The pinned Beads build is a go-module commit (schema v61-capable) whose
        ``bd version`` output does NOT echo the pin. The toolchain therefore
        declares ``reported_version`` — what the binary actually prints — and
        the gate consumes that value directly so preflight compares like with
        like. (mro-e9j0.6 / shared mro ledger at Dolt schema v61)
        """
        beads = config.Infra.codegen.toolchain.beads
        tm.that(beads.selector, eq="go:github.com/steveyegge/beads/cmd/bd")
        is_commit = len(beads.version) == 40 and all(
            char in "0123456789abcdef" for char in beads.version
        )
        tm.that(is_commit, eq=True)
        # ONE declared field, no optional/computed pair: the model states what
        # the binary prints and the gate reads exactly that.
        tm.that(beads.reported_version, eq="1.1.0")
        tm.that(hasattr(beads, "gate_version"), eq=False)

    def test_mise_tool_spec_requires_the_reported_version(self) -> None:
        """``reported_version`` is a required field validated by Pydantic.

        It was previously declared ``str | None`` with a fallback inside the
        model. Every mise tool knows what its binary prints, so the value is
        declared, required, and validated at construction instead.
        """
        spec = m.Infra.MiseToolSpec(
            selector="go:example.com/tool/cmd/x",
            version="0123456789abcdef0123456789abcdef01234567",
            reported_version="1.2.3",
        )
        tm.that(spec.reported_version, eq="1.2.3")
        with pytest.raises(c.ValidationError):
            m.Infra.MiseToolSpec.model_validate({
                "selector": "go:example.com/tool/cmd/x",
                "version": "0123456789abcdef0123456789abcdef01234567",
            })
        with pytest.raises(c.ValidationError):
            m.Infra.MiseToolSpec(
                selector="go:example.com/tool/cmd/x",
                version="0123456789abcdef0123456789abcdef01234567",
                reported_version="",
            )

    def test_beads_plan_declares_the_ledger_root_it_owns(self, tmp_path: Path) -> None:
        """``BeadsPlan.ledger_root`` is always the tree that owns the ledger.

        It was ``Path | None``, where ``None`` encoded "same as
        repository_root" — so three separate call sites re-derived the real
        value with ``plan.ledger_root or plan.repository_root`` and a fourth
        compared against ``None`` to detect routing. The plan now declares the
        owning root outright: consumers read one validated field and routing is
        the honest comparison between two paths.
        """
        repo = tmp_path / "member"
        principal = tmp_path / "principal"
        own = m.Infra.BeadsPlan(
            repository_root=repo,
            enabled=True,
            canonical_prefix="mro",
            expected_version="1.1.0",
            ledger_root=repo,
            ledger_id="mro",
        )
        tm.that(own.ledger_root, eq=repo)
        tm.that(own.routes_to_principal_ledger, eq=False)
        routed = own.model_copy(update={"ledger_root": principal})
        tm.that(routed.routes_to_principal_ledger, eq=True)
        # The field is required: "no ledger root" is not a representable state.
        with pytest.raises(c.ValidationError):
            m.Infra.BeadsPlan.model_validate({
                "repository_root": repo,
                "enabled": True,
                "canonical_prefix": "mro",
                "expected_version": "1.1.0",
                "ledger_id": "mro",
            })

    def test_beads_tracker_declaration_is_a_validated_model(
        self, tmp_path: Path
    ) -> None:
        """The committed tracker config parses once into a typed model.

        mro-o0cc: a committed ``.beads/config.yaml`` (e.g. the shared ``mro``
        ledger) is the tracker declaration for that repository. Reading it
        returned a bare ``str`` chosen by runtime isinstance checks against an
        untyped mapping, with a ``fallback`` argument deciding the outcome.
        Parsing happens once, at the boundary, into ``BeadsTrackerDeclaration``;
        absence is the model's absence, never a substituted string.
        """
        root = tmp_path / "flext-demo"
        beads_dir = root / ".beads"
        beads_dir.mkdir(parents=True)
        (beads_dir / "config.yaml").write_text(
            'issue-prefix: "mro"\ndolt:\n  database: mro\n', encoding="utf-8"
        )
        declared: m.Infra.BeadsTrackerDeclaration = tm.ok(
            FlextInfraCodegenConform.beads_declaration(root)
        )
        tm.that(declared.issue_prefix, eq="mro")
        # A repository without a committed tracker declares nothing; the
        # caller — not the reader — decides what that means.
        bare = tmp_path / "bare-demo"
        bare.mkdir()
        tm.fail(FlextInfraCodegenConform.beads_declaration(bare))
        # An empty prefix is rejected by the model, not silently replaced.
        broken = tmp_path / "broken-demo"
        (broken / ".beads").mkdir(parents=True)
        (broken / ".beads" / "config.yaml").write_text(
            'issue-prefix: ""\n', encoding="utf-8"
        )
        tm.fail(FlextInfraCodegenConform.beads_declaration(broken))

    def test_setup_provisions_only_and_gen_owns_conformance(self) -> None:
        """``make setup`` provisions tooling; ``make gen`` owns conformance.

        Operator contract (mro-e9j0.6 C7 final): setup installs mise, the
        venv, and dependencies — it never generates, conforms, or mutates
        project code. gen/gen APPLY=Y is the single public conformance and
        generation surface, and no public ``conform`` verb exists.
        """
        codegen = config.Infra.codegen
        make = codegen.make
        operations = {operation.name: operation for operation in make.operations}
        generation_verbs = tuple(
            verb
            for verb in make.verbs
            if operations[verb.operation].executor == "generation"
        )
        setup = next(verb for verb in make.verbs if verb.name == "setup")
        content = Path(codegen.surfaces.make_engine_path).read_text(encoding="utf-8")
        verb_names = tuple(verb.name for verb in make.verbs)

        tm.that(generation_verbs, len=1)
        tm.that(operations[setup.operation].executor, ne="generation")
        tm.that(content, has=f"PUBLIC_VERBS := {' '.join(verb_names)}")
        tm.that(content, has="workspace serialize-make")
        tm.that(content, lacks=["codegen conform", "_builtin_", "_custom_"])
        tm.that("conform" in verb_names, eq=False)

    def test_transaction_worktrees_skip_the_beads_lifecycle(
        self, tmp_path: Path
    ) -> None:
        """Inside a worktree transaction the Beads lifecycle is fully skipped.

        A transaction checkout routes its ledger to the principal worktree, so
        the repository_root never owns the tracker lifecycle.  The principal
        ledger is verified separately at the real tree on apply.
        """
        principal = tmp_path / "principal"
        principal.mkdir()
        tx = tmp_path / "tx-checkout"
        (tx / ".beads").mkdir(parents=True)
        (tx / ".beads" / "config.yaml").write_text(
            'issue-prefix: "mro"\n', encoding="utf-8"
        )
        plan = m.Infra.BeadsPlan(
            repository_root=tx,
            ledger_root=principal,
            enabled=False,
            canonical_prefix="mro",
            expected_version="1.1.0",
        )
        verify = FlextInfraCodegenConform.verify_beads_plan
        tm.ok(verify(plan, allow_missing=False))
        # Outside a transaction the disabled-but-present guard still fails.
        plan_at_root = m.Infra.BeadsPlan(
            repository_root=tx,
            enabled=False,
            canonical_prefix="mro",
            expected_version="1.1.0",
            ledger_root=tx,
        )
        tm.fail(verify(plan_at_root, allow_missing=False))

    def test_github_actions_ci_skips_the_beads_lifecycle(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inside GitHub Actions CI the Beads lifecycle is fully skipped.

        CI runners are ephemeral and do not carry a live Dolt tracker; the
        committed ``.beads`` tree is present but the tracker database is not.
        Attempting to verify a missing tracker in CI used to fail with
        'Beads tracker inspection failed'. CI is not a tracker owner.
        """
        root = tmp_path / "ci-checkout"
        (root / ".beads").mkdir(parents=True)
        (root / ".beads" / "config.yaml").write_text(
            'issue-prefix: "mro"\n', encoding="utf-8"
        )
        plan = m.Infra.BeadsPlan(
            repository_root=root,
            enabled=False,
            canonical_prefix="mro",
            expected_version="1.1.0",
            ledger_root=root,
        )
        monkeypatch.setenv(c.Infra.ENV_VAR_GITHUB_ACTIONS, "true")
        verify = FlextInfraCodegenConform.verify_beads_plan
        tm.ok(verify(plan, allow_missing=False))

    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        script_operation = next(
            operation
            for operation in config.Infra.codegen.make.operations
            if operation.executor == "script"
        )
        handler = (
            m.Infra.MakeHandlerSpec(
                what="all", default=True, apply_policy="required", apply_default=True
            )
            if script_operation.mutation == "apply"
            else m.Infra.MakeHandlerSpec(what="all", default=True)
        )
        root = _repository(
            "acme-platform", path=".", role=c.Infra.RepositoryRole.WORKSPACE_ROOT
        ).model_copy(
            update={
                "extra_verbs": (
                    m.Infra.MakeVerbSpec(
                        name="audit",
                        operation=script_operation.name,
                        handlers=(handler,),
                    ),
                ),
                "script_dispatch": m.Infra.ScriptDispatchSpec(
                    dispatcher="scripts/dispatch.py"
                ),
            }
        )
        project = m.Infra.ProjectSpec(
            package_name="acme_platform",
            class_stem="AcmePlatform",
            namespace="AcmePlatform",
            constant_name="acme-platform",
            namespace_attribute="acme_platform",
            alias="acme",
            environment_prefix="ACME_PLATFORM_",
            description="Product-neutral platform fixture",
            version="0.1.0",
            license="MIT",
            author_name="Acme Team",
            author_email="engineering@example.com",
            upstream="flext_core",
            homepage="https://example.com/acme-platform",
            documentation="https://example.com/acme-platform/docs",
            workspace_root_rel=".",
            year=2026,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root.name,
            repository=root,
            project=project,
            members=(
                _repository(
                    "acme-charts",
                    path="acme-charts",
                    role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                ),
            ),
        )
        member_root = tmp_path / "acme-charts"
        member_root.mkdir()
        (member_root / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "acme-charts"\nversion = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
            encoding="utf-8",
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "init", "-q", "-b", "development"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "add", c.Infra.PYPROJECT_FILENAME], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Initial fixture"], cwd=member_root
            )
        )
        # Register acme-charts as a real Git submodule so workspace root
        # resolution and analysis exclusion discovery observe the attached
        # topology. A local bare repo is used because Git file transport is
        # disabled by default in current releases.
        bare_repo = tmp_path.parent / "acme-charts-bare.git"
        tm.ok(
            u.Cli.run_checked([
                "git",
                "clone",
                "--bare",
                member_root.as_posix(),
                bare_repo.as_posix(),
            ])
        )
        tm.ok(u.Cli.run_checked(["rm", "-rf", member_root.as_posix()]))
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=tmp_path))
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    bare_repo.as_posix(),
                    "acme-charts",
                ],
                cwd=tmp_path,
            )
        )
        provider = config.Infra.codegen.providers[0]
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "config",
                    "remote.origin.url",
                    f"{provider.base_url}/acme-charts.git",
                ],
                cwd=member_root,
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.PYPROJECT_FILENAME,
                '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
                'requires-python = ">=3.13,<3.14"\ndependencies = []\n',
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.GITMODULES,
                '[submodule "acme-charts"]\n'
                f"    path = acme-charts\n"
                f"    url = {provider.base_url}/acme-charts.git\n"
                f"    branch = {provider.branch}\n",
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"], cwd=tmp_path
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=tmp_path
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "add", c.Infra.PYPROJECT_FILENAME, c.Infra.GITMODULES],
                cwd=tmp_path,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Workspace fixture"], cwd=tmp_path
            )
        )
        tm.ok(u.Cli.run_checked(["rm", "-rf", bare_repo.as_posix()]))
        manifest_path = tmp_path / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME
        manifest_path.parent.mkdir(parents=True)
        tm.ok(
            u.Cli.yaml_dump(
                manifest_path, workspace.model_dump(mode="json", exclude_none=True)
            )
        )
        request = m.Infra.CodegenConformRequest(
            root=tmp_path,
            what=c.Infra.CodegenConformSurface.ALL,
            scope=c.Infra.CodegenConformScope.ALL,
        )
        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(request)

        plan: m.Infra.CodegenPlan = tm.ok(result)
        tm.that(
            tuple(item.name for item in plan.repositories),
            eq=(root.name, "acme-charts"),
        )
        external_root = (tmp_path / "acme-content").resolve()
        tm.that(
            any(
                external_root == file.path or external_root in file.path.parents
                for file in plan.files
            ),
            eq=False,
        )
        tm.that(external_root.exists(), eq=False)
        root_make_engine = next(
            file
            for file in plan.files
            if file.path
            == tmp_path.resolve() / config.Infra.codegen.surfaces.make_engine_path
        )
        tm.that(root_make_engine.rendered, has="WORKSPACE_MEMBERS := acme-charts")
        tm.that("acme-content" in root_make_engine.rendered, eq=False)
        workflows = tuple(
            file for file in plan.files if ".github/workflows" in file.path.as_posix()
        )
        # How many workflows exist is config-owned: freezing the count makes a
        # legitimate template addition fail here. The contract is that every
        # planned workflow is one the config declares, and that none leaks the
        # content-only repository.
        declared_workflows = frozenset(
            entry.path
            for entry in config.Infra.codegen.surfaces.entries
            if ".github/workflows" in entry.path
        )
        tm.that(workflows, empty=False)
        for workflow in workflows:
            tm.that(
                any(
                    workflow.path.as_posix().endswith(path)
                    for path in declared_workflows
                ),
                eq=True,
                msg=f"undeclared workflow planned: {workflow.path}",
            )
        for workflow in workflows:
            tm.that("acme-content" in workflow.rendered, eq=False)
        gitmodules_plan = next(
            file for file in plan.files if file.path.name == c.Infra.GITMODULES
        )
        gitmodules = gitmodules_plan.rendered
        tm.that(gitmodules, has='[submodule "acme-charts"]')
        tm.that("acme-content" in gitmodules, eq=False)
        tm.ok(u.Cli.atomic_write_text_file(gitmodules_plan.path, gitmodules))
        fixed_point: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(initial_workspace=workspace).plan(request)
        )
        fixed_gitmodules = next(
            file for file in fixed_point.files if file.path.name == c.Infra.GITMODULES
        )
        tm.that(fixed_gitmodules.changed, eq=False)
        tm.that(fixed_gitmodules.rendered, eq=gitmodules)
        mise = tomllib.loads(
            next(file.rendered for file in plan.files if file.path.name == ".mise.toml")
        )
        tm.that(
            mise["tools"]["go:github.com/steveyegge/beads/cmd/bd"],
            eq=config.Infra.codegen.toolchain.beads.version,
        )
        qlty_tool = config.Infra.codegen.toolchain.qlty
        tm.that(mise["tools"][qlty_tool.selector], eq=qlty_tool.version)
        qlty = tomllib.loads(
            next(
                file.rendered
                for file in plan.files
                if file.path.as_posix().endswith(".qlty/qlty.toml")
            )
        )
        qlty_policy = config.Infra.tooling.tools.qlty
        tm.that(qlty["config_version"], eq=qlty_policy.config_version)
        tm.that(
            qlty["source"], eq=[source.model_dump() for source in qlty_policy.sources]
        )
        tm.that(
            qlty["smells"],
            eq={
                smell.check: {"threshold": smell.threshold}
                for smell in qlty_policy.smell_thresholds
            },
        )
        pyproject = tomllib.loads(
            next(
                file.rendered
                for file in plan.files
                if file.path.name == c.Infra.PYPROJECT_FILENAME
            )
        )
        tools = pyproject["tool"]
        tm.that("acme-content" in tools["ruff"]["exclude"], eq=False)
        tm.that("acme-content" in tools["pyright"]["exclude"], eq=False)


__all__: tuple[str, ...] = ()
