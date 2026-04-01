.PHONY: validate validate-plugins validate-skills help

PLUGINS := $(wildcard plugins/*)

validate: validate-plugins validate-skills ## Run all validations

validate-plugins: ## Validate all plugins with claude plugin validate
	@for plugin in $(PLUGINS); do \
		echo "Validating $$plugin..."; \
		claude plugin validate $$plugin; \
		echo ""; \
	done

validate-skills: ## Validate SKILL.md frontmatter against Claude Code docs
	@python3 scripts/validate-skills.py .

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
