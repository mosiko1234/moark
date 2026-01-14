"""Utility functions for airgap-ingest."""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable

import typer

# Global flag for SSL verification bypass
_ssl_verify = True


def set_ssl_verify(verify: bool) -> None:
    """Set global SSL verification flag for git operations."""
    global _ssl_verify
    _ssl_verify = verify


def run_git(args: Iterable[str], cwd: Path | None = None) -> None:
    """Run git command with echo on failure."""
    cmd = ["git"]
    if not _ssl_verify:
        cmd.extend(["-c", "http.sslVerify=false"])
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")


def derive_repo_name(repo_url: str) -> str:
    name = repo_url.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    # sanitize for file system
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name:
        raise ValueError("could not derive repository name")
    return name


def load_mapping(mapping_path: Path | None) -> Dict[str, str]:
    if mapping_path is None:
        return {}
    data = json.loads(mapping_path.read_text())
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    raise ValueError("mapping file must be a JSON object of {external: internal}")


def resolve_remote_url(
    template: str,
    repo: str,
    username: str | None,
    password: str | None,
) -> str:
    return template.format(repo=repo, username=username or "", password=password or "")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def warn(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.YELLOW)


def info(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.CYAN)


def success(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.GREEN)

