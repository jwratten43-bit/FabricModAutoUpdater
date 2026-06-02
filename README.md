# Minecraft Mod Updater

This project is a Windows tool for automatically updating Minecraft Java Edition mods, shaders, and resource packs for a chosen full release version.

## Quick Start

For end users, just double-click `setup_and_run.bat`.
It creates a local Python environment, installs dependencies, and launches the GUI.

## What it does

- Installs Fabric for the selected Minecraft version
- Downloads Fabric-compatible mods into your Minecraft `mods` folder
- Installs selected shader packs into `shaderpacks`
- Installs selected resource packs into `resourcepacks`
- Uses your Minecraft directory by default from `%APPDATA%\.minecraft`

## Final distribution files

- `dist\MinecraftModUpdater.exe` — standalone Windows executable
- `config.json` — user configuration file
- `config.sample.json` — example configuration template

## Configuration

Your config should include:

- `minecraft_version` — target Minecraft full release
- `minecraft_dir` — path to your `.minecraft` folder
- `modrinth_project_slugs` — list of mod slugs to update
- `shader_packs` — available shader pack slugs
- `resource_packs` — available resource pack slugs
- `selected_shader_packs` — shader packs to install
- `selected_resource_packs` — resource packs to install
- `mods_dir` — optional path to your mods folder; default is `minecraft_dir/mods`

Example final config:

```json
{
  "minecraft_version": "26.1.2",
  "minecraft_dir": "C:/Users/YourName/AppData/Roaming/.minecraft",
  "modrinth_project_slugs": [
    "cloth-config",
    "fabric-api",
    "freecam",
    "kirin",
    "lambdynamiclights",
    "modmenu",
    "presence-footsteps",
    "reeses-sodium-options",
    "shulkerboxtooltip",
    "sodium",
    "visuality",
    "iris"
  ],
  "shader_packs": [
    "bliss-shader",
    "complementary-unbound",
    "solas-shader"
  ],
  "resource_packs": [
    "fresh-animations",
    "better-leaves",
    "dramatic-skys",
    "faithful-64x"
  ],
  "selected_shader_packs": [
    "bliss-shader",
    "complementary-unbound",
    "solas-shader"
  ],
  "selected_resource_packs": [
    "fresh-animations",
    "better-leaves",
    "dramatic-skys",
    "faithful-64x"
  ]
}
```

## Rebuild the executable

Whenever you change the code, run:

```powershell
.\package.bat
```

The rebuilt executable will appear at `dist\MinecraftModUpdater.exe`.

## Troubleshooting

- If the GUI does not show pack checkboxes, make sure `config.json` has `shader_packs` and `resource_packs` arrays.
- If Python is not found, install it from https://www.python.org/downloads/ and enable `Add Python to PATH`.
- If Fabric installer fails, make sure Java is installed and available in PATH.
