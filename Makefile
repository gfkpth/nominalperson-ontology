# --- Configuration (Single Source of Truth) ---
export GITHUB_USER := gfkpth
export REPO_NAME   := nompers-ontology
export BASE_ID     := gfkpth/nompers

# These are derived from the variables above
export W3ID_BASE   := https://w3id.org/$(BASE_ID)
export RAW_BASE    := https://raw.githubusercontent.com/$(GITHUB_USER)/$(REPO_NAME)/main/nompers.ttl

# --- Targets ---

.PHONY: all clean w3id-generate w3id-clean

all: w3id-generate

## Generate the W3ID configuration files using the helper script
w3id-generate:
	@python3 scripts/generate_w3id_config.py

## Remove generated W3ID configuration files
w3id-clean:
	@echo "Cleaning up 'w3id_config/'..."
	rm -rf w3id_config/