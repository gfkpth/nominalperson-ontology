import os
import subprocess
import sys

def write_yaml(path, id_val, uri_val):
    """Writes a simple W3ID YAML configuration file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(f'id: {id_val}\n')
        f.write(f'redirect: true\n')
        f.write(f'uri: {uri_val}\n')

def main():
    # --- Configuration (Read from Environment Variables passed by Makefile) ---
    # The second argument is the fallback default if the variable isn't set
    GITHUB_USER = os.getenv("GITHUB_USER", "gfkpth")
    REPO_NAME   = os.getenv("REPO_NAME", "nompers-ontology")
    BASE_ID     = os.getenv("BASE_ID", "nompers")
    
    W3ID_BASE   = os.getenv("W3ID_BASE", f"https://w3id.org/{BASE_ID}")
    RAW_BASE    = os.getenv("RAW_BASE", f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/nompers.ttl")
    
    CONFIG_DIR  = "w3id_config"
    VERSION_DIR = os.path.join(CONFIG_DIR, BASE_ID)

    print(f"Generating W3ID configuration files for '{BASE_ID}'...")

    # 1. Generate the base (non-versioned) file: config/nompers.yaml
    base_filename = os.path.join(CONFIG_DIR, f"{BASE_ID}.yaml")
    write_yaml(base_filename, W3ID_BASE, RAW_BASE)
    print(f"Generated base: {base_filename} -> {W3ID_BASE}")

    # 2. Get all git tags starting with 'v'
    try:
        # Get tags, strip whitespace, and filter out empty strings
        result = subprocess.check_output(['git', 'tag', '-l', 'v*'], text=True).strip()
        tags = result.split('\n') if result else []
    except subprocess.CalledProcessError as e:
        print(f"Error reading git tags: {e}")
        sys.exit(1)

    if not tags:
        print("o version tags found (e.g., v0.0.1). Skipping versioned files.")
        return

    # 3. Generate versioned files
    for tag in tags:
        # Strip 'v' prefix (e.g., 'v0.0.2' -> '0.0.2')
        version = tag[1:]
        if not version:
            continue

        # Target IRI: https://w3id.org/nompers/0.0.2
        target_id = f"{W3ID_BASE}/{version}"
        
        # Target URI: https://raw.githubusercontent.com/gfkpth/nompers-ontology/v0.0.2/nompers.ttl
        target_uri = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{tag}/nompers.ttl"
        
        # W3ID expects: config/nompers/0.0.2.yaml
        filename = os.path.join(VERSION_DIR, f"{version}.yaml")
        
        write_yaml(filename, target_id, target_uri)
        print(f"Generated versioned: {filename} -> {target_id}")

    print("\nAll done! Files are in the 'w3id_config/' directory.")

if __name__ == "__main__":
    main()