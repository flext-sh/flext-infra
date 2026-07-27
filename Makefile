# flext-infra — generated project interface.
# Managed by flext-infra codegen conform for new and existing repositories.

SHELL := /bin/sh
.DEFAULT_GOAL := help

PROJECT_NAME := flext-infra
MAKE_PROFILE := workspace-member
WORKSPACE_ROOT_REL := ..
WORKSPACE_MEMBERS :=
WORKSPACE_EDITABLES := $(PROJECT_NAME):.
UV_LINK_MODE := copy

APPLY ?= N
ARGS ?=
PROJECTS ?=
# Public selector documented by base.mk. Forwarded to the test recipe so a
# focused run stays inside the canonical Make surface instead of forcing a
# loose pytest invocation.
PYTEST_ARGS ?=
WHAT ?=

PROJECT_ROOT := $(shell pwd -P)
PUBLIC_VERBS := help setup deps build check test format run status docs clean release codegen
RUFF_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests
MYPY_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests
UV ?= uv

# === MYPY RESOURCE LIMIT ===
# mro-0ftd.3.11: every Mypy process inherits validated memory and time caps.
MYPY_MEMORY_LIMIT_MB ?= 6144
MYPY_TIMEOUT_SECONDS ?= 600
MYPY_BOUNDED = timeout --signal=TERM --kill-after=5s "$(MYPY_TIMEOUT_SECONDS)s" prlimit --as=$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )):$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )) --
VALIDATE_MYPY_LIMITS = case "$(MYPY_MEMORY_LIMIT_MB)" in ""|*[!0-9]*) echo "ERROR: MYPY_MEMORY_LIMIT_MB must be a positive integer"; exit 2;; esac; [ "$(MYPY_MEMORY_LIMIT_MB)" -gt 0 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be greater than zero"; exit 2; }; [ "$(MYPY_MEMORY_LIMIT_MB)" -le 6144 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be less than or equal to 6144"; exit 2; }; case "$(MYPY_TIMEOUT_SECONDS)" in ""|*[!0-9]*) echo "ERROR: MYPY_TIMEOUT_SECONDS must be a positive integer"; exit 2;; esac; [ "$(MYPY_TIMEOUT_SECONDS)" -gt 0 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be greater than zero"; exit 2; }; [ "$(MYPY_TIMEOUT_SECONDS)" -le 600 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be less than or equal to 600"; exit 2; }; command -v timeout >/dev/null 2>&1 || { echo "ERROR: required executable not found: timeout"; exit 2; }; command -v prlimit >/dev/null 2>&1 || { echo "ERROR: required executable not found: prlimit"; exit 2; }
REPORT_MYPY_FAILURE = code=$$?; signal=none; if [ "$$code" -ge 128 ]; then signal=$$(( $$code - 128 )); fi; if [ "$$code" -eq 124 ] || [ "$$signal" != none ]; then reason="resource limit triggered"; else reason="type check failed under enforced limits"; fi; echo "ERROR: Mypy $$reason: memory_limit=$(MYPY_MEMORY_LIMIT_MB) MiB; timeout=$(MYPY_TIMEOUT_SECONDS)s; exit=$$code; signal=$$signal" >&2
export MYPY_MEMORY_LIMIT_MB MYPY_TIMEOUT_SECONDS


_DEFAULT_help := usage
_DEFAULT_deps := check
_DEFAULT_build := artifacts
_DEFAULT_check := all
_DEFAULT_test := all
_DEFAULT_format := check
_DEFAULT_run := default
_DEFAULT_status := diagnostics
_DEFAULT_docs := check
_DEFAULT_clean := generated
_DEFAULT_release := status
_DEFAULT_codegen := check


ifneq ($(filter $(MAKE_PROFILE),workspace-root workspace-member standalone),$(MAKE_PROFILE))
$(error Invalid MAKE_PROFILE '$(MAKE_PROFILE)')
endif

ifeq ($(MAKE_PROFILE),workspace-member)
DECLARED_WORKSPACE_ROOT := $(shell cd "$(PROJECT_ROOT)/$(WORKSPACE_ROOT_REL)" 2>/dev/null && pwd -P)
SUPERPROJECT_ROOT_RAW := $(shell git rev-parse --show-superproject-working-tree 2>/dev/null)
SUPERPROJECT_ROOT := $(shell test -n "$(SUPERPROJECT_ROOT_RAW)" && cd "$(SUPERPROJECT_ROOT_RAW)" 2>/dev/null && pwd -P)
ifeq ($(SUPERPROJECT_ROOT),$(DECLARED_WORKSPACE_ROOT))
ATTACHED_MEMBER := Y
RUNTIME_ROOT := $(DECLARED_WORKSPACE_ROOT)
else
ATTACHED_MEMBER := N
RUNTIME_ROOT := $(PROJECT_ROOT)
endif
else
ATTACHED_MEMBER := N
RUNTIME_ROOT := $(PROJECT_ROOT)
endif

RUNTIME_VENV := $(RUNTIME_ROOT)/.venv
RUNTIME_PYTHON := $(RUNTIME_VENV)/bin/python
override UV_PROJECT := $(RUNTIME_ROOT)
override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)
override VIRTUAL_ENV := $(RUNTIME_VENV)
override PATH := $(RUNTIME_VENV)/bin:/usr/local/bin:/usr/bin:/bin
export UV_PROJECT UV_PROJECT_ENVIRONMENT VIRTUAL_ENV PATH

ifeq ($(MAKE_PROFILE),workspace-root)
CODEGEN_SCOPE := all
ALLOWED_PROJECTS := . $(WORKSPACE_MEMBERS)
else
CODEGEN_SCOPE := self
ALLOWED_PROJECTS := .
endif

# Workspace-root gate verbs fan out across declared members through the generic
# `flext-infra workspace orchestrate` primitive (verb allowlist + CLI group come
# from the constants SSOT, never hardcoded here). Members and standalone projects
# run the gate locally. FAIL_FAST forwards the stop-on-first-failure policy.
WORKSPACE_ORCHESTRATE = $(UV_RUN) python -m flext_infra workspace orchestrate
ORCHESTRATED_VERBS := build check clean docs scan test val

UV ?= uv
UV_RUN := $(UV) run --project "$(RUNTIME_ROOT)" --no-sync
PROJECT_INFRA_PYTHONPATH ?= $(PROJECT_ROOT)/src
PROJECT_FLEXT_INFRA := test -x "$(FLEXT_INFRA_PYTHON)" || { printf 'ERROR: FLEXT_INFRA_PYTHON must name an executable managed Python\n' >&2; exit 2; }; env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(dir $(FLEXT_INFRA_PYTHON)):/usr/bin:/bin" PYTHONPATH="$(PROJECT_INFRA_PYTHONPATH)" $(FLEXT_INFRA_PYTHON) -m flext_infra
# mro-j47u (codex): scaffold dev tools live in the validated optional dev
# profile; a fresh project must create its lock before later check-mode locks.
UV_SYNC_FLAGS := --all-extras --all-groups


-include custom.mk

_BUILTIN_HANDLERS := \
	_builtin_help_usage \
	_builtin_deps_check \
	_builtin_deps_lock \
	_builtin_deps_upgrade \
	_builtin_build_artifacts \
	_builtin_check_all \
	_builtin_test_all \
	_builtin_format_check \
	_builtin_format_apply \
	_builtin_run_default \
	_builtin_status_diagnostics \
	_builtin_docs_check \
	_builtin_clean_generated \
	_builtin_release_status \
	_builtin_codegen_check \
	_builtin_codegen_apply

define _dispatch
	@what="$(strip $(WHAT))"; \
	if [ -z "$$what" ]; then what="$(_DEFAULT_$@)"; fi; \
	case "$$what" in \
		*[!a-z0-9_-]*|'') printf 'ERROR: invalid WHAT selector %s\n' "$$what" >&2; exit 2 ;; \
	esac; \
	builtin="_builtin_$@_$$what"; \
	custom="_custom_$@_$$what"; \
	for hook in "pre-$@" "pre-$@-$$what"; do \
		$(MAKE) --no-print-directory -q "$$hook" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then $(MAKE) --no-print-directory "$$hook" || exit $$?; fi; \
	done; \
	case " $(_BUILTIN_HANDLERS) " in \
		*" $$builtin "*) $(MAKE) --no-print-directory "$$builtin" || exit $$? ;; \
		*) $(MAKE) --no-print-directory "$$custom" || exit $$? ;; \
	esac; \
	for hook in "post-$@-$$what" "post-$@"; do \
		$(MAKE) --no-print-directory -q "$$hook" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then $(MAKE) --no-print-directory "$$hook" || exit $$?; fi; \
	done
endef

define _require_apply
	@if [ "$(APPLY)" != "Y" ]; then \
		printf 'ERROR: this action requires APPLY=Y\n' >&2; \
		exit 2; \
	fi
endef

define _run_for_selected_projects
	@set -eu; \
	selected="$(strip $(PROJECTS))"; \
	if [ -z "$$selected" ]; then selected="."; fi; \
	for project in $$selected; do \
		case " $(ALLOWED_PROJECTS) " in \
			*" $$project "*) ;; \
			*) printf 'ERROR: undeclared project %s\n' "$$project" >&2; exit 2 ;; \
		esac; \
		$(UV) lock --project "$(PROJECT_ROOT)/$$project" $(1); \
		$(UV) lock --project "$(PROJECT_ROOT)/$$project" $(1); \
	done
endef

.PHONY: $(PUBLIC_VERBS) $(_BUILTIN_HANDLERS)

$(filter-out setup,$(PUBLIC_VERBS)):
	$(call _dispatch)

setup:
	@if [ -n "$(strip $(WHAT))" ]; then printf 'ERROR: setup does not accept WHAT\n' >&2; exit 2; fi
	@$(MAKE) --no-print-directory _builtin_setup_environment

_builtin_help_usage:
	@printf '%s\n' 'flext-infra [workspace-member]' ''


	@printf '  %-10s WHAT=%s\n' 'help' 'usage'



	@printf '  %-10s\n' 'setup'



	@printf '  %-10s WHAT=%s\n' 'deps' 'check'



	@printf '  %-10s WHAT=%s\n' 'build' 'artifacts'



	@printf '  %-10s WHAT=%s\n' 'check' 'all'



	@printf '  %-10s WHAT=%s\n' 'test' 'all'



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'format' 'check'



	@printf '  %-10s WHAT=%s\n' 'run' 'default'



	@printf '  %-10s WHAT=%s\n' 'status' 'diagnostics'



	@printf '  %-10s WHAT=%s\n' 'docs' 'check'



	@printf '  %-10s WHAT=%s\n' 'clean' 'generated'



	@printf '  %-10s WHAT=%s\n' 'release' 'status'



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'codegen' 'check'


	@printf '\n%s\n' 'Custom hooks (custom.mk):'
	@printf '  %s\n' 'Define pre-<verb>, post-<verb>, pre-<verb>-<what>, post-<verb>-<what>'
	@printf '  %s\n' 'in custom.mk to run extra steps at the start or end of any verb,'
	@printf '  %s\n' 'for all or some WHATs. Add _custom_<verb>_<what> to define a new WHAT.'
	@if [ -f custom.mk ]; then \
		hooks=$$(grep -oE '^(pre|post)-[a-z][a-z0-9-]*|^_custom_[a-z][a-z0-9_-]*' custom.mk 2>/dev/null | sort -u); \
		if [ -n "$$hooks" ]; then \
			printf '  %s\n' 'Defined in this project:'; \
			for hook in $$hooks; do printf '    %s\n' "$$hook"; done; \
		fi; \
	fi

# A project owns the sources it declares. Setup makes the tree exactly what the
# manifest declares, using nothing outside the tree: every declared submodule is
# initialised recursively at its recorded gitlink and placed on the branch
# declared in .gitmodules. It is a no-op when the project declares no
# submodules, and it converges on re-run. It never moves a branch that holds
# work the superproject does not record: that is an error, never a warning, so
# setup can never report success over a tree that is not what it declares.
_builtin_setup_submodules:
	@set -eu; \
	if [ ! -f "$(PROJECT_ROOT)/.gitmodules" ]; then exit 0; fi; \
	git -C "$(PROJECT_ROOT)" submodule sync --recursive --quiet; \
	git -C "$(PROJECT_ROOT)" submodule update --init --recursive; \
	git -C "$(PROJECT_ROOT)" submodule foreach --recursive --quiet ' \
		branch=$$(git config -f "$$toplevel/.gitmodules" "submodule.$$name.branch" || true); \
		if [ -z "$$branch" ]; then exit 0; fi; \
		if ! git rev-parse --verify --quiet "refs/heads/$$branch" >/dev/null; then \
			git checkout --quiet -b "$$branch"; \
		elif [ "$$(git rev-parse "refs/heads/$$branch")" = "$$(git rev-parse HEAD)" ]; then \
			git checkout --quiet "$$branch"; \
		else \
			printf "ERROR: %s: branch %s is at %s but the superproject records %s\n" "$$name" "$$branch" "$$(git rev-parse --short "refs/heads/$$branch")" "$$(git rev-parse --short HEAD)" >&2; \
			printf "Reconcile that branch with the recorded gitlink, then re-run setup\n" >&2; \
			exit 1; \
		fi'

_builtin_require_environment:
	@if [ ! -x "$(RUNTIME_ROOT)/.venv/bin/python" ]; then \
		printf 'ERROR: missing environment interpreter %s; make setup creates it\n' "$(RUNTIME_ROOT)/.venv/bin/python" >&2; \
		exit 2; \
	fi

ifeq ($(MAKE_PROFILE),workspace-root)
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --no-install-project
	@$(UV) pip install --python "$(RUNTIME_PYTHON)" --no-deps --editable "$(PROJECT_ROOT)" --link-mode "$(UV_LINK_MODE)"
	@set -eu; for member in $(WORKSPACE_MEMBERS); do \
		$(UV) pip install --python "$(RUNTIME_PYTHON)" --no-deps --editable "$(PROJECT_ROOT)/$$member" --link-mode "$(UV_LINK_MODE)"; \
	done
	@$(UV) pip check --python "$(RUNTIME_PYTHON)"
else ifeq ($(MAKE_PROFILE),workspace-member)
ifeq ($(ATTACHED_MEMBER),Y)
_builtin_setup_environment: _builtin_setup_submodules
	@$(MAKE) --no-print-directory -C "$(RUNTIME_ROOT)" setup WHAT=environment
else
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --no-install-project
	@$(UV) pip install --python "$(RUNTIME_PYTHON)" --no-deps --editable "$(PROJECT_ROOT)" --link-mode "$(UV_LINK_MODE)"
endif
else
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --no-install-project
	@$(UV) pip install --python "$(RUNTIME_PYTHON)" --no-deps --editable "$(PROJECT_ROOT)" --link-mode "$(UV_LINK_MODE)"
endif

_builtin_deps_check: _builtin_require_environment
	$(call _run_for_selected_projects,--check)

_builtin_deps_lock:
	$(call _require_apply)
	$(call _run_for_selected_projects,)

_builtin_deps_upgrade:
	$(call _require_apply)
	$(call _run_for_selected_projects,--upgrade)


_builtin_build_artifacts:
	@$(UV) build --project "$(PROJECT_ROOT)"

_builtin_check_all: _builtin_require_environment
	@$(UV_RUN) ruff check --no-fix $(RUFF_PATHS)
	@$(UV_RUN) ruff format --check $(RUFF_PATHS)
	@$(UV_RUN) pyrefly check
	@$(VALIDATE_MYPY_LIMITS); $(MYPY_BOUNDED) $(UV_RUN) mypy $(MYPY_PATHS) || { $(REPORT_MYPY_FAILURE); exit $$code; }
	@$(UV_RUN) pyright
	@# NOTE (multi-agent, mro-j47u): Vulture reads its scope from generated pyproject.
	@$(UV_RUN) vulture

_builtin_test_all: _builtin_require_environment
	@$(UV_RUN) python -m pytest "$(PROJECT_ROOT)/tests" $(PYTEST_ARGS)


_builtin_format_check: _builtin_require_environment
	@$(UV_RUN) ruff check --no-fix $(RUFF_PATHS)
	@$(UV_RUN) ruff format --check $(RUFF_PATHS)

_builtin_format_apply: _builtin_require_environment
	$(call _require_apply)
	@$(UV_RUN) ruff check --fix $(RUFF_PATHS)
	@$(UV_RUN) ruff format $(RUFF_PATHS)

_builtin_run_default: _builtin_require_environment
	@$(UV_RUN) $(PROJECT_NAME) $(ARGS)

_builtin_status_diagnostics: _builtin_require_environment
	@printf 'profile=%s\nattached=%s\nproject=%s\nruntime=%s\n' \
		'$(MAKE_PROFILE)' '$(ATTACHED_MEMBER)' '$(PROJECT_ROOT)' '$(RUNTIME_ROOT)'
	@$(UV) --version
	@$(UV) lock --project "$(PROJECT_ROOT)" --check
	@if [ -x "$(RUNTIME_PYTHON)" ]; then \
		$(UV) pip check --python "$(RUNTIME_PYTHON)"; \
	fi
	@git -C "$(PROJECT_ROOT)" status --short

_builtin_docs_check:
	@test -s "$(PROJECT_ROOT)/README.md"

_builtin_clean_generated:
	$(call _require_apply)
	@find "$(PROJECT_ROOT)" -type d \
		\( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache -o -name .ruff_cache \) \
		-prune -exec rm -rf {} +
	@rm -rf "$(PROJECT_ROOT)/build" "$(PROJECT_ROOT)/dist" "$(PROJECT_ROOT)/htmlcov"
	@rm -f "$(PROJECT_ROOT)/.coverage"

_builtin_release_status: _builtin_require_environment
	@$(UV) lock --project "$(PROJECT_ROOT)" --check
	@git -C "$(PROJECT_ROOT)" diff --quiet
	@git -C "$(PROJECT_ROOT)" diff --cached --quiet

_builtin_codegen_check: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode check

_builtin_codegen_apply: _builtin_require_environment
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode apply
