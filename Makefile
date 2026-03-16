# flext-infra - Infrastructure Tooling
PROJECT_NAME := flext-infra
ifneq ("$(wildcard ../base.mk)", "")
include ../base.mk
else
include base.mk
endif

# === PROJECT-SPECIFIC TARGETS ===
.PHONY: docs-serve

docs-serve: ## Serve documentation
	$(Q)$(POETRY) run mkdocs serve

.DEFAULT_GOAL := help
