import json
import threading
from pathlib import Path
from typing import Dict
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import requests

from src.mod_updater import get_minecraft_dir, run_updater, load_json


class ModUpdaterGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Minecraft Mod Updater")
        self.geometry("700x520")
        
        # Find config.json in the script/exe directory or current directory
        script_dir = Path(__file__).parent.parent  # Project root
        self.config_path = script_dir / "config.json"
        if not self.config_path.exists():
            self.config_path = Path("config.json")

        # Load versions from Modrinth API on startup
        self.minecraft_versions = []
        self._load_versions_in_thread()

        self._build_ui()
        self.load_config()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        top_row = ttk.Frame(frame)
        top_row.pack(fill=tk.X, pady=(0, 8))

        self.config_entry = ttk.Entry(top_row)
        self.config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_button = ttk.Button(top_row, text="Browse...", command=self.choose_config)
        browse_button.pack(side=tk.LEFT, padx=(8, 0))

        load_button = ttk.Button(top_row, text="Refresh", command=self.load_config)
        load_button.pack(side=tk.LEFT, padx=(8, 0))

        self.status_label = ttk.Label(frame, text="Loading configuration...", anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(0, 8))

        settings_frame = ttk.LabelFrame(frame, text="Config Preview")
        settings_frame.pack(fill=tk.X, pady=(0, 8))

        self.version_var = tk.StringVar()
        self.mods_dir_var = tk.StringVar()
        self.slugs_var = tk.StringVar()
        self.shader_vars: Dict[str, tk.BooleanVar] = {}
        self.resource_vars: Dict[str, tk.BooleanVar] = {}

        self._add_version_dropdown(settings_frame)
        self._add_pack_checkboxes(settings_frame, "Shader packs:", "shader")
        self._add_pack_checkboxes(settings_frame, "Resource packs:", "resource")
        self._add_mods_dir_row(settings_frame)
        self._add_preview_row(settings_frame, "Modrinth slugs:", self.slugs_var)

        run_button = ttk.Button(frame, text="Update Mods", command=self.start_update)
        run_button.pack(fill=tk.X, pady=(0, 8))

        log_frame = ttk.LabelFrame(frame, text="Output")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=16, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _add_preview_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label, width=18, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=variable, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _add_mods_dir_row(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Mods folder:", width=18, anchor=tk.W).pack(side=tk.LEFT)
        self.mods_dir_entry = ttk.Entry(row, textvariable=self.mods_dir_var)
        self.mods_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_button = ttk.Button(row, text="Browse...", command=self.choose_mods_dir)
        browse_button.pack(side=tk.LEFT, padx=(8, 0))

    def _add_pack_checkboxes(self, parent: ttk.Frame, label: str, kind: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label, width=18, anchor=tk.W).pack(side=tk.LEFT)
        frame = ttk.Frame(row)
        frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        setattr(self, f"{kind}_checkbox_frame", frame)

    def _add_version_dropdown(self, parent: ttk.Frame) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Minecraft version:", width=18, anchor=tk.W).pack(side=tk.LEFT)
        self.version_combo = ttk.Combobox(row, textvariable=self.version_var, state="readonly", width=20)
        self.version_combo.pack(side=tk.LEFT, padx=(0, 8))
        refresh_button = ttk.Button(row, text="Refresh Versions", command=self._load_versions_in_thread)
        refresh_button.pack(side=tk.LEFT)

    def _load_versions_in_thread(self) -> None:
        thread = threading.Thread(target=self._fetch_minecraft_versions, daemon=True)
        thread.start()

    def _fetch_minecraft_versions(self) -> None:
        try:
            response = requests.get("https://api.modrinth.com/v2/tag/game_version", timeout=5)
            response.raise_for_status()
            versions = response.json()
            
            # Filter for release versions only, get last 5
            releases = [v for v in versions if v.get("version_type") == "release"]
            releases.sort(key=lambda x: x.get("date"), reverse=True)
            self.minecraft_versions = [v.get("version") for v in releases[:5]]
            
            # Update the combobox on the main thread
            self.after(0, self._update_version_combobox)
        except Exception as exc:
            self.after(0, lambda: self._set_status(f"Failed to fetch versions: {exc}"))

    def _update_version_combobox(self) -> None:
        if self.minecraft_versions:
            self.version_combo["values"] = self.minecraft_versions
            if not self.version_var.get():
                self.version_combo.current(0)

    def _refresh_pack_checkboxes(
        self,
        frame: ttk.Frame,
        pack_names: list,
        selected_names: list,
        vars_dict: Dict[str, tk.BooleanVar],
    ) -> None:
        for child in frame.winfo_children():
            child.destroy()
        vars_dict.clear()

        for name in pack_names:
            var = tk.BooleanVar(value=name in selected_names if selected_names else True)
            vars_dict[name] = var
            cb = ttk.Checkbutton(frame, text=name, variable=var)
            cb.pack(side=tk.LEFT, padx=(0, 8), pady=2)

    def choose_config(self) -> None:
        path = filedialog.askopenfilename(
            title="Select config file",
            filetypes=[("JSON files", "*.json"), ("All files", "*")],
            initialfile="config.json",
        )
        if path:
            self.config_path = Path(path)
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, str(path))
            self.load_config()

    def load_config(self) -> None:
        self.config_entry.delete(0, tk.END)
        self.config_entry.insert(0, str(self.config_path))
        if not self.config_path.exists():
            self._set_status(f"Config file not found: {self.config_path}")
            self.version_var.set("")
            self.mods_dir_var.set("")
            self.slugs_var.set("")
            return

        try:
            config = load_json(self.config_path)
            version = config.get("minecraft_version", "")
            self.version_var.set(version)
            self.mods_dir_var.set(
                config.get("mods_dir") or str(get_minecraft_dir(config) / "mods")
            )
            self.slugs_var.set(", ".join(config.get("modrinth_project_slugs", [])))

            shader_packs = config.get("shader_packs", [])
            selected_shaders = config.get("selected_shader_packs", shader_packs)
            if shader_packs:
                self._refresh_pack_checkboxes(
                    self.shader_checkbox_frame,
                    shader_packs,
                    selected_shaders,
                    self.shader_vars,
                )

            resource_packs = config.get("resource_packs", [])
            selected_resources = config.get("selected_resource_packs", resource_packs)
            if resource_packs:
                self._refresh_pack_checkboxes(
                    self.resource_checkbox_frame,
                    resource_packs,
                    selected_resources,
                    self.resource_vars,
                )

            self._set_status("Configuration loaded.")
        except Exception as exc:
            self._set_status(f"Failed to load config: {exc}")

    def choose_mods_dir(self) -> None:
        directory = filedialog.askdirectory(title="Select mods folder", initialdir=self.mods_dir_var.get() or Path.cwd())
        if directory:
            self.mods_dir_var.set(directory)

    def start_update(self) -> None:
        if not self.config_path.exists():
            self._set_status("Select a valid config file first.")
            return

        # Update config with selected options before running updater
        try:
            config = load_json(self.config_path)
            config["minecraft_version"] = self.version_var.get()
            config["mods_dir"] = self.mods_dir_var.get() or str(get_minecraft_dir(config) / "mods")
            config["selected_shader_packs"] = [name for name, var in self.shader_vars.items() if var.get()]
            config["selected_resource_packs"] = [name for name, var in self.resource_vars.items() if var.get()]
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as exc:
            self._set_status(f"Failed to update config: {exc}")
            return

        self._clear_log()
        self._append_log(f"Starting update using {self.config_path}")
        self._set_status("Updating mods...")
        thread = threading.Thread(target=self._run_update_in_thread, daemon=True)
        thread.start()

    def _run_update_in_thread(self) -> None:
        def logger(message: str) -> None:
            self.after(0, self._append_log, message)

        try:
            mods_dir = Path(self.mods_dir_var.get()) if self.mods_dir_var.get().strip() else None
            result = run_updater(self.config_path, logger=logger, mods_dir_override=mods_dir)
            status = "Update completed." if result == 0 else "Update finished with errors."
        except Exception as exc:
            logger(f"Unexpected error: {exc}")
            status = "Update failed."

        self.after(0, self._set_status, status)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)


def main() -> None:
    app = ModUpdaterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
