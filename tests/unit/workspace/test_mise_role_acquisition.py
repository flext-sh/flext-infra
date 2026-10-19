"""Real native Mise roles retain source, lock, scope and binary identities."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, p
from flext_infra.codegen import FlextInfraCodegenMiseToolchainProof
from tests import m, tm, u


class TestsMiseRoleAcquisition:
    """No simulated command runner or substitute executable qualifies a role."""

    @staticmethod
    def _request(scope: Path) -> m.Infra.MiseRoleRequest:
        owner = Path(__file__).resolve().parents[3]
        reader = tm.ok(u.Infra.managed_mise_self(owner))
        entry = next(
            tool for tool in config.Infra.codegen.toolchain.tools if tool.name == "node"
        )
        lock = tm.ok(u.Cli.toml_read_json(owner / c.Infra.MISE_LOCK_FILENAME))
        version, _ = tm.ok(
            FlextInfraCodegenMiseToolchainProof.lock_identity(
                entry,
                lock,
                tm.ok(FlextInfraCodegenMiseToolchainProof.current_platform()),
            )
        )
        source = tm.ok(
            u.Cli.atomic_read_binary_file_receipt(
                owner / c.Infra.MISE_LOCK_FILENAME, required=True
            )
        )
        document = entry.model_dump(mode="python")
        document["version"] = version
        declaration = m.Infra.MiseRoleDeclaration(
            role="source-fixture",
            source_inputs=(source,),
            tools=(m.Infra.MiseToolEntry.model_validate(document),),
        )
        path = scope / "role.json"
        tm.ok(u.Cli.json_write(path, declaration.model_dump(mode="json")))
        return m.Infra.MiseRoleRequest(
            declaration=tm.ok(
                u.Cli.atomic_read_binary_file_receipt(path, required=True)
            ),
            reader=tm.ok(u.Cli.atomic_read_binary_file_receipt(reader, required=True)),
            reader_manifest=tm.ok(
                u.Cli.atomic_read_binary_file_receipt(
                    owner / c.Infra.MISE_TOML_FILENAME, required=True
                )
            ),
            reader_lock=source,
            scope_root=scope,
            target_root=scope / "installed-role",
        )

    def test_exact_role_is_locked_installed_and_proven_in_its_own_scope(
        self, tmp_path: Path
    ) -> None:
        request = self._request(tmp_path)
        assert isinstance(request.reader, p.Cli.AtomicFileReceipt)
        plan = tm.ok(FlextInfraCodegenMiseToolchainProof.plan_role(request))
        result = tm.ok(FlextInfraCodegenMiseToolchainProof.acquire_role(plan))
        assert result.plan.manifest.sha256 == plan.manifest.sha256
        assert result.plan.lock.sha256 == plan.lock.sha256
        binary = result.executables["node"]
        assert isinstance(binary, p.Cli.AtomicFileReceipt)
        assert Path(binary.path).is_relative_to(request.target_root / "data")
        assert (
            binary.sha256
            == tm.ok(
                u.Cli.atomic_read_binary_file_receipt(binary.path, required=True)
            ).sha256
        )
        assert (
            tm.ok(
                u.Cli.atomic_read_binary_file_receipt(
                    request.reader.path, required=True
                )
            )
            == request.reader
        )

    def test_changed_declaration_is_denied_before_target_creation(
        self, tmp_path: Path
    ) -> None:
        request = self._request(tmp_path)
        path = Path(request.declaration.path)
        tm.ok(
            u.Cli.files_write_text(
                path, path.read_text(encoding=c.DEFAULT_ENCODING) + "\n"
            )
        )
        tm.fail(
            FlextInfraCodegenMiseToolchainProof.plan_role(request),
            has="source identity changed",
        )
        assert not request.target_root.exists()

    def test_target_outside_explicit_scope_is_denied(self, tmp_path: Path) -> None:
        request = self._request(tmp_path)
        document = request.model_dump(mode="python")
        document["target_root"] = tmp_path.parent / (tmp_path.name + "-outside")
        outside = m.Infra.MiseRoleRequest.model_validate(document)
        tm.fail(
            FlextInfraCodegenMiseToolchainProof.plan_role(outside),
            has="invalid new Mise role target",
        )
        assert not outside.target_root.exists()

    def test_changed_native_lock_cannot_be_used_for_installation(
        self, tmp_path: Path
    ) -> None:
        request = self._request(tmp_path)
        plan = tm.ok(FlextInfraCodegenMiseToolchainProof.plan_role(request))
        path = Path(plan.lock.path)
        tm.ok(
            u.Cli.files_write_text(
                path, path.read_text(encoding=c.DEFAULT_ENCODING) + "\n"
            )
        )
        tm.fail(
            FlextInfraCodegenMiseToolchainProof.acquire_role(plan),
            has="source identity changed",
        )
        assert not (request.target_root / "data" / "installs" / "node").exists()
