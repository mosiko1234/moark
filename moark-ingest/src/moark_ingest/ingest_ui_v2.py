"""Ingest TUI V2 - Simplified Terminal UI for ingesting bundles.

This is a simplified version focused on ease of use.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer

# Textual imports - optional dependency
try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, ScrollableContainer
    from textual.widgets import Button, Input, Label, Log, Select, Static, DataTable
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from .bundle_scanner import scan_bundles, find_disk_on_key_paths, BundleInfo

# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".moark"


class SimplifiedIngestTUI(App):
    """Simplified Terminal UI for ingesting Git bundles."""
    
    CSS = """
    Screen {
        overflow-y: auto;
    }
    
    #main_container {
        width: 95%;
        max-width: 120;
        min-width: 40;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
        layout: vertical;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        height: 3;
        padding: 0 1;
        color: $accent;
    }
    
    #form_container {
        padding: 0 1;
        height: auto;
        overflow-y: auto;
        scrollbar-size-vertical: 1;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 0;
        height: 2;
    }
    
    Label {
        width: 1fr;
        text-style: bold;
        margin-bottom: 0;
        text-align: left;
    }
    
    Input {
        width: 1fr;
        min-width: 20;
        margin-bottom: 1;
    }
    
    Select {
        width: 1fr;
        min-width: 20;
        margin-bottom: 1;
    }
    
    Horizontal {
        width: 1fr;
        height: auto;
        margin-bottom: 1;
    }
    
    Horizontal > Button {
        min-width: 15;
        margin-right: 1;
    }
    
    DataTable {
        height: 8;
        min-height: 4;
        width: 1fr;
        margin-bottom: 1;
    }
    
    #disks_table {
        height: 6;
    }
    
    #bundles_table {
        height: 8;
    }
    
    #log_container {
        width: 1fr;
        height: 8;
        border: solid $accent;
        padding: 0 1;
    }
    
    #log_title {
        text-style: bold;
        color: $accent;
    }
    
    #log {
        height: 6;
        border: none;
    }
    
    #buttons {
        dock: bottom;
        height: 3;
        width: 1fr;
        align: center middle;
    }
    
    #buttons > Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config_dir = DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.mapping_dict: dict = {}
        self.mapping_source: str = "local"  # "local" or "s3"
        self.selected_bundle: BundleInfo | None = None
        self.scanned_bundles: list[BundleInfo] = []
        self.available_disks: list[Path] = []
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(id="main_container"):
            yield Static(
                "⛵ Moses in the Ark - Load Bundle\n"
                "For support or questions, contact: Moshe Eliya",
                id="title"
            )
            
            with ScrollableContainer(id="form_container"):
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 1. Mapping Dictionary Source
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                yield Static("📋 Step 1: Choose Mapping Dictionary Source", classes="section-title")
                
                yield Label("Mapping Source:")
                mapping_options = [
                    ("Local File", "local"),
                    ("S3 Bucket", "s3")
                ]
                yield Select(mapping_options, value="local", id="mapping_source_select")
                
                # Local File Option
                yield Label("Local Mapping File Path:")
                with Horizontal():
                    yield Input(
                        placeholder=str(self.config_dir / "mapping_dict.json"),
                        value=str(self.config_dir / "mapping_dict.json"),
                        id="mapping_file_path"
                    )
                    yield Button("📁 Browse...", id="browse_mapping_button")
                    yield Button("📥 Load", variant="success", id="load_mapping_button")
                
                # S3 Option (shown when S3 is selected)
                yield Label("S3 Endpoint URL:")
                yield Input(placeholder="https://s3.internal.company", id="s3_endpoint", disabled=True)
                
                yield Label("S3 Bucket Name:")
                yield Input(placeholder="airgap-mappings", id="s3_bucket", disabled=True)
                
                with Horizontal():
                    yield Button("📥 Download from S3", id="download_s3_button", disabled=True)
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 2. Disk Selection (Auto Scan)
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                yield Static("💿 Step 2: Select Disk or Folder", classes="section-title")
                
                with Horizontal():
                    yield Button("🔍 Scan for Disks", variant="primary", id="scan_disks_button")
                    yield Button("📁 Manual Path...", id="manual_path_button")
                
                yield Static("Available Disks / Folders:")
                disks_table = DataTable(id="disks_table", zebra_stripes=True)
                disks_table.add_columns("Device", "Path", "Bundles Found")
                yield disks_table
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 3. Bundle Selection
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                yield Static("📦 Step 3: Select Bundle to Ingest", classes="section-title")
                
                yield Static("Found Bundles:")
                bundles_table = DataTable(id="bundles_table", zebra_stripes=True)
                bundles_table.add_columns("Bundle", "Repo", "Size (MB)", "Location")
                yield bundles_table
                
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 4. Target Repository Settings
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                yield Static("🎯 Step 4: Target Repository Settings", classes="section-title")
                
                yield Label("Selected Bundle:")
                yield Input(placeholder="No bundle selected", id="selected_bundle", disabled=True)
                
                yield Label("Internal Repository (from mapping):")
                yield Input(placeholder="Will be determined from mapping", id="internal_repo", disabled=True)
                
                yield Label("Git Username:")
                yield Input(placeholder="root", id="git_username")
                
                yield Label("Git Password:")
                yield Input(placeholder="password", password=True, id="git_password")
                
                yield Label("Remote Template:")
                yield Input(
                    placeholder="https://{username}:{password}@git.internal/root/{repo}.git",
                    value="https://{username}:{password}@kh-gitlab.kayhut.local/root/{repo}.git",
                    id="remote_template"
                )
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Log Output
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            with Container(id="log_container"):
                yield Static("Output:", id="log_title")
                yield Log(id="log")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Action Buttons
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            with Horizontal(id="buttons"):
                yield Button("⬆️ Upload Bundle", variant="primary", id="upload_button")
                yield Button("🗑️ Clear Log", id="clear_button")
                yield Button("❌ Quit", variant="error", id="quit_button")
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Moses in the Ark - Ingest"
        log = self.query_one("#log", Log)
        log.write("✅ Ready to ingest bundles.")
        log.write("")
        log.write("📋 Step 1: Load mapping dictionary (local file or S3)")
        log.write("💿 Step 2: Scan for disks with bundles")
        log.write("📦 Step 3: Select a bundle")
        log.write("🎯 Step 4: Enter credentials and upload")
        
        # Try to load default mapping file if exists
        default_mapping = self.config_dir / "mapping_dict.json"
        if default_mapping.exists():
            self._load_local_mapping(default_mapping)
    
    @on(Select.Changed, "#mapping_source_select")
    def on_mapping_source_changed(self, event: Select.Changed) -> None:
        """Handle mapping source selection change."""
        self.mapping_source = str(event.value)
        log = self.query_one("#log", Log)
        
        if self.mapping_source == "local":
            log.write("📁 Switched to Local File mapping source")
            # Enable local file inputs
            self.query_one("#mapping_file_path", Input).disabled = False
            self.query_one("#browse_mapping_button", Button).disabled = False
            self.query_one("#load_mapping_button", Button).disabled = False
            # Disable S3 inputs
            self.query_one("#s3_endpoint", Input).disabled = True
            self.query_one("#s3_bucket", Input).disabled = True
            self.query_one("#download_s3_button", Button).disabled = True
        else:
            log.write("☁️  Switched to S3 mapping source")
            # Disable local file inputs
            self.query_one("#mapping_file_path", Input).disabled = True
            self.query_one("#browse_mapping_button", Button).disabled = True
            self.query_one("#load_mapping_button", Button).disabled = True
            # Enable S3 inputs
            self.query_one("#s3_endpoint", Input).disabled = False
            self.query_one("#s3_bucket", Input).disabled = False
            self.query_one("#download_s3_button", Button).disabled = False
    
    @on(Button.Pressed, "#browse_mapping_button")
    def on_browse_mapping(self) -> None:
        """Browse for mapping file."""
        log = self.query_one("#log", Log)
        log.write("📁 Listing available mapping files in config directory...")
        
        config_dir = self.config_dir
        json_files = list(config_dir.glob("*.json"))
        
        if not json_files:
            log.write(f"❌ No JSON files found in {config_dir}")
            log.write("💡 Tip: Place your mapping dictionary at ~/.moark/mapping_dict.json")
            return
        
        log.write(f"Found {len(json_files)} JSON file(s):")
        for i, file in enumerate(json_files, 1):
            log.write(f"  {i}. {file.name}")
            # Auto-load the first one for convenience
            if i == 1:
                self.query_one("#mapping_file_path", Input).value = str(file)
                log.write(f"💡 Tip: Click 'Load' to load {file.name}")
    
    @on(Button.Pressed, "#load_mapping_button")
    def on_load_mapping(self) -> None:
        """Load mapping from local file."""
        mapping_path = Path(self.query_one("#mapping_file_path", Input).value)
        self._load_local_mapping(mapping_path)
    
    def _load_local_mapping(self, mapping_path: Path) -> None:
        """Load mapping dictionary from local file."""
        log = self.query_one("#log", Log)
        
        try:
            if not mapping_path.exists():
                log.write(f"❌ File not found: {mapping_path}")
                return
            
            with open(mapping_path, 'r') as f:
                self.mapping_dict = json.load(f)
            
            log.write(f"✅ Loaded mapping dictionary from {mapping_path.name}")
            log.write(f"📊 Found {len(self.mapping_dict)} mapping(s):")
            for external, internal in self.mapping_dict.items():
                log.write(f"   {external} → {internal}")
        
        except json.JSONDecodeError as e:
            log.write(f"❌ Invalid JSON in mapping file: {e}")
        except Exception as e:
            log.write(f"❌ Error loading mapping: {e}")
    
    @on(Button.Pressed, "#scan_disks_button")
    def on_scan_disks(self) -> None:
        """Scan for available disks."""
        log = self.query_one("#log", Log)
        log.write("🔍 Scanning for disk-on-keys and external drives...")
        
        self.available_disks = find_disk_on_key_paths()
        
        disks_table = self.query_one("#disks_table", DataTable)
        disks_table.clear()
        
        if not self.available_disks:
            log.write("❌ No external disks found")
            log.write("💡 Tip: Plug in your disk-on-key or use 'Manual Path' button")
            return
        
        log.write(f"✅ Found {len(self.available_disks)} disk(s)")
        
        # Scan each disk for bundles
        for disk in self.available_disks:
            bundles = scan_bundles(disk)
            bundle_count = len(bundles)
            
            disks_table.add_row(
                disk.name,
                str(disk),
                str(bundle_count)
            )
            
            log.write(f"   💿 {disk.name}: {bundle_count} bundle(s) found at {disk}")
            
            # Add bundles to the main bundles table
            if bundles:
                self._add_bundles_to_table(bundles)
    
    @on(Button.Pressed, "#manual_path_button")
    def on_manual_path(self) -> None:
        """Allow manual path entry."""
        log = self.query_one("#log", Log)
        log.write("📁 Enter manual path in the scan path field")
        log.write("💡 Example: /Volumes/USB or /path/to/folder")
        log.write("💡 Then scan for bundles using the table above")
    
    @on(DataTable.RowSelected, "#disks_table")
    def on_disk_selected(self, event: DataTable.RowSelected) -> None:
        """Handle disk selection - scan for bundles."""
        if event.cursor_row >= len(self.available_disks):
            return
        
        selected_disk = self.available_disks[event.cursor_row]
        log = self.query_one("#log", Log)
        log.write(f"📂 Selected disk: {selected_disk}")
        log.write(f"🔍 Scanning for bundles in {selected_disk}...")
        
        bundles = scan_bundles(selected_disk)
        
        if not bundles:
            log.write("❌ No bundles found on this disk")
            return
        
        log.write(f"✅ Found {len(bundles)} bundle(s)")
        self._add_bundles_to_table(bundles)
    
    def _add_bundles_to_table(self, bundles: list[BundleInfo]) -> None:
        """Add bundles to the bundles table."""
        bundles_table = self.query_one("#bundles_table", DataTable)
        bundles_table.clear()
        
        self.scanned_bundles = bundles
        
        for bundle in bundles:
            bundles_table.add_row(
                bundle.file_path.name,
                bundle.repo_name,
                f"{bundle.size / (1024 * 1024):.2f}",
                str(bundle.file_path.parent)
            )
    
    @on(DataTable.RowSelected, "#bundles_table")
    def on_bundle_selected(self, event: DataTable.RowSelected) -> None:
        """Handle bundle selection."""
        if event.cursor_row >= len(self.scanned_bundles):
            return
        
        self.selected_bundle = self.scanned_bundles[event.cursor_row]
        log = self.query_one("#log", Log)
        
        log.write(f"📦 Selected bundle: {self.selected_bundle.file_path.name}")
        log.write(f"   Repository: {self.selected_bundle.repo_name}")
        
        # Update UI
        self.query_one("#selected_bundle", Input).value = self.selected_bundle.file_path.name
        
        # Check mapping
        if self.selected_bundle.repo_name in self.mapping_dict:
            internal_repo = self.mapping_dict[self.selected_bundle.repo_name]
            self.query_one("#internal_repo", Input).value = internal_repo
            log.write(f"✅ Mapping found: {self.selected_bundle.repo_name} → {internal_repo}")
        else:
            self.query_one("#internal_repo", Input).value = "⚠️ NOT FOUND IN MAPPING"
            log.write(f"⚠️  Warning: No mapping found for '{self.selected_bundle.repo_name}'")
            log.write("   The bundle will be uploaded with the same name.")
    
    @on(Button.Pressed, "#upload_button")
    def on_upload(self) -> None:
        """Handle upload button press."""
        log = self.query_one("#log", Log)
        
        if not self.selected_bundle:
            log.write("❌ Error: Please select a bundle first")
            return
        
        if not self.mapping_dict:
            log.write("⚠️  Warning: No mapping dictionary loaded")
            log.write("   Proceeding anyway...")
        
        username = self.query_one("#git_username", Input).value.strip()
        password = self.query_one("#git_password", Input).value.strip()
        remote_template = self.query_one("#remote_template", Input).value.strip()
        
        if not username or not password:
            log.write("❌ Error: Please enter Git username and password")
            return
        
        if not remote_template:
            log.write("❌ Error: Please enter remote template")
            return
        
        # Run ingest command
        asyncio.create_task(self._run_ingest(
            self.selected_bundle,
            username,
            password,
            remote_template
        ))
    
    async def _run_ingest(
        self,
        bundle: BundleInfo,
        username: str,
        password: str,
        remote_template: str
    ) -> None:
        """Run ingest command asynchronously."""
        log = self.query_one("#log", Log)
        
        try:
            log.write("")
            log.write("⏳ Starting ingest operation...")
            log.write(f"📦 Bundle: {bundle.file_path.name}")
            log.write(f"🔐 Username: {username}")
            
            # Build command
            cmd = [sys.executable, "-m", "moark_ingest.ingest", "ingest"]
            cmd.extend(["--tar", str(bundle.file_path)])
            cmd.extend(["--remote-template", remote_template])
            cmd.extend(["--username", username])
            cmd.extend(["--password", password])
            
            # Add mapping if available
            mapping_file = self.config_dir / "mapping_dict.json"
            if mapping_file.exists():
                cmd.extend(["--mapping", str(mapping_file)])
            
            log.write(f"🚀 Running: moark-ingest ingest...")
            
            # Set environment variable for SSL
            import os
            env = os.environ.copy()
            env["GIT_SSL_NO_VERIFY"] = "true"
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode("utf-8", errors="replace").rstrip()
                log.write(decoded)
            
            await process.wait()
            
            if process.returncode == 0:
                log.write("")
                log.write("✅ Ingest operation completed successfully!")
            else:
                log.write("")
                log.write(f"❌ Ingest operation failed with exit code {process.returncode}")
        
        except Exception as e:
            log.write(f"❌ Error: {str(e)}")
    
    @on(Button.Pressed, "#clear_button")
    def on_clear(self) -> None:
        """Clear the log."""
        self.query_one("#log", Log).clear()
        self.query_one("#log", Log).write("Log cleared.")
    
    @on(Button.Pressed, "#quit_button")
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main() -> None:
    """Entry point for the simplified Ingest TUI."""
    if not TEXTUAL_AVAILABLE:
        typer.echo(
            "Error: Textual is required for the Ingest TUI.\n"
            "Install with: pip install textual",
            err=True
        )
        raise typer.Exit(1)
    
    app = SimplifiedIngestTUI()
    app.run()


if __name__ == "__main__":
    main()


