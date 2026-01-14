"""GitLab API client for private GitLab instances."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse

import requests


@dataclass
class GitLabConfig:
    """Configuration for connecting to a GitLab instance."""

    base_url: str  # e.g., "https://gitlab.mycompany.com"
    username: str | None = None
    password: str | None = None
    token: str | None = None  # Deprecated: use password instead


@dataclass
class ArtifactInfo:
    """Metadata about a downloaded artifact."""

    job_id: int
    job_name: str
    file_name: str
    file_size: int
    pipeline_id: int
    ref: str


class GitLabClient:
    """Client for interacting with GitLab API."""

    def __init__(self, config: GitLabConfig, verify_ssl: bool = True) -> None:
        self.config = config
        self.verify_ssl = verify_ssl
        self._session = requests.Session()
        self._session.verify = verify_ssl
        
        # Support both password (preferred) and token (legacy)
        if config.password and config.username:
            # Use HTTP Basic Auth with username:password
            from requests.auth import HTTPBasicAuth
            self._session.auth = HTTPBasicAuth(config.username, config.password)
        elif config.token:
            # Legacy: use token in header
            self._session.headers["PRIVATE-TOKEN"] = config.token

    def build_clone_url(self, repo_path: str) -> str:
        """Build authenticated Git clone URL.

        Constructs URL in format: https://{username}:{password}@{host}/{repo_path}.git
        Uses password if available, otherwise falls back to token.
        """
        parsed = urlparse(self.config.base_url)
        host = parsed.netloc

        # Prefer password over token
        if self.config.username and self.config.password:
            auth = f"{self.config.username}:{self.config.password}@"
        elif self.config.username and self.config.token:
            # Legacy: use token
            auth = f"{self.config.username}:{self.config.token}@"
        else:
            auth = ""

        # Ensure repo_path doesn't have leading/trailing slashes
        repo_path = repo_path.strip("/")

        return f"{parsed.scheme}://{auth}{host}/{repo_path}.git"

    def get_project_id(self, repo_path: str) -> int:
        """Get project ID from repo path like 'group/subgroup/project'."""
        encoded_path = quote(repo_path, safe="")
        url = f"{self.config.base_url}/api/v4/projects/{encoded_path}"
        response = self._session.get(url)
        response.raise_for_status()
        return response.json()["id"]

    def get_latest_successful_pipeline(
        self, project_id: int, ref: str | None = None
    ) -> dict | None:
        """Get the latest successful pipeline for a ref (or default branch).

        Args:
            project_id: The GitLab project ID
            ref: Optional branch or tag name to filter by

        Returns:
            Pipeline dict or None if no successful pipeline found
        """
        url = f"{self.config.base_url}/api/v4/projects/{project_id}/pipelines"
        params = {"status": "success", "per_page": 1, "order_by": "id", "sort": "desc"}
        if ref:
            params["ref"] = ref

        response = self._session.get(url, params=params)
        response.raise_for_status()
        pipelines = response.json()
        return pipelines[0] if pipelines else None

    def list_pipeline_jobs_with_artifacts(
        self, project_id: int, pipeline_id: int
    ) -> list[dict]:
        """List all jobs in a pipeline that have artifacts.

        Args:
            project_id: The GitLab project ID
            pipeline_id: The pipeline ID

        Returns:
            List of job dicts that have artifacts
        """
        url = f"{self.config.base_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        response = self._session.get(url)
        response.raise_for_status()
        jobs = response.json()
        return [job for job in jobs if job.get("artifacts", [])]

    def download_job_artifacts(
        self, project_id: int, job_id: int, job_name: str, pipeline_id: int, ref: str, output_path: Path
    ) -> ArtifactInfo:
        """Download artifacts zip for a specific job.

        Args:
            project_id: The GitLab project ID
            job_id: The job ID
            job_name: Name of the job
            pipeline_id: The pipeline ID
            ref: The git ref (branch/tag)
            output_path: Path to save the artifacts zip

        Returns:
            ArtifactInfo with metadata about the downloaded artifact
        """
        url = f"{self.config.base_url}/api/v4/projects/{project_id}/jobs/{job_id}/artifacts"
        response = self._session.get(url, stream=True)
        response.raise_for_status()

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        file_size = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                file_size += len(chunk)

        return ArtifactInfo(
            job_id=job_id,
            job_name=job_name,
            file_name=output_path.name,
            file_size=file_size,
            pipeline_id=pipeline_id,
            ref=ref,
        )

