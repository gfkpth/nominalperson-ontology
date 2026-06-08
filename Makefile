# --- Configuration ---
export BASE_ID     := gfkpth/nompers-ont
export GITHUB_USER := gfkpth
export REPO_NAME   := nompers-ontology

# These are derived from the variables above
export W3ID_BASE   := https://w3id.org/$(BASE_ID)
export RAW_BASE    := https://raw.githubusercontent.com/$(GITHUB_USER)/$(REPO_NAME)/main/nompers.ttl

# --- Targets ---

.PHONY: all clean generate-simplegraph generate-classdiagram generate-w3id clean-w3id

all: 
	generate-w3id
	generate-simplegraph
	generate-classdiagram

generate-simplegraph:
	@mkdir -p docs/vis
	@python3 scripts/generate_mmd.py nompers.ttl docs/vis/simple-graph.mmd --diagram_type "graph TD" --no_prefix

generate-classdiagram:
	@mkdir -p docs/vis
	@python3 scripts/generate_mmd.py nompers.ttl docs/vis/class-diagram.mmd --diagram_type "classDiagram" --include_datatype_properties --no_prefix

## Generate the W3ID configuration files using the helper script
generate-w3id:
	@python3 scripts/generate_w3id_config.py

## Remove generated W3ID configuration files
w3id-clean:
	@echo "Cleaning up 'w3id_config/'..."
	rm -rf w3id_config/