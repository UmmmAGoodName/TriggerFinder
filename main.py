import os
import re
import json
from collections import defaultdict

# === CONFIGURATION ===
INPUT_DIR = r"C:\redENGINE\Dumps\45.84.198.89"  # 🔁 change this
#OUTPUT_JSON = "fivem_full_scan.json"
print(f"[🔍] Scanning directory: {INPUT_DIR}")

# === REGEX PATTERNS ===

# Triggers (categorized)
regex_patterns = {
    "client": {
        "TriggerServerEvent": r'TriggerServerEvent\([\'"](.+?)[\'"]',
        "TriggerEvent": r'TriggerEvent\([\'"](.+?)[\'"]',
        "RegisterNetEvent": r'RegisterNetEvent\([\'"](.+?)[\'"]\)',
        "AddEventHandler": r'AddEventHandler\([\'"](.+?)[\'"]\)',
    },
    "server": {
        "TriggerClientEvent": r'TriggerClientEvent\([\'"](.+?)[\'"]',
        "RegisterCommand": r'RegisterCommand\([\'"](.+?)[\'"]',
        "RegisterNetEvent": r'RegisterNetEvent\([\'"](.+?)[\'"]\)',
        "AddEventHandler": r'AddEventHandler\([\'"](.+?)[\'"]\)',
    }
}

# Webhook pattern
webhook_regex = r'(https?:\/\/(?:discord|discordapp)\.com\/api\/webhooks\/\d+\/[a-zA-Z0-9_.-]+)'
coord_regex = r"x\s*=\s*([-\d.]+)\s*,\s*y\s*=\s*([-\d.]+)\s*,\s*z\s*=\s*([-\d.]+)"


# === DATA STORAGE ===
triggers = {
    "client": defaultdict(set),
    "server": defaultdict(set)
}
webhooks_found = []
coordinates_found = []

# === MAIN WALK ===
for (root, dirs, files) in os.walk(INPUT_DIR):
    for file in files:
        full_path = os.path.join(root, file)
        ext = os.path.splitext(file)[1].lower()

        if ext not in {".lua", ".json"}:
            print(f"[⚠️] Skipping unsupported file: {full_path}")
            continue

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                print(f"[✔] Successfully read: {full_path}")
        except Exception as e:
            print(f"[!] Failed to read {full_path}: {e}")
            continue

        # ── Trigger scanning (only for .lua)
        if ext == ".lua":
            for category, patterns in regex_patterns.items():
                for label, pattern in patterns.items():
                    matches = re.findall(pattern, content)
                    for match in matches:
                        triggers[category][label].add(match)
                        
        # ── Coordinate extraction
        coord_matches = re.findall(coord_regex, content)
        for x, y, z in coord_matches:
            coordinates_found.append({
                "file": full_path,
                "x": float(x),
                "y": float(y),
                "z": float(z)
            })

        for line in content.splitlines():
            match = re.search(webhook_regex, line)
            if match:
                webhook_url = match.group(1)
                webhooks_found.append({
                    "url": webhook_url,
                    "file": full_path  # absolute path
                })



# === OUTPUT ===
output = {
    "client": {k: sorted(list(v)) for k, v in triggers["client"].items()},
    "server": {k: sorted(list(v)) for k, v in triggers["server"].items()},
    "webhooks": webhooks_found,
    "coordinates": coordinates_found
}


# === OUTPUT JSON STRUCTURE ===

# Create JSON file based on dump name and current timestamp
dump_name = os.path.basename(INPUT_DIR.rstrip("\\/"))
OUTPUT_JSON = f"{dump_name}_full_scan_.json"

# Save JSON output
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"[✔] Scan complete. Output saved to: {OUTPUT_JSON}")
