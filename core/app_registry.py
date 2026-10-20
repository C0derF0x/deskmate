import json
import subprocess
import time
from pathlib import Path


# =========================
# Registry location
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FOLDER = PROJECT_ROOT / "data"
REGISTRY_FILE = DATA_FOLDER / "applications.json"


# =========================
# Registry settings
# =========================

# Refresh the registry after this many seconds
REGISTRY_REFRESH_INTERVAL = 60 * 60 * 24


# =========================
# Scan Windows applications
# =========================

def scan_applications():

    applications = {}

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-StartApps | ConvertTo-Json -Compress"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:

        print(
            f"Failed to query Windows applications: {e}"
        )

        return applications

    if result.returncode != 0:

        print(
            "PowerShell returned an error:"
        )

        print(result.stderr)

        return applications

    try:

        data = json.loads(result.stdout)

    except json.JSONDecodeError:

        print(
            "Could not read the application list returned by Windows."
        )

        return applications

    # PowerShell returns a dictionary instead
    # of a list when only one app exists.
    if isinstance(data, dict):

        data = [data]

    for app in data:

        name = app.get("Name")
        app_id = app.get("AppID")

        if not name or not app_id:
            continue

        key = name.lower().strip()

        if key not in applications:

            applications[key] = {
                "name": name,
                "app_id": app_id,
                "type": "windows_app"
            }

    return applications


# =========================
# Save registry
# =========================

def save_registry(applications):

    DATA_FOLDER.mkdir(
        exist_ok=True
    )

    with open(
        REGISTRY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            applications,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================
# Build registry
# =========================

def build_registry():

    print(
        "Scanning applications registered with Windows..."
    )

    applications = scan_applications()

    if not applications:

        print(
            "No applications were found."
        )

        return {}

    save_registry(applications)

    print(
        f"Found {len(applications)} applications."
    )

    return applications


# =========================
# Check registry age
# =========================

def registry_needs_refresh():

    if not REGISTRY_FILE.exists():

        return True

    try:

        modified_time = REGISTRY_FILE.stat().st_mtime

        age = time.time() - modified_time

        return age >= REGISTRY_REFRESH_INTERVAL

    except OSError:

        return True


# =========================
# Load registry
# =========================

def load_registry():

    if registry_needs_refresh():

        applications = build_registry()

        if applications:

            return applications

    try:

        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return build_registry()


# =========================
# Find application
# =========================

def find_registered_application(application):

    registry = load_registry()

    query = application.lower().strip()

    # Exact match
    if query in registry:

        return registry[query]

    # Partial match
    for key, app in registry.items():

        if query in key:

            return app

    return None


# =========================
# Test
# =========================

if __name__ == "__main__":

    build_registry()