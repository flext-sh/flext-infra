# Snapshot refresh is an explicit repository operation, separate from make mod.
_custom-mod-snapshots:
	@$(PROJECT_FLEXT_INFRA) refactor mod-snapshots --repository-root "$(PROJECT_ROOT)" --apply
