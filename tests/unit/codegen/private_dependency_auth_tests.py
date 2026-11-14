"""Generated setup jobs keep the private-dependency credential out of global Git.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import base64
import os
from collections.abc import Mapping
from pathlib import Path

from flext_infra import config
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodegenPrivateDependencyAuth:
    """Run the generated credential step exactly as the runner runs it.

    The generated network bootstrap refuses a credential-bearing global
    ``url.<base>.insteadOf`` rewrite, because it shadows the fleet SSH route.
    A workflow that wrote one before ``make setup`` stopped every consumer CI
    job at setup (cosmos-gitops run 42397901984). The step consuming the
    minted App token must therefore leave global Git configuration untouched
    and hand Git that token only for the declared repositories.
    """

    _WORKFLOWS = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows"
    )
    _OWNER = "example-owner"
    _GRANTED = ("example-private-a", "example-private-b")
    _MINTED = "fixture-only-installation-value"
    _APP_ID_SETTING = "CI_DEPENDENCIES_APP_ID"
    _SIGNING_SETTING = "CI_DEPENDENCIES_APP_PRIVATE_KEY"
    _GLOBAL_SOURCE = "[user]\n\tname = fixture-global-identity\n"

    _SUPERPROJECT = m.Infra.CiSuperprojectCheckoutSpec.model_validate({
        "repository": f"{_OWNER}/example-superproject",
        "ref": "develop",
        "path": "apps/example-workspace",
        "submodules": ("apps/example-workspace", "apps/example-sibling"),
    })

    @classmethod
    def _jobs(
        cls,
        template: str,
        *,
        attached: bool = False,
    ) -> tuple[t.JsonMapping, ...]:
        """Render one workflow for a private-dependency member.

        Returns:
            Every rendered job in declaration order.

        """
        auth = m.Infra.CiPrivateDependencyAuthSpec.model_validate({
            "app_id_secret": cls._APP_ID_SETTING,
            "private_key_secret": cls._SIGNING_SETTING,
            "repositories": cls._GRANTED,
        })
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="example-workspace",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="develop",
            ci_trigger_branches=("develop", "main"),
        ).model_copy(
            update={
                "private_dependency_auth": auth,
                "superproject": cls._SUPERPROJECT if attached else None,
            },
        )
        rendered = tm.ok(u.Cli.template_render(cls._WORKFLOWS / template, spec))
        document = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tm.ok(u.Cli.yaml_parse(rendered)),
        )
        jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
        return tuple(
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(raw) for raw in jobs.values()
        )

    @classmethod
    def _setup_jobs(
        cls,
        template: str,
        *,
        attached: bool = False,
    ) -> tuple[t.JsonMapping, ...]:
        """Render one workflow and return its jobs that run ``make setup``.

        Returns:
            Every rendered job with a ``make setup`` step.

        """
        return tuple(
            job
            for job in cls._jobs(template, attached=attached)
            if any(cls._runs_setup(step) for step in cls._steps(job))
        )

    @staticmethod
    def _steps(job: t.JsonMapping) -> tuple[t.JsonMapping, ...]:
        """Return the typed steps of one rendered job.

        Returns:
            The job steps in declaration order.

        """
        return tuple(
            u.Cli.JSON_MAPPING_ADAPTER.validate_python(step)
            for step in u.json_list_adapter().validate_python(job.get("steps", []))
        )

    @staticmethod
    def _runs_setup(step: t.JsonMapping) -> bool:
        """Return whether one step runs the public setup verb.

        Returns:
            True when the step command ends with ``make setup``.

        """
        return str(step.get("run", "")).split()[-2:] == ["make", "setup"]

    @staticmethod
    def _mint(steps: tuple[t.JsonMapping, ...]) -> t.JsonMapping:
        """Return the step minting the App installation token.

        Returns:
            The declared ``create-github-app-token`` step.

        """
        action = config.Infra.codegen.github_actions["create-github-app-token"]
        return next(
            step
            for step in steps
            if str(step.get("uses", "")).startswith(f"{action.repository}@")
        )

    @classmethod
    def _token_consumer(
        cls,
        steps: tuple[t.JsonMapping, ...],
    ) -> tuple[t.JsonMapping, str]:
        """Return the step receiving the minted token and its token expression.

        Returns:
            The consuming step and the minted token output expression.

        """
        mint = cls._mint(steps)
        grant = u.Cli.JSON_MAPPING_ADAPTER.validate_python(mint["with"])
        tm.that(grant["repositories"], eq=",".join(cls._GRANTED))
        tm.that(grant["permission-contents"], eq="read")
        token_output = f"${{{{ steps.{mint['id']}.outputs.token }}}}"
        # A step output is empty before its step runs: every reader of the
        # minted token, a superproject checkout's ``with.token`` included,
        # must come after the mint step.
        readers = tuple(
            step
            for step in steps
            if any(
                token_output
                in u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    step.get(section, {}),
                ).values()
                for section in ("env", "with")
            )
        )
        tm.that(readers, empty=False)
        for reader in readers:
            tm.that(steps.index(mint) < steps.index(reader))
        consumer = next(
            step
            for step in reversed(steps)
            if token_output
            in u.Cli.JSON_MAPPING_ADAPTER.validate_python(step.get("env", {})).values()
        )
        setup = next(step for step in steps if cls._runs_setup(step))
        tm.that(steps.index(consumer) < steps.index(setup))
        tm.that(consumer["shell"], eq="bash")
        return consumer, token_output

    @classmethod
    def _run_as_runner(
        cls,
        root: Path,
        step: t.JsonMapping,
        environment: Mapping[str, str],
    ) -> Mapping[str, str]:
        """Run one ``shell: bash`` step as GitHub runs it; return its exports.

        Returns:
            The variables the step exported through ``GITHUB_ENV``.

        """
        github_env = root / "github.env"
        github_env.write_text("", encoding="utf-8")
        # GitHub runs a ``shell: bash`` step as
        # ``bash --noprofile --norc -eo pipefail {0}``.
        executed = tm.ok(
            u.Cli.run_raw(
                (
                    "bash",
                    "--noprofile",
                    "--norc",
                    "-eo",
                    "pipefail",
                    "-c",
                    str(step["run"]),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        **environment,
                        "GITHUB_ENV": str(github_env),
                        "GITHUB_REPOSITORY_OWNER": cls._OWNER,
                    },
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(executed.outcome))
        tm.that(executed.stdout + executed.stderr, lacks=cls._MINTED)
        return dict(
            line.split("=", maxsplit=1)
            for line in github_env.read_text(encoding="utf-8").splitlines()
        )

    @staticmethod
    def _extraheader(
        root: Path,
        url: str,
        environment: Mapping[str, str],
    ) -> p.Cli.CommandOutput:
        """Ask native Git for the HTTP header it sends to one URL.

        Returns:
            The native ``git config --get-urlmatch`` process output.

        """
        return tm.ok(
            u.Cli.run_raw(
                (c.Infra.GIT, "config", "--get-urlmatch", "http.extraheader", url),
                cwd=root,
                options=m.Cli.ProcessOptions(env=environment),
            ),
        )

    def _assert_token_scoped(self, root: Path, job: t.JsonMapping) -> None:
        """Run one job's credential step and observe Git's resulting routes."""
        consumer, token_output = self._token_consumer(self._steps(job))
        root.mkdir()
        global_config = root / "global.gitconfig"
        global_config.write_text(self._GLOBAL_SOURCE, encoding="utf-8")
        git_environment = {
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": c.ParserBooleanToken.ONE,
            "GIT_CONFIG_PARAMETERS": "",
            "GIT_CONFIG_COUNT": "0",
        }
        exported = self._run_as_runner(
            root,
            consumer,
            {
                **git_environment,
                **{
                    name: self._MINTED
                    for name, value in u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                        consumer["env"],
                    ).items()
                    if value == token_output
                },
            },
        )
        tm.that(global_config.read_text(encoding="utf-8"), eq=self._GLOBAL_SOURCE)
        later_steps = {**git_environment, **exported}
        authorization = base64.b64encode(
            f"x-access-token:{self._MINTED}".encode(),
        ).decode()
        for repository in self._GRANTED:
            for suffix in ("", c.GIT_DIR_NAME):
                url = f"https://github.com/{self._OWNER}/{repository}{suffix}"
                tm.that(
                    self._extraheader(root, url, later_steps).stdout.strip(),
                    eq=f"AUTHORIZATION: basic {authorization}",
                )
        for ungranted in (
            f"https://github.com/{self._OWNER}/example-public",
            f"https://github.com/other-owner/{self._GRANTED[0]}",
        ):
            tm.that(
                self._extraheader(root, ungranted, later_steps).outcome.raw_return_code,
                eq=1,
            )

    @c.Tests.MARK.parametrize("attached", [False, True])
    @c.Tests.MARK.parametrize(
        "template",
        ["ci.yml.j2", "release-plan.yml.j2", "docs.yml.j2"],
    )
    def test_setup_jobs_scope_the_minted_token_to_declared_repositories(
        self,
        tmp_path: Path,
        template: str,
        *,
        attached: bool,
    ) -> None:
        """The minted token reaches declared repositories, never global config.

        An attached member checks out its private superproject with that
        token, so the token is minted before the checkout (cosmos-gitops CI:
        ``repository 'https://github.com/datacosmos-br/cosmos-main/' not found``).
        """
        jobs = self._setup_jobs(template, attached=attached)
        tm.that(jobs, empty=False)
        for index, job in enumerate(jobs):
            self._assert_token_scoped(tmp_path / f"job-{index}", job)

    @c.Tests.MARK.parametrize(
        "template",
        [
            "ci.yml.j2",
            "ci-matrix.yml.j2",
            "docs.yml.j2",
            "release-plan.yml.j2",
            "release.yml.j2",
        ],
    )
    def test_superproject_checkout_follows_the_token_it_reads(
        self,
        template: str,
    ) -> None:
        """A private superproject is cloned with a token that already exists.

        Every step before that checkout runs from the job root, because the
        default working directory is the not-yet-cloned superproject path.
        """
        checked_out = 0
        for job in self._jobs(template, attached=True):
            steps = self._steps(job)
            checkout = next(
                (
                    step
                    for step in steps
                    if u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                        step.get("with", {}),
                    ).get("repository")
                    == self._SUPERPROJECT.repository
                ),
                None,
            )
            if checkout is None:
                continue
            checked_out += 1
            position = steps.index(checkout)
            tm.that(steps.index(self._mint(steps)) < position)
            for step in steps[:position]:
                if "run" in step:
                    tm.that(step.get("working-directory"), eq=".")
        tm.that(checked_out > 0)

    @c.Tests.MARK.parametrize(
        "template",
        [
            "ci.yml.j2",
            "ci-matrix.yml.j2",
            "docs.yml.j2",
            "release-plan.yml.j2",
            "release.yml.j2",
        ],
    )
    def test_member_fetch_follows_authentication_and_submodule_init(
        self,
        template: str,
    ) -> None:
        """An attached member is fetched only once Git can reach it.

        The authenticated superproject checkout skips submodules, so the
        member tree does not exist and Git holds no credential until the
        token is handed over and the submodules are initialized
        (cosmos-gitops run 43427385814: ``could not read Username``).
        """
        pinned = 0
        for job in self._jobs(template, attached=True):
            steps = self._steps(job)
            fetches = tuple(
                step
                for step in steps
                if f'git -C "{self._SUPERPROJECT.path}" fetch'
                in str(step.get("run", ""))
            )
            if not fetches:
                continue
            pinned += 1
            handovers = tuple(
                step
                for step in steps
                if "GIT_CONFIG_COUNT=" in str(step.get("run", ""))
            )
            tm.that(len(handovers), eq=1)
            tm.that(steps.index(self._mint(steps)) < steps.index(handovers[0]))
            init = next(
                step
                for step in steps
                if str(step.get("run", "")).startswith("git submodule update --init")
            )
            tm.that(init.get("working-directory"), eq=".")
            tm.that(
                init.get("run"),
                eq=(
                    "git submodule update --init --recursive -- "
                    "apps/example-workspace apps/example-sibling"
                ),
            )
            tm.that(steps.index(handovers[0]) < steps.index(init))
            tm.that(steps.index(init) < steps.index(fetches[0]))
        tm.that(pinned > 0)

    @c.Tests.MARK.parametrize(
        "template",
        ["ci.yml.j2", "docs.yml.j2", "release-plan.yml.j2", "release.yml.j2"],
    )
    def test_standalone_job_mints_after_its_own_checkout(
        self,
        template: str,
    ) -> None:
        """A standalone member keeps minting the token after its checkout."""
        action = config.Infra.codegen.github_actions["checkout"]
        minting = 0
        for job in self._jobs(template):
            steps = self._steps(job)
            if not any(step.get("id") == "private_dependency_token" for step in steps):
                continue
            minting += 1
            checkout = next(
                step
                for step in steps
                if str(step.get("uses", "")).startswith(f"{action.repository}@")
            )
            tm.that(steps.index(checkout) < steps.index(self._mint(steps)))
        tm.that(minting > 0)
