import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

MODRINTH_BASE = "https://api.modrinth.com/v2"
FABRIC_META = "https://meta.fabricmc.net/v2"
CACHE_FILE = "download_cache.json"


def load_json(path: Path) -> Dict:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: Dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_project_versions(slug: str) -> List[Dict]:
    response = requests.get(f"{MODRINTH_BASE}/project/{slug}/version")
    response.raise_for_status()
    return response.json()


def find_latest_version(versions: List[Dict], minecraft_version: str) -> Optional[Dict]:
    # Filter for versions compatible with both the MC version and Fabric loader
    compatible = [
        v for v in versions 
        if minecraft_version in v.get("game_versions", [])
        and "fabric" in v.get("loaders", [])
    ]
    if not compatible:
        return None
    return max(compatible, key=lambda v: v.get("date_published", ""))


def find_latest_pack_version(versions: List[Dict], minecraft_version: str) -> Optional[Dict]:
    compatible = [
        v for v in versions
        if minecraft_version in v.get("game_versions", [])
    ]
    if not compatible:
        return None
    return max(compatible, key=lambda v: v.get("date_published", ""))


def get_default_minecraft_dir() -> Path:
    if os.name == "nt":
        return Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / ".minecraft"
    return Path.home() / ".minecraft"


def get_minecraft_dir(config: Dict) -> Path:
    configured = config.get("minecraft_dir")
    if configured:
        return Path(configured).expanduser()
    return get_default_minecraft_dir()


def download_file(url: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with target_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def update_mod(
    slug: str,
    minecraft_version: str,
    mods_dir: Path,
    cache: Dict,
    logger: Callable[[str], None] = print,
) -> None:
    logger(f"Checking mod: {slug}")
    versions = fetch_project_versions(slug)
    latest = find_latest_version(versions, minecraft_version)
    if latest is None:
        logger(f"  No compatible version found for Minecraft {minecraft_version}")
        return

    version_id = latest["id"]
    previous_id = cache.get(slug)
    if version_id == previous_id:
        logger(f"  Already up to date ({latest.get('version_number')})")
        return

    files = latest.get("files", [])
    if not files:
        logger("  No download files available for this version")
        return

    file_info = files[0]
    file_url = file_info.get("url")
    filename = file_info.get("filename") or f"{slug}-{version_id}.jar"
    target_file = mods_dir / filename

    logger(f"  Downloading {filename}...")
    download_file(file_url, target_file)
    cache[slug] = version_id
    logger(f"  Updated to {latest.get('version_number')} and saved to {target_file}")


def update_pack(
    slug: str,
    minecraft_version: str,
    pack_dir: Path,
    cache: Dict,
    logger: Callable[[str], None] = print,
) -> None:
    logger(f"Checking pack: {slug}")
    versions = fetch_project_versions(slug)
    latest = find_latest_pack_version(versions, minecraft_version)
    if latest is None:
        logger(f"  No compatible pack found for Minecraft {minecraft_version}")
        return

    version_id = latest["id"]
    cache_key = f"pack:{slug}"
    previous_id = cache.get(cache_key)
    if version_id == previous_id:
        logger(f"  Already up to date ({latest.get('version_number')})")
        return

    files = latest.get("files", [])
    if not files:
        logger("  No download files available for this pack")
        return

    # Prefer a zip file if available, otherwise take the first file
    file_info = next((f for f in files if f.get("filename", "").endswith(".zip")), files[0])
    file_url = file_info.get("url")
    filename = file_info.get("filename") or f"{slug}-{version_id}.zip"
    target_file = pack_dir / filename

    logger(f"  Downloading {filename} to {pack_dir.name}...")
    download_file(file_url, target_file)
    cache[cache_key] = version_id
    logger(f"  Installed pack {slug} version {latest.get('version_number')} to {target_file}")


def install_packs(
    pack_type: str,
    pack_slugs: List[str],
    minecraft_dir: Path,
    minecraft_version: str,
    cache: Dict,
    logger: Callable[[str], None] = print,
) -> None:
    if not pack_slugs:
        return

    pack_dir = minecraft_dir / pack_type
    pack_dir.mkdir(parents=True, exist_ok=True)
    logger(f"Installing {pack_type} to {pack_dir}")

    for slug in pack_slugs:
        try:
            update_pack(slug, minecraft_version, pack_dir, cache, logger=logger)
        except requests.HTTPError as exc:
            logger(f"  HTTP error for pack {slug}: {exc}")
        except Exception as exc:
            logger(f"  Unexpected error for pack {slug}: {exc}")


def get_fabric_installer_url(logger: Callable[[str], None] = print) -> Optional[str]:
    """Fetch the download URL for the latest Fabric installer."""
    try:
        response = requests.get(f"{FABRIC_META}/versions/installer", timeout=5)
        response.raise_for_status()
        versions = response.json()
        if not versions:
            logger("No Fabric installer versions found")
            return None
        latest_installer = versions[0]  # First is latest
        url = latest_installer.get("url")
        if not url:
            logger("Could not extract Fabric installer URL")
            return None
        return url
    except Exception as exc:
        logger(f"Failed to fetch Fabric installer URL: {exc}")
        return None


def install_fabric(minecraft_version: str, logger: Callable[[str], None] = print) -> None:
    """Download and run the Fabric installer for the given Minecraft version."""
    logger("Installing Fabric...")
    installer_url = get_fabric_installer_url(logger)
    if not installer_url:
        logger("Could not install Fabric: failed to get installer URL")
        return

    temp_installer = Path("fabric-installer.jar")
    try:
        logger(f"Downloading Fabric installer...")
        download_file(installer_url, temp_installer)

        logger(f"Running Fabric installer for Minecraft {minecraft_version}...")
        # Run the installer with -mcversion and -loader arguments
        result = subprocess.run(
            ["java", "-jar", str(temp_installer), "client", "-mcversion", minecraft_version],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger("Fabric installed successfully!")
        else:
            logger(f"Fabric installer returned error code {result.returncode}")
            if result.stderr:
                logger(f"Error output: {result.stderr}")
    except FileNotFoundError:
        logger("Java is not installed or not in PATH. Please install Java to use Fabric installer.")
    except subprocess.TimeoutExpired:
        logger("Fabric installer timed out")
    except Exception as exc:
        logger(f"Error installing Fabric: {exc}")
    finally:
        if temp_installer.exists():
            temp_installer.unlink()



def run_updater(
    config_path: Path,
    logger: Callable[[str], None] = print,
    mods_dir_override: Optional[Path] = None,
) -> int:
    if not config_path.exists():
        logger(f"Config file not found: {config_path}")
        return 1

    config = load_json(config_path)
    minecraft_version = config.get("minecraft_version")
    minecraft_dir = get_minecraft_dir(config)
    mods_dir = (
        mods_dir_override
        if mods_dir_override is not None
        else Path(config.get("mods_dir"))
        if config.get("mods_dir")
        else minecraft_dir / "mods"
    )
    mod_slugs = config.get("modrinth_project_slugs", [])
    shader_slugs = config.get("selected_shader_packs", config.get("shader_packs", []))
    resource_slugs = config.get("selected_resource_packs", config.get("resource_packs", []))

    if not minecraft_version or not mod_slugs:
        logger("Config must define 'minecraft_version' and 'modrinth_project_slugs'.")
        return 1

    # Install Fabric if needed
    install_fabric(minecraft_version, logger=logger)

    cache = load_json(Path(CACHE_FILE))

    install_packs("shaderpacks", shader_slugs, minecraft_dir, minecraft_version, cache, logger=logger)
    install_packs("resourcepacks", resource_slugs, minecraft_dir, minecraft_version, cache, logger=logger)

    for slug in mod_slugs:
        try:
            update_mod(slug, minecraft_version, mods_dir, cache, logger=logger)
        except requests.HTTPError as exc:
            logger(f"  HTTP error for {slug}: {exc}")
        except Exception as exc:
            logger(f"  Unexpected error for {slug}: {exc}")

    save_json(Path(CACHE_FILE), cache)
    logger("Done.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Minecraft Mod Updater for full release versions")
    parser.add_argument("--config", default="config.json", help="Path to the config JSON file")
    args = parser.parse_args()

    config_path = Path(args.config)
    return run_updater(config_path)


if __name__ == "__main__":
    raise SystemExit(main())
