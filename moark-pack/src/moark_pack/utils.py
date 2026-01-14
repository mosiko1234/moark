"""Utility functions for airgap-pack."""

import configparser
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Iterable, List

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


def git_version() -> str:
    return subprocess.check_output(["git", "--version"], text=True).strip()


def derive_repo_name(repo_url: str) -> str:
    name = repo_url.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    # sanitize for file system
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name:
        raise ValueError("could not derive repository name")
    return name


def parse_gitlab_url(repo_url: str) -> tuple[str, str]:
    """Parse a GitLab repository URL into base URL and repo path.
    
    Args:
        repo_url: Full GitLab repository URL (e.g., https://gitlab.com/group/project.git)
        
    Returns:
        Tuple of (base_url, repo_path)
        
    Example:
        parse_gitlab_url("https://kh-gitlab.kayhut.local/root/moshe-test.git")
        -> ("https://kh-gitlab.kayhut.local", "root/moshe-test")
    """
    from urllib.parse import urlparse
    
    # Remove .git suffix if present
    url = repo_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Extract repo path (remove leading slash)
    repo_path = parsed.path.lstrip("/")
    
    return base_url, repo_path


def iso_timestamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def read_submodules_from_worktree(worktree: Path) -> List[dict]:
    gitmodules = worktree / ".gitmodules"
    if not gitmodules.exists():
        return []
    parser = configparser.ConfigParser()
    parser.read(gitmodules)
    entries = []
    for section in parser.sections():
        path = parser.get(section, "path", fallback=None)
        url = parser.get(section, "url", fallback=None)
        if path and url:
            entries.append({"path": path, "url": url})
    return entries


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def stage_tarball(source_dir: Path, tar_path: Path) -> None:
    import tarfile

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(source_dir, arcname=source_dir.name)


def tempdir() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix="airgap-pack-")


def warn(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.YELLOW)


def info(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.CYAN)


def success(msg: str) -> None:
    typer.secho(msg, fg=typer.colors.GREEN)

