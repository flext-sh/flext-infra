"""Behavior contract for the persisted repository-artifact reference foundation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config, m
from flext_tests import tm
from git import Repo
import pytest
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


class TestsRepositoryArtifactFoundation:
    def test_public_content_validator_reports_unwritten_invalid_locators(
        self, tmp_path: Path
    ) -> None:
        repo = config.Infra.codegen.repository_artifact_authorities[0]
        authority = u.Infra.repository_artifact_authority_from_remote(
            f"https://github.com/{repo.organization}/{repo.repository}.git", repo.ref
        )
        escape = "../" + "../" + "AGENTS.md"
        absolute = "/" + "home/user/AGENTS.md"
        home = "~" + "/AGENTS.md"
        unknown = "https://github.com/unknown/repository/blob/ref/AGENTS.md"
        content = (
            f"[escape]({escape})\n[absolute]({absolute})\n"
            f"[home]({home})\n[unknown]({unknown})\n"
        )

        result = u.Infra.repository_persisted_references_validate_content(
            content, "generated/AGENTS.md", (authority,), repository_root=tmp_path
        )

        tm.that(result.success, eq=True)
        tm.that(
            [issue.code for issue in result.value.issues],
            eq=["PREF001", "PREF001", "PREF001", "PREF002"],
        )

    def test_public_content_validator_accepts_internal_unwritten_reference(
        self, tmp_path: Path
    ) -> None:
        result = u.Infra.repository_persisted_references_validate_content(
            "[law](../AGENTS.md)\n", "docs/index.md", (), repository_root=tmp_path
        )

        tm.that(result.value.issues, eq=())

    def test_public_remote_authority_derivation(self) -> None:
        repo = config.Infra.codegen.repository_artifact_authorities[0]
        remote = f"https://github.com/{repo.organization}/{repo.repository}.git"

        authority = u.Infra.repository_artifact_authority_from_remote(remote, repo.ref)

        tm.that(authority.organization, eq=repo.organization)
        tm.that(authority.repository, eq=repo.repository)
        tm.that(authority.ref, eq=repo.ref)

    def test_authority_and_reference_models_reject_invalid_segments(self) -> None:
        repo = config.Infra.codegen.repository_artifact_authorities[0]

        with pytest.raises(ValueError, match="host"):
            m.Infra.RepositoryArtifactAuthority(
                host="example.com",
                organization=repo.organization,
                repository=repo.repository,
                ref=repo.ref,
            )
        with pytest.raises(ValueError, match="canonical repository-relative"):
            m.Infra.RepositoryArtifactReference(
                authority=m.Infra.RepositoryArtifactAuthority(
                    host="github.com",
                    organization=repo.organization,
                    repository=repo.repository,
                    ref=repo.ref,
                ),
                kind=m.Infra.RepositoryArtifactKind.BLOB,
                path="docs" + "/../" + "index.md",
            )

    def test_builder_and_parser_support_slash_refs_and_encoded_paths(self) -> None:
        repo = next(
            item
            for item in config.Infra.codegen.repository_artifact_authorities
            if "/" not in item.ref
        )
        authority = m.Infra.RepositoryArtifactAuthority(
            host="github.com",
            organization=repo.organization,
            repository=repo.repository,
            ref=f"{repo.ref}/lane",
        )
        reference = m.Infra.RepositoryArtifactReference(
            authority=authority,
            kind=m.Infra.RepositoryArtifactKind.BLOB,
            path="docs/a file.md",
            fragment="section one",
        )

        url = u.Infra.repository_artifact_url(reference)
        parsed = u.Infra.repository_artifact_parse(url, (authority,))

        tm.that(parsed.success, eq=True)
        tm.that(parsed.value, eq=reference)
        tm.that(url, has="a%20file.md")

    def test_parser_rejects_invalid_authority_ref_and_traversal(self) -> None:
        repo = config.Infra.codegen.repository_artifact_authorities[0]
        authority = m.Infra.RepositoryArtifactAuthority(
            host="github.com",
            organization=repo.organization,
            repository=repo.repository,
            ref=repo.ref,
        )
        base = f"https://{authority.host}/{authority.organization}/{authority.repository}/blob"
        invalid = (
            f"{base}/wrong/docs/index.md",
            f"{base}/{authority.ref}/docs/%2E%2E/index.md",
            f"{base}/{authority.ref}/docs/%252E%252E/index.md",
            f"https://user@{authority.host}/{authority.organization}/{authority.repository}/blob/{authority.ref}/docs/index.md",
        )

        results = tuple(
            u.Infra.repository_artifact_parse(value, (authority,)) for value in invalid
        )

        tm.that(all(result.failure for result in results), eq=True)

    def test_candidate_payloads_use_current_tree_and_untracked_files(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        tracked = root / "tracked.md"
        deleted = root / "deleted.md"
        tracked.write_text("indexed", encoding="utf-8")
        deleted.write_text("deleted", encoding="utf-8")
        git = Repo.init(root)
        git.index.add([tracked.name, deleted.name])
        tracked.write_text("working", encoding="utf-8")
        deleted.unlink()
        (root / "untracked.md").write_text("untracked", encoding="utf-8")
        (root / "authority").symlink_to("docs/AGENTS.md")

        result = u.Infra.git_candidate_payloads(m.Infra.GitRepoRequest(repo_root=root))

        payloads = {payload.path: payload.content for payload in result.value.payloads}
        tm.that(payloads[tracked.name], eq=b"working")
        tm.that(payloads["untracked.md"], eq=b"untracked")
        tm.that(payloads["authority"], eq=b"docs/AGENTS.md")
        tm.that(deleted.name in payloads, eq=False)

    def test_semantic_validator_ignores_runtime_path_prose(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        (root / "module.py").write_text(
            "from pathlib import Path\nROOT = Path.cwd()\n", encoding="utf-8"
        )
        Repo.init(root).index.add(["module.py"])

        result = u.Infra.repository_persisted_references_validate(
            root, (), config.Infra.codegen.templates.entries
        )

        tm.that(result.value.issues, eq=())

    def test_semantic_validator_resolves_template_destination(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "repo"
        template = (
            root
            / "src/flext_infra/templates/project/base/.github/copilot-instructions.md.j2"
        )
        template.parent.mkdir(parents=True)
        template.write_text("[law](../AGENTS.md)\n", encoding="utf-8")
        Repo.init(root).index.add([template.relative_to(root).as_posix()])

        result = u.Infra.repository_persisted_references_validate(
            root, (), config.Infra.codegen.templates.entries
        )

        tm.that(result.value.issues, eq=())

    def test_semantic_validator_rejects_explicit_escaping_comment(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        target = "../" + "../" + "authority.md"
        (root / "module.py").write_text(
            f'# canonical authority lives in "{target}"\n', encoding="utf-8"
        )
        Repo.init(root).index.add(["module.py"])

        result = u.Infra.repository_persisted_references_validate(root, ())

        tm.that([issue.code for issue in result.value.issues], eq=["PREF001"])

    def test_public_validator_uses_explicit_authorities(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        repo = config.Infra.codegen.repository_artifact_authorities[0]
        authority = u.Infra.repository_artifact_authority_from_remote(
            f"https://github.com/{repo.organization}/{repo.repository}.git", repo.ref
        )
        reference = m.Infra.RepositoryArtifactReference(
            authority=authority,
            kind=m.Infra.RepositoryArtifactKind.BLOB,
            path="docs/index.md",
        )
        (root / "AGENTS.md").write_text(
            f"[authority]({u.Infra.repository_artifact_url(reference)})\n",
            encoding="utf-8",
        )
        Repo.init(root).index.add(["AGENTS.md"])

        result = u.Infra.repository_persisted_references_validate(root, (authority,))

        tm.that(result.value.issues, eq=())


__all__: tuple[str, ...] = ()
