from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import typer

if TYPE_CHECKING:
    from .gitlab_client import GitLabClient

from .utils import (
    derive_repo_name,
    ensure_dir,
    git_version,
    info,
    iso_timestamp,
    read_submodules_from_worktree,
    run_git,
    set_ssl_verify,
    stage_tarball,
    success,
    tempdir,
    warn,
)

app = typer.Typer(help="Pack external Git repo (and submodules) into a tar.gz for airgap transfer.")


def clone_submodules(entries: List[dict], base_dir: Path) -> List[dict]:
    submodules_dir = base_dir / "submodules"
    cloned = []
    for entry in entries:
        path = entry["path"]
        url = entry["url"]
        target = submodules_dir / f"{path}.git"
        ensure_dir(target.parent)
        info(f"Cloning submodule {path} -> {target}")
        run_git(["clone", "--mirror", url, str(target)])
        cloned.append({"path": path, "url": url, "mirror": str(target.relative_to(base_dir))})
    return cloned


def download_artifacts(
    gitlab_client: "GitLabClient",
    repo_path: str,
    artifacts_ref: Optional[str],
    bundle_root: Path,
) -> List[dict]:
    """Download CI/CD artifacts from GitLab and store in bundle.

    Args:
        gitlab_client: Configured GitLab API client
        repo_path: Project path in GitLab
        artifacts_ref: Optional branch/tag to get artifacts from
        bundle_root: Root directory of the bundle

    Returns:
        List of artifact metadata dicts for manifest
    """
    from .gitlab_client import ArtifactInfo

    artifacts_manifest: List[dict] = []

    try:
        project_id = gitlab_client.get_project_id(repo_path)
    except Exception as e:
        warn(f"Failed to get project ID for {repo_path}: {e}")
        return artifacts_manifest

    pipeline = gitlab_client.get_latest_successful_pipeline(project_id, artifacts_ref)
    if not pipeline:
        warn(f"No successful pipeline found for ref '{artifacts_ref or 'default branch'}'")
        return artifacts_manifest

    pipeline_id = pipeline["id"]
    pipeline_ref = pipeline.get("ref", artifacts_ref or "unknown")
    info(f"Found pipeline {pipeline_id} for ref '{pipeline_ref}'")

    jobs = gitlab_client.list_pipeline_jobs_with_artifacts(project_id, pipeline_id)
    if not jobs:
        warn("No jobs with artifacts found in pipeline")
        return artifacts_manifest

    artifacts_dir = bundle_root / "artifacts"
    ensure_dir(artifacts_dir)

    for job in jobs:
        job_id = job["id"]
        job_name = job["name"]
        job_dir = artifacts_dir / job_name
        ensure_dir(job_dir)
        output_path = job_dir / "artifacts.zip"

        try:
            info(f"Downloading artifacts for job '{job_name}' (ID: {job_id})")
            artifact_info: ArtifactInfo = gitlab_client.download_job_artifacts(
                project_id=project_id,
                job_id=job_id,
                job_name=job_name,
                pipeline_id=pipeline_id,
                ref=pipeline_ref,
                output_path=output_path,
            )
            artifacts_manifest.append({
                "job_id": artifact_info.job_id,
                "job_name": artifact_info.job_name,
                "file_name": artifact_info.file_name,
                "file_size": artifact_info.file_size,
                "pipeline_id": artifact_info.pipeline_id,
                "ref": artifact_info.ref,
            })
            info(f"Downloaded {artifact_info.file_size} bytes for job '{job_name}'")
        except Exception as e:
            warn(f"Failed to download artifacts for job '{job_name}': {e}")
            continue

    return artifacts_manifest


@app.command("pack")
def pack_repo(
    repo_url: Optional[str] = typer.Option(None, "--repo-url", help="Git URL to clone (for public repos)"),
    output: Path = typer.Option(Path("./dist"), "--output", "-o", file_okay=False, help="Output directory"),
    repo_name: Optional[str] = typer.Option(None, "--repo-name", help="Override derived repo name"),
    with_submodules: bool = typer.Option(False, "--with-submodules", help="Clone submodules mirrors too"),
    # GitLab private source parameters
    source_gitlab_url: Optional[str] = typer.Option(
        None, "--source-gitlab-url", help="Private GitLab base URL (e.g., https://gitlab.mycompany.com)"
    ),
    repo_path: Optional[str] = typer.Option(
        None, "--repo-path", help="Project path in GitLab (e.g., group/subgroup/project)"
    ),
    source_username: Optional[str] = typer.Option(
        None, "--source-username", envvar="SOURCE_GITLAB_USERNAME", help="GitLab username for authentication"
    ),
    source_password: Optional[str] = typer.Option(
        None, "--source-password", envvar="SOURCE_GITLAB_PASSWORD", help="GitLab password for authentication"
    ),
    source_token: Optional[str] = typer.Option(
        None, "--source-token", envvar="SOURCE_GITLAB_TOKEN", help="GitLab token for authentication (deprecated: use password)"
    ),
    # Artifact parameters
    with_artifacts: bool = typer.Option(
        False, "--with-artifacts", help="Download CI/CD artifacts from GitLab"
    ),
    artifacts_ref: Optional[str] = typer.Option(
        None, "--artifacts-ref", help="Branch/tag for artifacts (default: default branch)"
    ),
    insecure: bool = typer.Option(
        False, "--insecure", "-k", help="Disable SSL certificate verification (for self-signed certs)"
    ),
) -> None:
    """Create a tar.gz bundle with a bare mirror and manifest."""
    # Configure SSL verification
    if insecure:
        set_ssl_verify(False)
        warn("SSL certificate verification disabled")

    # Parameter validation
    use_gitlab_source = source_gitlab_url is not None

    if use_gitlab_source:
        if not repo_path:
            raise typer.BadParameter(
                "--source-gitlab-url requires --repo-path to be specified"
            )
    else:
        if not repo_url:
            raise typer.BadParameter(
                "Either --repo-url or --source-gitlab-url with --repo-path must be provided"
            )

    if with_artifacts and not use_gitlab_source:
        raise typer.BadParameter(
            "--with-artifacts requires GitLab source parameters (--source-gitlab-url and --repo-path)"
        )

    # Determine the effective repo URL
    if use_gitlab_source:
        from .gitlab_client import GitLabClient, GitLabConfig

        gitlab_config = GitLabConfig(
            base_url=source_gitlab_url,
            username=source_username,
            password=source_password,
            token=source_token,  # Legacy support
        )
        gitlab_client = GitLabClient(gitlab_config, verify_ssl=not insecure)
        effective_repo_url = gitlab_client.build_clone_url(repo_path)
    else:
        effective_repo_url = repo_url
        gitlab_client = None

    resolved_repo_name = repo_name or derive_repo_name(effective_repo_url)
    ensure_dir(output)

    with tempdir() as tmp:
        tmp_path = Path(tmp)
        main_mirror = tmp_path / f"{resolved_repo_name}.git"
        info(f"Cloning mirror of {effective_repo_url} -> {main_mirror}")
        run_git(["clone", "--mirror", effective_repo_url, str(main_mirror)])

        submodules_manifest: List[dict] = []
        if with_submodules:
            worktree = tmp_path / "worktree"
            info("Inspecting submodules via shallow recursive clone")
            run_git(["clone", "--recursive", "--depth", "1", effective_repo_url, str(worktree)])
            sub_entries = read_submodules_from_worktree(worktree)
            if sub_entries:
                submodules_manifest = clone_submodules(sub_entries, tmp_path)
            else:
                warn("No submodules found in .gitmodules")

        bundle_root = tmp_path / "bundle" / resolved_repo_name
        ensure_dir(bundle_root)
        shutil.move(str(main_mirror), bundle_root / f"{resolved_repo_name}.git")

        if submodules_manifest:
            sub_dir = bundle_root / "submodules"
            ensure_dir(sub_dir)
            for entry in submodules_manifest:
                src = tmp_path / entry["mirror"]
                dest = sub_dir / Path(entry["mirror"]).name
                shutil.move(src, dest)
                entry["mirror"] = str(dest.relative_to(bundle_root))

        # Download artifacts if requested
        artifacts_manifest: List[dict] = []
        if with_artifacts and gitlab_client is not None:
            info("Downloading CI/CD artifacts...")
            artifacts_manifest = download_artifacts(
                gitlab_client=gitlab_client,
                repo_path=repo_path,
                artifacts_ref=artifacts_ref,
                bundle_root=bundle_root,
            )
            if artifacts_manifest:
                success(f"Downloaded artifacts from {len(artifacts_manifest)} job(s)")
            else:
                warn("No artifacts were downloaded")

        manifest = {
            "repo_url": effective_repo_url,
            "repo_name": resolved_repo_name,
            "created_at": iso_timestamp(),
            "git_version": git_version(),
            "with_submodules": with_submodules,
            "submodules": submodules_manifest,
            "with_artifacts": with_artifacts,
            "artifacts": artifacts_manifest,
        }

        # Add GitLab source metadata if applicable
        if use_gitlab_source:
            manifest["source_gitlab_url"] = source_gitlab_url
            manifest["repo_path"] = repo_path

        (bundle_root / "manifest.json").write_text(json.dumps(manifest, indent=2))

        tar_name = f"{resolved_repo_name}-{manifest['created_at']}.tar.gz"
        tar_path = output / tar_name
        stage_tarball(bundle_root, tar_path)
        success(f"Created bundle: {tar_path}")


def main():
    app()


if __name__ == "__main__":
    main()

