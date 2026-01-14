"""Ingest TUI - Terminal UI for the ingest operation.

This module provides a terminal-based UI for ingesting bundles in the air-gapped environment.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Optional

import typer

# Textual imports - optional dependency
try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
    from textual.widgets import Button, Checkbox, Input, Label, Log, Select, Static, DataTable
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from .config_manager import ConfigManager
from .history_manager import HistoryManager
from .s3_settings import S3Settings
from .s3_client import S3Client, load_mapping_dict, get_internal_repo_info
from .bundle_scanner import scan_bundles, auto_scan_for_bundles, BundleInfo

# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".moark"


class IngestTUI(App):
    """Terminal UI for ingesting Git bundles."""
    
    CSS = """
    Screen {
        overflow-y: auto;
    }
    
    #main_container {
        width: 95%;
        max-width: 100;
        min-width: 30;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
        layout: vertical;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        height: 2;
        padding: 0 1;
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
    }
    
    Vertical > Label {
        width: 1fr;
        text-style: bold;
        margin-bottom: 0;
        text-align: left;
    }
    
    Vertical > Input {
        width: 1fr;
        min-width: 10;
        margin-bottom: 0;
    }
    
    Vertical > Select {
        width: 1fr;
        min-width: 10;
        margin-bottom: 0;
    }
    
    Horizontal {
        width: 1fr;
        height: auto;
    }
    
    Horizontal > Label {
        width: auto;
        min-width: 12;
        max-width: 25;
        text-style: bold;
        margin-right: 1;
    }
    
    Horizontal > Input {
        width: 1fr;
        min-width: 8;
    }
    
    Horizontal > Button {
        margin: 0 1;
    }
    
    Checkbox {
        width: auto;
        margin-right: 1;
        margin-bottom: 0;
    }
    
    #log_container {
        height: 8;
        min-height: 5;
        border: solid $secondary;
        margin-top: 1;
        overflow: hidden;
    }
    
    Log {
        height: 1fr;
        scrollbar-size-vertical: 1;
        overflow-y: auto;
    }
    
    #buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
        width: 1fr;
        dock: bottom;
    }
    
    Button {
        margin: 0 1;
        width: auto;
        min-width: 6;
        max-width: 18;
    }
    
    DataTable {
        height: 8;
        min-height: 5;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self, config_dir: Path | None = None):
        super().__init__()
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_manager = ConfigManager(self.config_dir)
        self.history_manager = HistoryManager(self.config_dir / "history.json")
        self.s3_settings = S3Settings(self.config_dir / "s3_settings.json")
        self.mapping_dict_path = self.config_dir / "mapping-dict.json"
        self.mapping_dict = {}
        self.selected_bundle: Optional[BundleInfo] = None
        self.scanned_bundles: list[BundleInfo] = []
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(id="main_container"):
            yield Static("⛵ Moses in the Ark - Load Bundle\nFor support or questions, contact: Moshe Eliya", id="title")
            
            with ScrollableContainer(id="form_container"):
                # S3 Configuration Section
                yield Static("🔧 S3 Configuration", classes="section-title")
                yield Label("S3 Endpoint URL:")
                yield Input(placeholder="https://s3.internal.company", id="s3_endpoint")
                
                yield Label("S3 Bucket Name:")
                yield Input(placeholder="airgap-mappings", id="s3_bucket")
                
                yield Label("S3 Access Key (optional):")
                yield Input(placeholder="access-key", id="s3_access_key")
                
                yield Label("S3 Secret Key (optional):")
                yield Input(placeholder="secret-key", password=True, id="s3_secret_key")
                
                with Horizontal():
                    yield Checkbox("Disable SSL Verification", id="s3_insecure")
                    yield Button("💾 Save & Download Mapping", variant="success", id="save_s3_button")
                
                # Bundle Scanner Section
                yield Static("🔍 Bundle Scanner", classes="section-title")
                yield Label("Scan Path (disk-on-key or folder):")
                with Horizontal():
                    yield Input(placeholder="/Volumes/USB or /path/to/folder", id="scan_path")
                    yield Button("🔎 Auto Scan", id="auto_scan_button")
                    yield Button("📁 Scan Path", id="scan_button")
                
                # Bundles Table
                yield Static("📦 Available Bundles", classes="section-title")
                yield DataTable(id="bundles_table", zebra_stripes=True)
                
                # Mapping Table
                yield Static("🗺️  Repository Mappings (External → Internal)", classes="section-title")
                yield DataTable(id="mapping_table", zebra_stripes=True)
                
                # Upload Settings Section
                yield Static("⬆️  Upload Settings", classes="section-title")
                yield Label("Target Git Username:")
                yield Input(placeholder="git-user", id="git_username")
                
                yield Label("Target Git Password:")
                yield Input(placeholder="password", password=True, id="git_password")
                
                with Horizontal():
                    yield Checkbox("Verify Repository", value=True, id="verify_repo")
                    yield Checkbox("Force Push", id="force_push")
                
                # History Table
                yield Static("📜 Recent Ingests", classes="section-title")
                yield DataTable(id="history_table", zebra_stripes=True)
            
            with Container(id="log_container"):
                yield Static("Output:", id="log_title")
                yield Log(id="log")
            
            with Horizontal(id="buttons"):
                yield Button("⬆️ Upload Bundle", variant="primary", id="upload_button")
                yield Button("🔄 Refresh", id="refresh_button")
                yield Button("🗑️  Clear Log", id="clear_button")
                yield Button("❌ Quit", variant="error", id="quit_button")
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Moses in the Ark - Ingest"
        log = self.query_one("#log", Log)
        
        # Load S3 settings if configured
        if self.s3_settings.is_configured():
            self.query_one("#s3_endpoint", Input).value = self.s3_settings.get_endpoint_url() or ""
            self.query_one("#s3_bucket", Input).value = self.s3_settings.get_bucket_name() or ""
            log.write("✅ S3 settings loaded from previous configuration")
        else:
            log.write("⚠️  S3 not configured. Please configure S3 to download mapping dictionary.")
        
        # Load mapping dictionary if exists
        self._load_mapping_dict()
        
        # Initialize tables
        self._init_bundles_table()
        self._init_mapping_table()
        self._init_history_table()
        
        log.write("Ready! Configure S3 and scan for bundles to begin.")
    
    def _init_bundles_table(self) -> None:
        """Initialize bundles table."""
        table = self.query_one("#bundles_table", DataTable)
        table.add_columns("File", "Repo Name", "Size (MB)", "Artifacts")
        table.cursor_type = "row"
    
    def _init_mapping_table(self) -> None:
        """Initialize mapping table."""
        table = self.query_one("#mapping_table", DataTable)
        table.add_columns("External Name", "Internal Repo", "Internal URL", "Team")
        self._refresh_mapping_table()
    
    def _init_history_table(self) -> None:
        """Initialize history table."""
        table = self.query_one("#history_table", DataTable)
        table.add_columns("Bundle", "Source → Target", "Status", "Time")
        self._refresh_history_table()
    
    def _load_mapping_dict(self) -> None:
        """Load mapping dictionary from local file."""
        log = self.query_one("#log", Log)
        
        if self.mapping_dict_path.exists():
            self.mapping_dict = load_mapping_dict(self.mapping_dict_path)
            log.write(f"✅ Loaded mapping dictionary with {len(self.mapping_dict.get('mappings', {}))} entries")
        else:
            log.write("ℹ️  No local mapping dictionary found. Download from S3 to get mappings.")
    
    def _refresh_mapping_table(self) -> None:
        """Refresh mapping table with current mappings."""
        table = self.query_one("#mapping_table", DataTable)
        table.clear()
        
        mappings = self.mapping_dict.get("mappings", {})
        for external_name, info in sorted(mappings.items()):
            table.add_row(
                external_name,
                info.get("internal_repo", "N/A"),
                info.get("internal_url", "N/A"),
                info.get("team", "N/A")
            )
    
    def _refresh_history_table(self) -> None:
        """Refresh history table with recent entries."""
        table = self.query_one("#history_table", DataTable)
        table.clear()
        
        entries = self.history_manager.get_entries(limit=10)
        for entry in entries:
            status_icon = "✅" if entry.status == "success" else "❌"
            table.add_row(
                entry.bundle_name,
                f"{entry.source_repo} → {entry.target_repo}",
                f"{status_icon} {entry.status}",
                entry.timestamp[:16]  # Show date and time only
            )
    
    def _refresh_bundles_table(self) -> None:
        """Refresh bundles table with scanned bundles."""
        table = self.query_one("#bundles_table", DataTable)
        table.clear()
        
        for bundle in self.scanned_bundles:
            table.add_row(
                bundle.file_path.name,
                bundle.repo_name,
                str(bundle.to_dict()["size_mb"]),
                "Yes" if bundle.has_artifacts else "No"
            )
    
    @on(Button.Pressed, "#save_s3_button")
    async def on_save_s3_button(self, event: Button.Pressed) -> None:
        """Save S3 settings and download mapping dictionary."""
        log = self.query_one("#log", Log)
        log.clear()
        log.write("💾 Saving S3 settings...")
        
        # Get S3 settings
        endpoint = self.get_input_value("s3_endpoint")
        bucket = self.get_input_value("s3_bucket")
        access_key = self.get_input_value("s3_access_key")
        secret_key = self.get_input_value("s3_secret_key")
        insecure = self.get_checkbox_value("s3_insecure")
        
        if not endpoint or not bucket:
            log.write("❌ Error: Please provide S3 Endpoint URL and Bucket Name")
            return
        
        # Save settings
        self.s3_settings.set_settings(
            endpoint_url=endpoint,
            bucket_name=bucket,
            access_key=access_key or None,
            secret_key=secret_key or None,
            verify_ssl=not insecure
        )
        log.write("✅ S3 settings saved")
        
        # Try to download mapping dictionary
        log.write("📥 Downloading mapping dictionary from S3...")
        try:
            s3_client = S3Client(
                endpoint_url=endpoint,
                bucket_name=bucket,
                access_key=access_key or None,
                secret_key=secret_key or None,
                verify_ssl=not insecure
            )
            
            # Test connection
            if not s3_client.test_connection():
                log.write("❌ Error: Cannot connect to S3. Please check your settings.")
                return
            
            # Download mapping dict
            mapping_dict = s3_client.download_mapping_dict()
            
            # Save locally
            s3_client.save_mapping_dict_locally(mapping_dict, self.mapping_dict_path)
            
            # Reload
            self.mapping_dict = mapping_dict
            self._refresh_mapping_table()
            
            log.write(f"✅ Downloaded and saved mapping dictionary ({len(mapping_dict.get('mappings', {}))} entries)")
            
        except Exception as e:
            log.write(f"❌ Error downloading mapping dictionary: {str(e)}")
    
    @on(Button.Pressed, "#auto_scan_button")
    def on_auto_scan_button(self, event: Button.Pressed) -> None:
        """Auto-scan for bundles on disk-on-key."""
        log = self.query_one("#log", Log)
        log.clear()
        log.write("🔎 Auto-scanning for disk-on-key and bundles...")
        
        try:
            bundles = auto_scan_for_bundles()
            
            if not bundles:
                log.write("ℹ️  No bundles found on any disk-on-key")
                return
            
            self.scanned_bundles = bundles
            self._refresh_bundles_table()
            
            log.write(f"✅ Found {len(bundles)} bundle(s)")
            for bundle in bundles[:5]:  # Show first 5
                log.write(f"   📦 {bundle.file_path.name} ({bundle.repo_name})")
            
            if len(bundles) > 5:
                log.write(f"   ... and {len(bundles) - 5} more")
                
        except Exception as e:
            log.write(f"❌ Error during auto-scan: {str(e)}")
    
    @on(Button.Pressed, "#scan_button")
    def on_scan_button(self, event: Button.Pressed) -> None:
        """Scan specific path for bundles."""
        log = self.query_one("#log", Log)
        log.clear()
        
        scan_path = self.get_input_value("scan_path")
        if not scan_path:
            log.write("❌ Error: Please provide a scan path")
            return
        
        path = Path(scan_path)
        if not path.exists():
            log.write(f"❌ Error: Path does not exist: {scan_path}")
            return
        
        log.write(f"📁 Scanning {scan_path}...")
        
        try:
            bundles = scan_bundles(path)
            
            if not bundles:
                log.write("ℹ️  No bundles found in this path")
                return
            
            self.scanned_bundles = bundles
            self._refresh_bundles_table()
            
            log.write(f"✅ Found {len(bundles)} bundle(s)")
            for bundle in bundles:
                log.write(f"   📦 {bundle.file_path.name} ({bundle.repo_name})")
                
        except Exception as e:
            log.write(f"❌ Error during scan: {str(e)}")
    
    @on(DataTable.RowSelected, "#bundles_table")
    def on_bundle_selected(self, event: DataTable.RowSelected) -> None:
        """Handle bundle selection from table."""
        log = self.query_one("#log", Log)
        
        if event.cursor_row < len(self.scanned_bundles):
            self.selected_bundle = self.scanned_bundles[event.cursor_row]
            log.write(f"✅ Selected bundle: {self.selected_bundle.file_path.name}")
            log.write(f"   Repo: {self.selected_bundle.repo_name}")
            log.write(f"   Size: {self.selected_bundle.to_dict()['size_mb']} MB")
            
            # Check if mapping exists
            internal_info = get_internal_repo_info(self.mapping_dict, self.selected_bundle.repo_name)
            if internal_info:
                log.write(f"   ✅ Mapping found: {internal_info['internal_repo']}")
                log.write(f"   Target: {internal_info['internal_url']}")
            else:
                log.write(f"   ⚠️  No mapping found for '{self.selected_bundle.repo_name}'")
                log.write("   Please check your mapping dictionary or add this mapping.")
    
    @on(Button.Pressed, "#upload_button")
    def on_upload_button(self, event: Button.Pressed) -> None:
        """Handle upload button press."""
        self.upload_bundle()
    
    @on(Button.Pressed, "#refresh_button")
    def on_refresh_button(self, event: Button.Pressed) -> None:
        """Refresh all tables."""
        log = self.query_one("#log", Log)
        log.clear()
        log.write("🔄 Refreshing...")
        
        self._load_mapping_dict()
        self._refresh_mapping_table()
        self._refresh_history_table()
        self._refresh_bundles_table()
        
        log.write("✅ Refreshed all data")
    
    @on(Button.Pressed, "#clear_button")
    def on_clear_button(self, event: Button.Pressed) -> None:
        """Clear the log."""
        self.query_one("#log", Log).clear()
        self.query_one("#log", Log).write("Log cleared.")
    
    @on(Button.Pressed, "#quit_button")
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def get_input_value(self, widget_id: str) -> str:
        """Get value from input widget."""
        widget = self.query_one(f"#{widget_id}", Input)
        return widget.value.strip()
    
    def get_checkbox_value(self, widget_id: str) -> bool:
        """Get value from checkbox widget."""
        widget = self.query_one(f"#{widget_id}", Checkbox)
        return widget.value
    
    def upload_bundle(self) -> None:
        """Execute upload operation."""
        log = self.query_one("#log", Log)
        log.clear()
        log.write("🚀 Starting upload operation...")
        
        # Check if bundle is selected
        if not self.selected_bundle:
            log.write("❌ Error: Please select a bundle from the table")
            return
        
        bundle_path = self.selected_bundle.file_path
        repo_name = self.selected_bundle.repo_name
        
        # Check if mapping exists
        internal_info = get_internal_repo_info(self.mapping_dict, repo_name)
        if not internal_info:
            log.write(f"❌ Error: No mapping found for repository '{repo_name}'")
            log.write("   Please download the latest mapping dictionary from S3")
            return
        
        internal_url = internal_info["internal_url"]
        log.write(f"📦 Bundle: {bundle_path.name}")
        log.write(f"🗺️  Mapping: {repo_name} → {internal_info['internal_repo']}")
        log.write(f"🎯 Target: {internal_url}")
        
        # Get credentials
        username = self.get_input_value("git_username")
        password = self.get_input_value("git_password")
        
        if not username or not password:
            log.write("❌ Error: Please provide Git username and password")
            return
        
        # Build authenticated URL
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(internal_url)
        auth_netloc = f"{username}:{password}@{parsed.netloc}"
        auth_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, "", "", ""))
        
        # Get options
        force_push = self.get_checkbox_value("force_push")
        
        # Build command
        cmd = [sys.executable, "-m", "moark_ingest.ingest", "ingest"]
        cmd.extend(["--tar", str(bundle_path)])
        cmd.extend(["--remote-template", auth_url])
        
        if force_push:
            cmd.append("--force")
        
        # Run command asynchronously
        asyncio.create_task(self._run_upload_command(cmd, log, bundle_path, repo_name, internal_info))
    
    async def _run_upload_command(
        self,
        cmd: list[str],
        log: Log,
        bundle_path: Path,
        repo_name: str,
        internal_info: dict
    ) -> None:
        """Run upload command and stream output."""
        try:
            log.write("")
            log.write("⏳ Extracting and uploading bundle...")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
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
                log.write("✅ Upload operation completed successfully!")
                log.write(f"📦 Bundle: {bundle_path.name}")
                log.write(f"🎯 Uploaded to: {internal_info['internal_repo']}")
                
                # Refresh history
                self._refresh_history_table()
            else:
                log.write("")
                log.write(f"❌ Upload operation failed with exit code {process.returncode}")
                
        except Exception as e:
            log.write(f"❌ Error: {str(e)}")


cli_app = typer.Typer(help="Ingest TUI for uploading and ingesting bundles.")


@cli_app.command()
def serve(
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        envvar="MOARK_CONFIG_DIR",
        help="Configuration directory"
    ),
) -> None:
    """Start the Ingest TUI."""
    if not TEXTUAL_AVAILABLE:
        typer.echo(
            "Error: Textual is required for the Ingest TUI.\n"
            "Install with: pip install textual",
            err=True
        )
        raise typer.Exit(1)
    
    app = IngestTUI(config_dir)
    app.run()


def main() -> None:
    """Entry point for the Ingest TUI."""
    cli_app()


if __name__ == "__main__":
    main()
