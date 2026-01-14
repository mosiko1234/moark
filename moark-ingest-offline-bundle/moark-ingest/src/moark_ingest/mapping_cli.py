"""CLI for managing repository name mappings.

This module provides Typer commands for listing, adding, removing,
and validating repository name mappings.
"""

from __future__ import annotations

import os
from pathlib import Path

import typer

from .config_manager import ConfigManager

app = typer.Typer(
    name="airgap-mapping",
    help="Manage repository name mappings for airgap-git-relay.",
)


def get_config_dir(config_dir: Path | None) -> Path:
    """Get the configuration directory.
    
    Priority:
    1. CLI parameter
    2. MOARK_CONFIG_DIR environment variable
    3. Default: ~/.moark
    """
    if config_dir:
        return config_dir
    
    env_dir = os.environ.get("MOARK_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)
    
    return Path.home() / ".moark"


@app.command("list")
def list_mappings(
    profile: str = typer.Option(
        "default", "--profile", "-p",
        help="Profile name to list mappings for."
    ),
    config_dir: Path | None = typer.Option(
        None, "--config-dir",
        envvar="MOARK_CONFIG_DIR",
        help="Configuration directory path."
    ),
) -> None:
    """List all mappings for a profile."""
    dir_path = get_config_dir(config_dir)
    manager = ConfigManager(dir_path)
    
    mappings = manager.get_mappings(profile)
    
    if not mappings:
        typer.echo(f"No mappings found for profile '{profile}'.")
        return
    
    typer.echo(f"Mappings for profile '{profile}':")
    typer.echo("-" * 60)
    
    for external, entry in sorted(mappings.items()):
        typer.echo(f"  {external} -> {entry.internal_name}")
        if entry.notes:
            typer.echo(f"    Notes: {entry.notes}")
    
    typer.echo("-" * 60)
    typer.echo(f"Total: {len(mappings)} mapping(s)")


@app.command("add")
def add_mapping(
    external: str = typer.Argument(..., help="External repository name."),
    internal: str = typer.Argument(..., help="Internal repository name."),
    profile: str = typer.Option(
        "default", "--profile", "-p",
        help="Profile name to add mapping to."
    ),
    notes: str = typer.Option(
        "", "--notes", "-n",
        help="Optional notes for the mapping."
    ),
    config_dir: Path | None = typer.Option(
        None, "--config-dir",
        envvar="MOARK_CONFIG_DIR",
        help="Configuration directory path."
    ),
) -> None:
    """Add a new mapping."""
    dir_path = get_config_dir(config_dir)
    manager = ConfigManager(dir_path)
    
    # Check if mapping already exists
    existing = manager.get_mappings(profile)
    if external in existing:
        typer.echo(
            f"Warning: Mapping for '{external}' already exists. Overwriting.",
            err=True
        )
    
    entry = manager.add_mapping(profile, external, internal, notes)
    typer.echo(f"Added mapping: {external} -> {entry.internal_name}")
    
    if entry.notes:
        typer.echo(f"  Notes: {entry.notes}")


@app.command("remove")
def remove_mapping(
    external: str = typer.Argument(..., help="External repository name to remove."),
    profile: str = typer.Option(
        "default", "--profile", "-p",
        help="Profile name to remove mapping from."
    ),
    config_dir: Path | None = typer.Option(
        None, "--config-dir",
        envvar="MOARK_CONFIG_DIR",
        help="Configuration directory path."
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Skip confirmation prompt."
    ),
) -> None:
    """Remove a mapping."""
    dir_path = get_config_dir(config_dir)
    manager = ConfigManager(dir_path)
    
    # Check if mapping exists
    mappings = manager.get_mappings(profile)
    if external not in mappings:
        typer.echo(f"Error: No mapping found for '{external}' in profile '{profile}'.", err=True)
        raise typer.Exit(1)
    
    # Confirm removal
    if not force:
        entry = mappings[external]
        typer.echo(f"Mapping to remove: {external} -> {entry.internal_name}")
        confirm = typer.confirm("Are you sure you want to remove this mapping?")
        if not confirm:
            typer.echo("Cancelled.")
            raise typer.Exit(0)
    
    result = manager.remove_mapping(profile, external)
    
    if result:
        typer.echo(f"Removed mapping for '{external}'.")
    else:
        typer.echo(f"Error: Failed to remove mapping for '{external}'.", err=True)
        raise typer.Exit(1)


@app.command("validate")
def validate_mappings(
    profile: str = typer.Option(
        "default", "--profile", "-p",
        help="Profile name to validate."
    ),
    config_dir: Path | None = typer.Option(
        None, "--config-dir",
        envvar="MOARK_CONFIG_DIR",
        help="Configuration directory path."
    ),
) -> None:
    """Validate mapping configuration."""
    dir_path = get_config_dir(config_dir)
    manager = ConfigManager(dir_path)
    
    errors = manager.validate_mappings(profile)
    
    if not errors:
        typer.echo(f"✓ Mapping configuration for profile '{profile}' is valid.")
        raise typer.Exit(0)
    
    typer.echo(f"✗ Validation errors for profile '{profile}':", err=True)
    for error in errors:
        typer.echo(f"  - {error}", err=True)
    
    raise typer.Exit(1)


def main() -> None:
    """Entry point for the mapping CLI."""
    app()


if __name__ == "__main__":
    main()
