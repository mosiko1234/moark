import json
import os
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Optional

import typer

from .config_manager import ConfigManager
from .history_manager import HistoryManager, HistoryEntry
from .utils import (
    derive_repo_name,
    ensure_dir,
    info,
    load_mapping,
    resolve_remote_url,
    run_git,
    success,
    warn,
)

app = typer.Typer(help="Ingest packed tar.gz into internal Git (mirror push).")


def extract_bundle(tar_path: Path, workdir: Path) -> Path:
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=workdir)
    entries = list(workdir.iterdir())
    if len(entries) != 1:
        raise ValueError("bundle must contain single root directory")
    return entries[0]


def has_artifacts(bundle_root: Path) -> bool:
    """
    Check if a bundle contains an artifacts directory.
    
    Args:
        bundle_root: Path to the extracted bundle root directory
        
    Returns:
        True if artifacts/ directory exists within the bundle root, False otherwise
    """
    artifacts_dir = bundle_root / "artifacts"
    return artifacts_dir.exists() and artifacts_dir.is_dir()


def extract_artifacts(bundle_root: Path, output_dir: Path) -> tuple[int, int]:
    """
    Extract artifacts from bundle to output directory.
    
    Copies all files from the bundle's artifacts/ directory to the output directory,
    preserving the original directory structure.
    
    Args:
        bundle_root: Path to the extracted bundle root directory
        output_dir: Path to the destination directory for artifacts
        
    Returns:
        Tuple of (file_count, total_bytes) extracted
    """
    import shutil
    
    artifacts_dir = bundle_root / "artifacts"
    file_count = 0
    total_bytes = 0
    
    if not artifacts_dir.exists():
        return file_count, total_bytes
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Walk through all files in artifacts directory
    for source_file in artifacts_dir.rglob("*"):
        if source_file.is_file():
            # Calculate relative path from artifacts/ directory
            relative_path = source_file.relative_to(artifacts_dir)
            dest_file = output_dir / relative_path
            
            # Create parent directories if needed
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_file, dest_file)
            
            file_count += 1
            total_bytes += source_file.stat().st_size
    
    return file_count, total_bytes


def push_mirror(repo_dir: Path, remote_url: str) -> None:
    # Ensure clean remote name
    try:
        run_git(["--git-dir", str(repo_dir), "remote", "remove", "target"])
    except RuntimeError:
        pass
    run_git(["--git-dir", str(repo_dir), "remote", "add", "target", remote_url])
    
    # Try to push with mirror
    try:
        run_git(["--git-dir", str(repo_dir), "push", "--mirror", "--force", "target"])
    except RuntimeError as e:
        error_msg = str(e)
        if "protected branch" in error_msg or "pre-receive hook declined" in error_msg:
            # Clean URL for display (remove credentials)
            import re
            clean_url = re.sub(r'//[^@]+@', '//', remote_url)
            
            # Provide helpful error message
            print("\n" + "="*70)
            print("❌ PUSH FAILED: Protected Branch")
            print("="*70)
            print("\nThe target repository has protected branches that prevent force push.")
            print("\nTo fix this, go to GitLab:")
            print(f"  1. Open: {clean_url}")
            print("  2. Go to: Settings → Repository → Protected branches")
            print("  3. Either:")
            print("     - Unprotect the 'main' branch, OR")
            print("     - Enable 'Allowed to force push' for Maintainers")
            print("\nThen try the upload again.")
            print("="*70 + "\n")
            raise RuntimeError(
                "Cannot push to protected branch. "
                "Please unprotect the branch or enable force push in GitLab settings."
            ) from e
        else:
            raise


def _get_default_config_dir() -> Path:
    """Get the default configuration directory."""
    return Path.home() / ".moark"


def _resolve_mapping(
    external_name: str,
    mapping_file: Path | None,
    config_manager: ConfigManager | None,
    profile: str,
) -> str:
    """Resolve external repo name to internal name using mapping.
    
    Priority:
    1. ConfigManager with profile (if provided)
    2. Legacy mapping file (if provided)
    3. Return original name unchanged
    """
    if config_manager:
        return config_manager.resolve_mapping(profile, external_name)
    if mapping_file:
        mapping = load_mapping(mapping_file)
        return mapping.get(external_name, external_name)
    return external_name


def ingest_tar(
    tar_path: Path,
    remote_template: str,
    username: Optional[str],
    password: Optional[str],
    mapping_file: Path | None,
    artifacts_output_dir: Path | None = None,
    config_manager: ConfigManager | None = None,
    profile: str = "default",
    history_manager: HistoryManager | None = None,
) -> dict:
    """Ingest a tar bundle into the internal Git repository.
    
    Args:
        tar_path: Path to the tar.gz bundle.
        remote_template: URL template for the remote repository.
        username: Git username for authentication.
        password: Git password/token for authentication.
        mapping_file: Legacy mapping file path (optional).
        artifacts_output_dir: Directory to extract artifacts to (optional).
        config_manager: ConfigManager instance for profile-based mappings (optional).
        profile: Profile name to use for mapping resolution.
        history_manager: HistoryManager instance for recording history (optional).
        
    Returns:
        Dictionary with ingestion details (source_repo, target_repo, artifacts_count).
    """
    result = {
        "source_repo": "",
        "target_repo": "",
        "artifacts_count": 0,
    }
    
    start_time = time.time()
    error_message = None
    status = "success"
    
    try:
        with tempfile.TemporaryDirectory(prefix="airgap-ingest-") as tmp:
            workdir = Path(tmp)
            root = extract_bundle(tar_path, workdir)
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())

            source_repo_name = manifest.get("repo_name") or derive_repo_name(manifest["repo_url"])
            target_repo = _resolve_mapping(source_repo_name, mapping_file, config_manager, profile)
            
            result["source_repo"] = source_repo_name
            result["target_repo"] = target_repo

            remote_url = resolve_remote_url(remote_template, target_repo, username, password)

            main_repo = root / f"{source_repo_name}.git"
            info(f"Pushing main mirror to {target_repo}")
            push_mirror(main_repo, remote_url)

            if manifest.get("with_submodules") and manifest.get("submodules"):
                sub_root = root / "submodules"
                for sub in manifest["submodules"]:
                    sub_name = derive_repo_name(sub["url"])
                    target_sub = _resolve_mapping(sub_name, mapping_file, config_manager, profile)
                    sub_repo_dir = sub_root / Path(sub["mirror"]).name
                    sub_remote = resolve_remote_url(remote_template, target_sub, username, password)
                    info(f"Pushing submodule {sub_name} -> {target_sub}")
                    push_mirror(sub_repo_dir, sub_remote)

            # Handle artifact extraction
            if has_artifacts(root):
                if artifacts_output_dir:
                    file_count, total_bytes = extract_artifacts(root, artifacts_output_dir)
                    result["artifacts_count"] = file_count
                    info(f"Extracted {file_count} artifact(s), total size: {total_bytes} bytes")
                else:
                    info("Bundle contains artifacts but --artifacts-output-dir not specified, skipping extraction")

            success(f"Ingested {tar_path.name}")
    except Exception as e:
        status = "failed"
        error_message = str(e)
        raise
    finally:
        # Record history if history manager is provided
        if history_manager:
            duration = time.time() - start_time
            entry = HistoryEntry(
                bundle_name=tar_path.name,
                source_repo=result["source_repo"],
                target_repo=result["target_repo"],
                profile=profile,
                status=status,
                error_message=error_message,
                artifacts_count=result["artifacts_count"],
                duration_seconds=round(duration, 2),
            )
            history_manager.add_entry(entry)
    
    return result


@app.command("ingest")
def ingest_command(
    tar: Path = typer.Option(..., "--tar", exists=True, readable=True, help="tar.gz created by airgap-pack"),
    remote_template: str = typer.Option(
        ...,
        "--remote-template",
        envvar="MOARK_REMOTE_TEMPLATE",
        help="Template like https://{username}:{password}@git.internal/{repo}.git",
    ),
    username: Optional[str] = typer.Option(None, "--username", envvar="MOARK_REMOTE_USERNAME"),
    password: Optional[str] = typer.Option(None, "--password", envvar="MOARK_REMOTE_PASSWORD"),
    mapping: Optional[Path] = typer.Option(None, "--mapping", exists=True, readable=True, help="JSON mapping file (legacy)"),
    mapping_config: Optional[Path] = typer.Option(
        None, 
        "--mapping-config", 
        envvar="MOARK_CONFIG_DIR",
        help="Path to configuration directory for profile-based mappings"
    ),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name for mapping resolution"),
    artifacts_output_dir: Optional[Path] = typer.Option(
        None, "--artifacts-output-dir", help="Directory to extract artifacts to"
    ),
    record_history: bool = typer.Option(True, "--record-history/--no-record-history", help="Record ingestion in history"),
) -> None:
    """Ingest a packed tar.gz bundle into internal Git repository."""
    # Determine config manager
    config_manager = None
    config_dir = None
    if mapping_config:
        config_dir = mapping_config
        config_manager = ConfigManager(mapping_config)
    elif os.environ.get("MOARK_CONFIG_DIR"):
        config_dir = Path(os.environ["MOARK_CONFIG_DIR"])
        config_manager = ConfigManager(config_dir)
    
    # Set up history manager if recording is enabled
    history_manager = None
    if record_history:
        history_dir = config_dir if config_dir else _get_default_config_dir()
        history_file = history_dir / "history.json"
        history_manager = HistoryManager(history_file)
    
    ingest_tar(
        tar, 
        remote_template, 
        username, 
        password, 
        mapping, 
        artifacts_output_dir,
        config_manager=config_manager,
        profile=profile,
        history_manager=history_manager,
    )


@app.command("ingest-dir")
def ingest_dir_command(
    drop_dir: Path = typer.Option(..., "--drop-dir", file_okay=False, exists=True, help="Folder with *.tar.gz bundles"),
    remote_template: str = typer.Option(
        ...,
        "--remote-template",
        envvar="MOARK_REMOTE_TEMPLATE",
        help="Template like https://{username}:{password}@git.internal/{repo}.git",
    ),
    username: Optional[str] = typer.Option(None, "--username", envvar="MOARK_REMOTE_USERNAME"),
    password: Optional[str] = typer.Option(None, "--password", envvar="MOARK_REMOTE_PASSWORD"),
    mapping: Optional[Path] = typer.Option(None, "--mapping", exists=True, readable=True, help="JSON mapping file (legacy)"),
    mapping_config: Optional[Path] = typer.Option(
        None, 
        "--mapping-config", 
        envvar="MOARK_CONFIG_DIR",
        help="Path to configuration directory for profile-based mappings"
    ),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name for mapping resolution"),
    record_history: bool = typer.Option(True, "--record-history/--no-record-history", help="Record ingestion in history"),
) -> None:
    """Ingest all tar.gz bundles from a drop folder."""
    # Determine config manager
    config_manager = None
    config_dir = None
    if mapping_config:
        config_dir = mapping_config
        config_manager = ConfigManager(mapping_config)
    elif os.environ.get("MOARK_CONFIG_DIR"):
        config_dir = Path(os.environ["MOARK_CONFIG_DIR"])
        config_manager = ConfigManager(config_dir)
    
    # Set up history manager if recording is enabled
    history_manager = None
    if record_history:
        history_dir = config_dir if config_dir else _get_default_config_dir()
        history_file = history_dir / "history.json"
        history_manager = HistoryManager(history_file)
    
    bundles = sorted(drop_dir.glob("*.tar.gz"))
    if not bundles:
        warn(f"No bundles found in {drop_dir}")
        return
    for tar in bundles:
        try:
            ingest_tar(
                tar, 
                remote_template, 
                username, 
                password, 
                mapping,
                config_manager=config_manager,
                profile=profile,
                history_manager=history_manager,
            )
        except Exception as e:
            warn(f"Failed to ingest {tar.name}: {e}")


def main():
    app()


if __name__ == "__main__":
    main()

