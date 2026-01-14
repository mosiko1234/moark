"""Pack TUI - Terminal UI for the pack operation.

This module provides a terminal-based UI for creating bundles for air-gapped transfer.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from urllib.parse import urlparse

from .utils import parse_gitlab_url

# Textual imports - optional dependency
try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
    from textual.widgets import Button, Checkbox, Input, Label, Log, Select, Static
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


class PackTUI(App):
    """Terminal UI for packing Git repositories."""
    
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
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(id="main_container"):
            yield Static("⛵ Moses in the Ark - Create Bundle\nFor support or questions, contact: Moshe Eliya", id="title")
            with Vertical(id="form_container"):
                yield Label("Repository URL:")
                yield Input(
                    placeholder="https://gitlab.com/group/project.git or https://kh-gitlab.kayhut.local/root/moshe-test.git",
                    id="repo_url"
                )
                
                yield Label("Username:")
                yield Input(placeholder="your-username", id="username")
                
                yield Label("Password:")
                yield Input(placeholder="your-password", password=True, id="password")
                
                yield Label("Output Directory:")
                yield Input(placeholder="./dist", value="./dist", id="output_dir")
                
                yield Label("Repository Name (override):")
                yield Input(placeholder="auto", id="repo_name")
                
                with Horizontal():
                    yield Checkbox("Include Submodules", id="submodules")
                    yield Checkbox("Download Artifacts", id="artifacts")
                
                yield Label("Artifacts Ref (branch/tag):")
                yield Input(placeholder="main", id="artifacts_ref")
                
                yield Checkbox("Disable SSL Verification", id="insecure")
            
            with Container(id="log_container"):
                yield Static("Output:", id="log_title")
                yield Log(id="log")
            
            with Horizontal(id="buttons"):
                yield Button("Pack", variant="primary", id="pack_button")
                yield Button("Clear", id="clear_button")
                yield Button("Quit", variant="error", id="quit_button")
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "Moses in the Ark - Pack"
        self.query_one("#log").write("Ready to pack repository. Fill in the form and click Pack.")
    
    @on(Button.Pressed, "#pack_button")
    def on_pack_button(self) -> None:
        """Handle pack button press."""
        self.pack_repository()
    
    @on(Button.Pressed, "#clear_button")
    def on_clear_button(self) -> None:
        """Clear the log."""
        self.query_one("#log").clear()
        self.query_one("#log").write("Log cleared.")
    
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
    
    def pack_repository(self) -> None:
        """Execute pack operation."""
        log = self.query_one("#log")
        log.clear()
        log.write("🚀 Starting pack operation...")
        
        # Build command
        cmd = ["moark-pack"]
        
        # Get form values
        repo_url = self.get_input_value("repo_url")
        username = self.get_input_value("username")
        password = self.get_input_value("password")
        output_dir = self.get_input_value("output_dir") or "./dist"
        repo_name = self.get_input_value("repo_name")
        with_submodules = self.get_checkbox_value("submodules")
        with_artifacts = self.get_checkbox_value("artifacts")
        artifacts_ref = self.get_input_value("artifacts_ref")
        insecure = self.get_checkbox_value("insecure")
        
        # Validate inputs
        if not repo_url:
            log.write("❌ Error: Please provide Repository URL")
            return
        
        # Determine if this is a GitLab private instance or public
        # If username/password provided, treat as private GitLab
        # Otherwise, check if it's a known public domain
        is_gitlab_private = False
        gitlab_base_url = None
        gitlab_repo_path = None
        
        # If credentials provided, assume it's private GitLab
        if username or password:
            try:
                gitlab_base_url, gitlab_repo_path = parse_gitlab_url(repo_url)
                is_gitlab_private = True
            except Exception as e:
                log.write(f"❌ Error parsing GitLab URL: {e}")
                return
        else:
            # Check if it's a known public domain
            try:
                parsed = urlparse(repo_url)
                public_domains = ["github.com", "gitlab.com", "bitbucket.org"]
                is_gitlab_private = not any(domain in parsed.netloc for domain in public_domains)
                
                if is_gitlab_private:
                    # Parse for private GitLab
                    gitlab_base_url, gitlab_repo_path = parse_gitlab_url(repo_url)
            except Exception:
                # If parsing fails, assume it's a public URL
                is_gitlab_private = False
        
        # If artifacts are requested, we need GitLab private with credentials
        if with_artifacts:
            if not is_gitlab_private:
                log.write("❌ Error: Artifacts require private GitLab instance")
                return
            if not username or not password:
                log.write("❌ Error: Artifacts require Username and Password")
                return
        
        # Add source parameters
        if is_gitlab_private:
            # Use GitLab private
            cmd.extend(["--source-gitlab-url", gitlab_base_url])
            cmd.extend(["--repo-path", gitlab_repo_path])
            if username:
                cmd.extend(["--source-username", username])
            if password:
                cmd.extend(["--source-password", password])
        else:
            # Use as public repository URL
            cmd.extend(["--repo-url", repo_url])
        
        # Add options
        if with_submodules:
            cmd.append("--with-submodules")
        
        if with_artifacts:
            cmd.append("--with-artifacts")
            if artifacts_ref:
                cmd.extend(["--artifacts-ref", artifacts_ref])
        
        if insecure:
            cmd.append("--insecure")
        
        if output_dir:
            cmd.extend(["--output", output_dir])
        
        if repo_name:
            cmd.extend(["--repo-name", repo_name])
        
        # Run command asynchronously
        asyncio.create_task(self._run_pack_command(cmd, log))
    
    async def _run_pack_command(self, cmd: list[str], log: Log) -> None:
        """Run pack command and stream output."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            
            bundle_file = None
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode("utf-8", errors="replace").rstrip()
                log.write(decoded)
                
                if "Created bundle:" in decoded:
                    bundle_file = decoded.split("Created bundle:")[-1].strip()
            
            await process.wait()
            
            if process.returncode == 0:
                log.write("")
                log.write("✅ Pack operation completed successfully!")
                if bundle_file:
                    log.write(f"📦 Bundle created: {bundle_file}")
            else:
                log.write("")
                log.write(f"❌ Pack operation failed with exit code {process.returncode}")
                
        except Exception as e:
            log.write(f"❌ Error: {str(e)}")


cli_app = typer.Typer(help="Pack TUI for creating bundles.")


@cli_app.command()
def serve() -> None:
    """Start the Pack TUI."""
    if not TEXTUAL_AVAILABLE:
        typer.echo(
            "Error: Textual is required for the Pack TUI.\n"
            "Install with: pip install textual",
            err=True
        )
        raise typer.Exit(1)
    
    app = PackTUI()
    app.run()


def main() -> None:
    """Entry point for the Pack TUI."""
    cli_app()


if __name__ == "__main__":
    main()
