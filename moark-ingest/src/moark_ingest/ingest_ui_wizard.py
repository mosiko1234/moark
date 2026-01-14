"""Ingest TUI Wizard - Step-by-step wizard for ingesting bundles.

This wizard breaks down the ingest process into manageable steps,
making it easier to use on small terminal screens.
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
    from textual.containers import Container, Horizontal, VerticalScroll
    from textual.widgets import Button, Input, Label, Log, Select, Static, DataTable, Footer
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from .bundle_scanner import scan_bundles, find_disk_on_key_paths, BundleInfo

# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".moark"


class IngestWizard(App):
    """Step-by-step wizard for ingesting Git bundles."""
    
    CSS = """
    Screen {
        overflow-y: hidden;
    }
    
    #main_container {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1 2;
        layout: vertical;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        height: 3;
        color: $accent;
    }
    
    #step_indicator {
        text-align: center;
        height: 1;
        color: $secondary;
        margin-bottom: 1;
    }
    
    #content_area {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        height: 2;
        margin-bottom: 1;
    }
    
    Label {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }
    
    Input {
        width: 100%;
        margin-bottom: 1;
    }
    
    Select {
        width: 100%;
        margin-bottom: 1;
    }
    
    DataTable {
        height: 15;
        width: 100%;
        margin-bottom: 1;
    }
    
    #log {
        height: 12;
        border: solid $accent;
        width: 100%;
    }
    
    #nav_buttons {
        dock: bottom;
        height: 3;
        width: 100%;
        align: center middle;
    }
    
    #nav_buttons > Button {
        margin: 0 1;
        min-width: 12;
    }
    
    .success {
        color: $success;
    }
    
    .warning {
        color: $warning;
    }
    
    .error {
        color: $error;
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
        
        # Wizard state
        self.current_step = 1
        self.total_steps = 4
        
        # Data
        self.mapping_dict: dict = {}
        self.mapping_source: str = "local"
        self.mapping_file_path: str = str(self.config_dir / "mapping_dict.json")
        
        self.available_disks: list[Path] = []
        self.selected_disk: Path | None = None
        
        self.scanned_bundles: list[BundleInfo] = []
        self.selected_bundle: BundleInfo | None = None
        
        self.git_username: str = ""
        self.git_password: str = ""
        self.remote_template: str = "https://{username}:{password}@kh-gitlab.kayhut.local/root/{repo}.git"
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(id="main_container"):
            yield Static(
                "⛵ Moses in the Ark - Ingest Wizard\n"
                "For support or questions, contact: Moshe Eliya",
                id="title"
            )
            
            yield Static("", id="step_indicator")
            
            yield VerticalScroll(id="content_area")
            
            with Horizontal(id="nav_buttons"):
                yield Button("◀ Back", id="back_button", disabled=True)
                yield Button("Next ▶", variant="primary", id="next_button")
                yield Button("❌ Quit", variant="error", id="quit_button")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Moses in the Ark - Ingest Wizard"
        self.render_step()
    
    def render_step(self) -> None:
        """Render the current step."""
        # Update step indicator
        step_indicator = self.query_one("#step_indicator", Static)
        step_indicator.update(f"Step {self.current_step} of {self.total_steps}")
        
        # Clear content area
        content_area = self.query_one("#content_area", VerticalScroll)
        content_area.remove_children()
        
        # Render appropriate step
        if self.current_step == 1:
            self._render_step_1_mapping(content_area)
        elif self.current_step == 2:
            self._render_step_2_disks(content_area)
        elif self.current_step == 3:
            self._render_step_3_bundles(content_area)
        elif self.current_step == 4:
            self._render_step_4_upload(content_area)
        
        # Update navigation buttons
        back_button = self.query_one("#back_button", Button)
        next_button = self.query_one("#next_button", Button)
        
        back_button.disabled = (self.current_step == 1)
        
        if self.current_step == 4:
            next_button.label = "⬆️ Upload"
            next_button.variant = "success"
        else:
            next_button.label = "Next ▶"
            next_button.variant = "primary"
    
    def _render_step_1_mapping(self, container: VerticalScroll) -> None:
        """Render Step 1: Mapping Dictionary."""
        container.mount(Static("📋 Step 1: Load Mapping Dictionary", classes="section-title"))
        
        container.mount(Label("Mapping Source:"))
        mapping_select = Select(
            [("Local File", "local"), ("S3 Bucket", "s3")],
            value=self.mapping_source,
            id="mapping_source_select"
        )
        container.mount(mapping_select)
        
        # Local file section
        container.mount(Label("Local Mapping File Path:"))
        mapping_input = Input(
            placeholder=str(self.config_dir / "mapping_dict.json"),
            value=self.mapping_file_path,
            id="mapping_file_path"
        )
        container.mount(mapping_input)
        
        # Mount buttons container first, then add buttons
        buttons_container = Horizontal()
        container.mount(buttons_container)
        buttons_container.mount(Button("📁 Browse", id="browse_mapping_button"))
        buttons_container.mount(Button("📥 Load", variant="success", id="load_mapping_button"))
        
        # S3 section (for future)
        container.mount(Label("S3 Endpoint (if using S3):"))
        s3_input = Input(
            placeholder="https://s3.internal.company",
            id="s3_endpoint",
            disabled=(self.mapping_source == "local")
        )
        container.mount(s3_input)
        
        # Status log
        container.mount(Static("Status:", classes="section-title"))
        log = Log(id="step1_log")
        container.mount(log)
        
        # Show current status
        if self.mapping_dict:
            log.write(f"✅ Mapping dictionary loaded ({len(self.mapping_dict)} entries)")
            for ext, int_name in self.mapping_dict.items():
                log.write(f"   {ext} → {int_name}")
        else:
            log.write("⚠️  No mapping dictionary loaded yet")
            log.write("💡 Load a mapping file to continue")
    
    def _render_step_2_disks(self, container: VerticalScroll) -> None:
        """Render Step 2: Select Disk."""
        container.mount(Static("💿 Step 2: Select Disk or Folder", classes="section-title"))
        
        # Status log first (so it's visible)
        log = Log(id="step2_log")
        container.mount(log)
        
        if self.selected_disk:
            log.write(f"✅ Selected: {self.selected_disk}")
            if self.scanned_bundles:
                log.write(f"✅ Found {len(self.scanned_bundles)} bundle(s) - Ready to continue!")
        else:
            log.write("💡 Choose one option:")
            log.write("   1️⃣  Scan for USB drives (below)")
            log.write("   2️⃣  Enter path manually")
        
        # Scan button
        scan_button = Button("🔍 Scan for Disks", variant="primary", id="scan_disks_button")
        container.mount(scan_button)
        
        # Disks table
        container.mount(Static("Available Disks (Click on a row to select):", classes="section-title"))
        disks_table = DataTable(id="disks_table", zebra_stripes=True, cursor_type="row")
        disks_table.add_columns("Device", "Path", "Bundles")
        container.mount(disks_table)
        
        # Manual path section
        container.mount(Static("─" * 40))
        container.mount(Static("Or enter manual path:", classes="section-title"))
        manual_input = Input(placeholder="/Users/.../dist or /Volumes/USB", id="manual_path_input")
        container.mount(manual_input)
        scan_manual_button = Button("📁 Scan Manual Path", id="scan_manual_button")
        container.mount(scan_manual_button)
    
    def _render_step_3_bundles(self, container: VerticalScroll) -> None:
        """Render Step 3: Select Bundle."""
        container.mount(Static("📦 Step 3: Select Bundle to Ingest", classes="section-title"))
        
        # Status log first (visible at top)
        log = Log(id="step3_log")
        container.mount(log)
        
        if self.selected_bundle:
            log.write(f"✅ Selected: {self.selected_bundle.file_path.name}")
            log.write(f"   Repository: {self.selected_bundle.repo_name}")
            
            # Check mapping
            if self.selected_bundle.repo_name in self.mapping_dict:
                internal = self.mapping_dict[self.selected_bundle.repo_name]
                log.write(f"   Mapping: {self.selected_bundle.repo_name} → {internal}")
                log.write("✅ Ready! Click 'Next ▶' to configure upload")
            else:
                log.write(f"   ⚠️  No mapping found for '{self.selected_bundle.repo_name}'")
                log.write("   ❌ Cannot proceed without mapping!")
        else:
            log.write("💡 Click on a bundle in the table below to select it")
            log.write(f"   Found {len(self.scanned_bundles)} bundle(s) from: {self.selected_disk}")
        
        # Info about selected disk
        if self.selected_disk:
            container.mount(Static(f"Source: {self.selected_disk}", classes="success"))
        
        # Bundles table
        container.mount(Static("Available Bundles (Click on a row to select):", classes="section-title"))
        bundles_table = DataTable(id="bundles_table", zebra_stripes=True, cursor_type="row")
        bundles_table.add_columns("Bundle", "Repository", "Size (MB)")
        container.mount(bundles_table)
        
        # Populate if we have bundles
        if self.scanned_bundles:
            for bundle in self.scanned_bundles:
                bundles_table.add_row(
                    bundle.file_path.name,
                    bundle.repo_name,
                    f"{bundle.size / (1024 * 1024):.2f}"
                )
    
    def _render_step_4_upload(self, container: VerticalScroll) -> None:
        """Render Step 4: Upload Settings."""
        container.mount(Static("🎯 Step 4: Upload to Internal Git", classes="section-title"))
        
        # Summary
        if self.selected_bundle:
            container.mount(Static(
                f"Bundle: {self.selected_bundle.file_path.name}\n"
                f"Repository: {self.selected_bundle.repo_name}",
                classes="success"
            ))
            
            if self.selected_bundle.repo_name in self.mapping_dict:
                internal = self.mapping_dict[self.selected_bundle.repo_name]
                container.mount(Static(
                    f"Will upload to: {internal}",
                    classes="success"
                ))
        
        # Git credentials
        container.mount(Label("Git Username:"))
        username_input = Input(placeholder="root", value=self.git_username, id="git_username")
        container.mount(username_input)
        
        container.mount(Label("Git Password:"))
        password_input = Input(
            placeholder="password",
            password=True,
            value=self.git_password,
            id="git_password"
        )
        container.mount(password_input)
        
        container.mount(Label("Remote Template:"))
        template_input = Input(
            placeholder="https://{username}:{password}@git.internal/{repo}.git",
            value=self.remote_template,
            id="remote_template"
        )
        container.mount(template_input)
        
        # Upload log
        container.mount(Static("Upload Status:", classes="section-title"))
        log = Log(id="upload_log")
        container.mount(log)
        log.write("💡 Click 'Upload' button below to start")
    
    @on(Button.Pressed, "#back_button")
    def on_back(self) -> None:
        """Go to previous step."""
        if self.current_step > 1:
            self.current_step -= 1
            self.render_step()
    
    @on(Button.Pressed, "#next_button")
    def on_next(self) -> None:
        """Go to next step or upload."""
        if self.current_step == 4:
            # Upload
            self._start_upload()
        else:
            # Validate before moving forward
            if self._validate_current_step():
                self.current_step += 1
                self.render_step()
    
    def _validate_current_step(self) -> bool:
        """Validate current step before moving forward."""
        import sys
        print(f"\n[DEBUG] _validate_current_step called for step {self.current_step}", file=sys.stderr)
        
        if self.current_step == 1:
            print(f"[DEBUG] Step 1: mapping_dict = {bool(self.mapping_dict)}", file=sys.stderr)
            if not self.mapping_dict:
                log = self.query_one("#step1_log", Log)
                log.write("❌ Please load a mapping dictionary first")
                return False
            # Validation passed
            log = self.query_one("#step1_log", Log)
            log.write("✅ Validation passed! Moving to step 2...")
        
        elif self.current_step == 2:
            print(f"[DEBUG] Step 2: selected_disk = {self.selected_disk}", file=sys.stderr)
            print(f"[DEBUG] Step 2: scanned_bundles = {len(self.scanned_bundles) if self.scanned_bundles else 0}", file=sys.stderr)
            print(f"[DEBUG] Step 2: scanned_bundles list = {self.scanned_bundles}", file=sys.stderr)
            
            log = self.query_one("#step2_log", Log)
            log.write("🔍 Validating step 2...")
            log.write(f"   selected_disk = {self.selected_disk}")
            log.write(f"   scanned_bundles = {len(self.scanned_bundles) if self.scanned_bundles else 0}")
            
            # Check if disk was selected
            if not self.selected_disk:
                log.write("❌ Please select a disk or scan a path first")
                log.write("💡 Use 'Scan for Disks' or 'Scan Manual Path'")
                print(f"[DEBUG] Validation FAILED: no selected_disk", file=sys.stderr)
                return False
            # Check if bundles were found
            if not self.scanned_bundles:
                log.write("❌ No bundles found on the selected disk!")
                log.write(f"   Selected: {self.selected_disk}")
                log.write("💡 Try another disk or check if it contains .tar.gz files")
                print(f"[DEBUG] Validation FAILED: no scanned_bundles", file=sys.stderr)
                return False
            
            log.write("✅ Validation passed! Moving to step 3...")
            print(f"[DEBUG] Validation PASSED for step 2", file=sys.stderr)
        
        elif self.current_step == 3:
            log = self.query_one("#step3_log", Log)
            
            print(f"[DEBUG] Step 3: selected_bundle = {self.selected_bundle}", file=sys.stderr)
            if self.selected_bundle:
                print(f"[DEBUG] Step 3: selected_bundle.repo_name = {self.selected_bundle.repo_name}", file=sys.stderr)
            
            print(f"[DEBUG] Step 3: mapping_dict = {self.mapping_dict}", file=sys.stderr)
            print(f"[DEBUG] Step 3: mapping_dict keys = {list(self.mapping_dict.keys()) if self.mapping_dict else 'None'}", file=sys.stderr)
            
            if not self.selected_bundle:
                log.write("❌ Please select a bundle first")
                log.write("💡 Click on a bundle row in the table above")
                print(f"[DEBUG] Validation FAILED: no selected_bundle", file=sys.stderr)
                return False
            
            # DEBUG: Show what we're checking
            log.write(f"🔍 Validating...")
            log.write(f"   Bundle repo: '{self.selected_bundle.repo_name}'")
            log.write(f"   Mapping keys: {list(self.mapping_dict.keys())}")
            log.write(f"   Checking: '{self.selected_bundle.repo_name}' in {list(self.mapping_dict.keys())}")
            
            # Check mapping exists
            print(f"[DEBUG] Checking if '{self.selected_bundle.repo_name}' in mapping_dict...", file=sys.stderr)
            if self.selected_bundle.repo_name not in self.mapping_dict:
                log.write(f"❌ No mapping found for '{self.selected_bundle.repo_name}'")
                log.write(f"💡 Available mappings: {', '.join(self.mapping_dict.keys())}")
                log.write("💡 Update your mapping dictionary")
                print(f"[DEBUG] Validation FAILED: no mapping for '{self.selected_bundle.repo_name}'", file=sys.stderr)
                print(f"[DEBUG] Available keys: {list(self.mapping_dict.keys())}", file=sys.stderr)
                return False
            
            log.write("✅ Validation passed!")
            print(f"[DEBUG] Validation PASSED for step 3", file=sys.stderr)
        
        print(f"[DEBUG] Validation returning True", file=sys.stderr)
        return True
    
    @on(Button.Pressed, "#browse_mapping_button")
    def on_browse_mapping(self) -> None:
        """Browse for mapping files."""
        log = self.query_one("#step1_log", Log)
        log.write("📁 Searching for mapping files...")
        
        json_files = list(self.config_dir.glob("*.json"))
        
        if not json_files:
            log.write(f"❌ No JSON files found in {self.config_dir}")
            return
        
        log.write(f"Found {len(json_files)} file(s):")
        for i, file in enumerate(json_files, 1):
            log.write(f"  {i}. {file.name}")
        
        if json_files:
            self.query_one("#mapping_file_path", Input).value = str(json_files[0])
            log.write(f"💡 Selected: {json_files[0].name}")
    
    @on(Button.Pressed, "#load_mapping_button")
    def on_load_mapping(self) -> None:
        """Load mapping dictionary."""
        import sys
        mapping_path_str = self.query_one("#mapping_file_path", Input).value.strip()
        log = self.query_one("#step1_log", Log)
        
        log.write(f"🔍 Loading from: {mapping_path_str}")
        
        print(f"\n[DEBUG] on_load_mapping called", file=sys.stderr)
        print(f"[DEBUG] mapping_path = {mapping_path_str}", file=sys.stderr)
        
        try:
            # Expand ~ if present
            if mapping_path_str.startswith('~'):
                mapping_path = Path.home() / mapping_path_str[2:]
            else:
                mapping_path = Path(mapping_path_str)
            
            log.write(f"   Resolved to: {mapping_path}")
            
            if not mapping_path.exists():
                log.write(f"❌ File not found: {mapping_path}")
                return
            
            with open(mapping_path, 'r') as f:
                raw_content = f.read()
                log.write(f"   File size: {len(raw_content)} bytes")
                self.mapping_dict = json.loads(raw_content)
            
            print(f"[DEBUG] Loaded mapping_dict = {self.mapping_dict}", file=sys.stderr)
            print(f"[DEBUG] Type = {type(self.mapping_dict)}", file=sys.stderr)
            print(f"[DEBUG] Keys = {list(self.mapping_dict.keys())}", file=sys.stderr)
            
            self.mapping_file_path = str(mapping_path)
            
            log.write(f"✅ Loaded mapping dictionary!")
            log.write(f"📊 {len(self.mapping_dict)} mapping(s):")
            for ext, int_name in self.mapping_dict.items():
                log.write(f"   '{ext}' → '{int_name}'")
            log.write(f"   DEBUG: Keys = {list(self.mapping_dict.keys())}")
        
        except Exception as e:
            log.write(f"❌ Error: {e}")
            import traceback
            log.write(traceback.format_exc())
            print(f"[DEBUG] Error loading mapping: {e}", file=sys.stderr)
    
    @on(Button.Pressed, "#scan_disks_button")
    def on_scan_disks(self) -> None:
        """Scan for disks."""
        log = self.query_one("#step2_log", Log)
        log.write("🔍 Scanning for external disks and USB drives...")
        
        self.available_disks = find_disk_on_key_paths()
        
        disks_table = self.query_one("#disks_table", DataTable)
        disks_table.clear()
        
        if not self.available_disks:
            log.write("❌ No external disks found")
            log.write("💡 Plug in your USB drive or use manual path")
            return
        
        log.write(f"✅ Found {len(self.available_disks)} disk(s)")
        
        for disk in self.available_disks:
            bundles = scan_bundles(disk)
            disks_table.add_row(disk.name, str(disk), str(len(bundles)))
            log.write(f"   {disk.name}: {len(bundles)} bundle(s)")
        
        log.write("")
        log.write("💡 Click on a disk in the table to select it")
    
    @on(Button.Pressed, "#scan_manual_button")
    def on_scan_manual(self) -> None:
        """Scan manual path."""
        import sys
        manual_path_str = self.query_one("#manual_path_input", Input).value.strip()
        log = self.query_one("#step2_log", Log)
        
        print(f"[DEBUG] on_scan_manual called with: '{manual_path_str}'", file=sys.stderr)
        
        if not manual_path_str:
            log.write("❌ Please enter a path first")
            return
        
        manual_path = Path(manual_path_str)
        print(f"[DEBUG] Path object: {manual_path}", file=sys.stderr)
        print(f"[DEBUG] Path exists: {manual_path.exists()}", file=sys.stderr)
        
        if not manual_path.exists():
            log.write(f"❌ Path not found: {manual_path}")
            log.write(f"   Tried: {manual_path}")
            return
        
        log.write(f"🔍 Scanning: {manual_path}")
        self.selected_disk = manual_path
        
        print(f"[DEBUG] Calling scan_bundles...", file=sys.stderr)
        self.scanned_bundles = scan_bundles(manual_path)
        print(f"[DEBUG] scan_bundles returned: {len(self.scanned_bundles)} bundles", file=sys.stderr)
        print(f"[DEBUG] self.scanned_bundles = {self.scanned_bundles}", file=sys.stderr)
        
        log.write(f"✅ Scanned! Found {len(self.scanned_bundles)} bundle(s)")
        log.write(f"   selected_disk = {self.selected_disk}")
        log.write(f"   scanned_bundles count = {len(self.scanned_bundles)}")
        
        if self.scanned_bundles:
            log.write("✅ Ready! Click 'Next ▶' to continue")
            for bundle in self.scanned_bundles:
                log.write(f"   • {bundle.file_path.name} ({bundle.repo_name})")
        else:
            log.write("⚠️  No bundles (.tar.gz files) found in this path")
            log.write("💡 Make sure the path contains packed bundles")
    
    @on(DataTable.RowSelected, "#disks_table")
    def on_disk_selected(self, event: DataTable.RowSelected) -> None:
        """Handle disk selection."""
        import sys
        print(f"\n[DEBUG] on_disk_selected called!", file=sys.stderr)
        print(f"[DEBUG] cursor_row = {event.cursor_row}", file=sys.stderr)
        print(f"[DEBUG] available_disks length = {len(self.available_disks)}", file=sys.stderr)
        
        if event.cursor_row >= len(self.available_disks):
            print(f"[DEBUG] Row out of range, returning", file=sys.stderr)
            return
        
        self.selected_disk = self.available_disks[event.cursor_row]
        print(f"[DEBUG] selected_disk = {self.selected_disk}", file=sys.stderr)
        
        log = self.query_one("#step2_log", Log)
        log.clear()
        log.write(f"✅ Selected: {self.selected_disk}")
        log.write(f"🔍 Scanning for bundles...")
        
        # Scan for bundles
        self.scanned_bundles = scan_bundles(self.selected_disk)
        print(f"[DEBUG] Found {len(self.scanned_bundles)} bundles", file=sys.stderr)
        
        log.write(f"📦 Found {len(self.scanned_bundles)} bundle(s)")
        
        if self.scanned_bundles:
            log.write("✅ Ready! Click 'Next ▶' to continue")
            for bundle in self.scanned_bundles:
                log.write(f"   • {bundle.file_path.name} ({bundle.repo_name})")
        else:
            log.write("⚠️  No bundles found on this disk")
            log.write("💡 Try another disk or manual path")
    
    @on(DataTable.RowSelected, "#bundles_table")
    def on_bundle_selected(self, event: DataTable.RowSelected) -> None:
        """Handle bundle selection."""
        import sys
        print(f"\n[DEBUG] on_bundle_selected called!", file=sys.stderr)
        print(f"[DEBUG] cursor_row = {event.cursor_row}", file=sys.stderr)
        print(f"[DEBUG] scanned_bundles length = {len(self.scanned_bundles)}", file=sys.stderr)
        
        if event.cursor_row >= len(self.scanned_bundles):
            print(f"[DEBUG] Row out of range, returning", file=sys.stderr)
            return
        
        self.selected_bundle = self.scanned_bundles[event.cursor_row]
        print(f"[DEBUG] selected_bundle = {self.selected_bundle.file_path.name}", file=sys.stderr)
        print(f"[DEBUG] selected_bundle.repo_name = {self.selected_bundle.repo_name}", file=sys.stderr)
        
        log = self.query_one("#step3_log", Log)
        log.clear()
        log.write(f"✅ Selected: {self.selected_bundle.file_path.name}")
        log.write(f"   Repository: {self.selected_bundle.repo_name}")
        
        if self.selected_bundle.repo_name in self.mapping_dict:
            internal = self.mapping_dict[self.selected_bundle.repo_name]
            log.write(f"   Mapping: → {internal}")
        else:
            log.write(f"   ⚠️  No mapping for '{self.selected_bundle.repo_name}'")
    
    def _start_upload(self) -> None:
        """Start the upload process."""
        # Save credentials
        self.git_username = self.query_one("#git_username", Input).value.strip()
        self.git_password = self.query_one("#git_password", Input).value.strip()
        self.remote_template = self.query_one("#remote_template", Input).value.strip()
        
        log = self.query_one("#upload_log", Log)
        
        if not self.git_username or not self.git_password:
            log.write("❌ Please enter username and password")
            return
        
        asyncio.create_task(self._run_upload())
    
    async def _run_upload(self) -> None:
        """Run upload asynchronously."""
        log = self.query_one("#upload_log", Log)
        
        try:
            log.write("")
            log.write("⏳ Starting upload...")
            log.write(f"📦 Bundle: {self.selected_bundle.file_path.name}")
            
            # Build command
            cmd = [sys.executable, "-m", "moark_ingest.ingest", "ingest"]
            cmd.extend(["--tar", str(self.selected_bundle.file_path)])
            cmd.extend(["--remote-template", self.remote_template])
            cmd.extend(["--username", self.git_username])
            cmd.extend(["--password", self.git_password])
            
            # Add mapping
            mapping_file = Path(self.mapping_file_path)
            if mapping_file.exists():
                cmd.extend(["--mapping", str(mapping_file)])
            
            log.write("🚀 Executing moark-ingest...")
            
            # Set env for SSL
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
                log.write(line.decode("utf-8", errors="replace").rstrip())
            
            await process.wait()
            
            if process.returncode == 0:
                log.write("")
                log.write("✅ Upload completed successfully!")
            else:
                log.write("")
                log.write(f"❌ Upload failed (exit code {process.returncode})")
        
        except Exception as e:
            log.write(f"❌ Error: {e}")
    
    @on(Button.Pressed, "#quit_button")
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def main() -> None:
    """Entry point for the Ingest Wizard."""
    if not TEXTUAL_AVAILABLE:
        typer.echo(
            "Error: Textual is required for the Ingest Wizard.\n"
            "Install with: pip install textual",
            err=True
        )
        raise typer.Exit(1)
    
    app = IngestWizard()
    app.run()


if __name__ == "__main__":
    main()

