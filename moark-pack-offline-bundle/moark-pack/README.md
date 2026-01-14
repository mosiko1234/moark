# ⛵ Moses in the Ark - Pack

**Moses in the Ark** is a secure air-gap transfer system for Git repositories and CI/CD artifacts.

The **Pack** tool creates bundles in internet-connected networks for transfer to air-gapped environments.

## Installation

```bash
pip install .
# Or with Terminal UI
pip install ".[ui]"
```

Requirements: git installed, Python 3.10+.

## Usage

### Terminal User Interface (TUI)

```bash
moark-pack-ui
```

Opens an interactive terminal interface for creating bundles. The interface includes:
- **Repository URL**: Single input for full Git repository URL
- **Credentials**: Username and password for GitLab authentication
- **Options**: Submodules, artifacts, SSL verification
- **Real-time output**: Live streaming of the packing process

The system intelligently detects:
- Public repositories (GitHub, GitLab.com, Bitbucket)
- Private GitLab instances (requires credentials)
- Automatic URL parsing and configuration

### CLI Usage

#### Pack a public repository

```bash
moark-pack pack \
  --repo-url https://github.com/user/project.git \
  --output-dir ./dist
```

#### Pack a private GitLab repository

```bash
moark-pack pack \
  --source-gitlab-url https://gitlab.company.com \
  --repo-path group/project \
  --source-username deploy-user \
  --source-password your-password \
  --output-dir ./dist
```

#### Include submodules

```bash
moark-pack pack \
  --repo-url https://github.com/user/project.git \
  --with-submodules \
  --output-dir ./dist
```

#### Download CI/CD artifacts

```bash
moark-pack pack \
  --source-gitlab-url https://gitlab.company.com \
  --repo-path group/project \
  --source-username deploy-user \
  --source-password your-password \
  --with-artifacts \
  --artifacts-ref main \
  --output-dir ./dist
```

## Parameters

### Pack Parameters

- `--repo-url`: Public Git repository URL (for public repos)
- `--source-gitlab-url`: GitLab base URL (for private GitLab)
- `--repo-path`: Repository path in GitLab (e.g., `group/project`)
- `--source-username`: GitLab username
- `--source-password`: GitLab password (or ENV: `SOURCE_GITLAB_PASSWORD`)
- `--output-dir`: Output directory for bundles (default: `./dist`)
- `--repo-name`: Override repository name
- `--with-submodules`: Include submodules
- `--with-artifacts`: Download CI/CD artifacts
- `--artifacts-ref`: Branch/tag for artifacts (default: `main`)
- `--insecure`: Disable SSL verification

### Environment Variables

- `SOURCE_GITLAB_PASSWORD` - GitLab password (alternative to --source-password)

## Output

The tool creates a `.tar.gz` bundle containing:
- Git repository bundle (`.bundle` file)
- Submodules (if requested)
- CI/CD artifacts (if requested)
- Manifest file with metadata

Example output:
```
dist/
└── project-2024-01-15-143022.tar.gz
```

## Security Notes

- Passwords are never stored or logged
- SSL verification is enabled by default
- Credentials are only used during the packing process
- Bundle files are self-contained and portable

## For Support

For support or questions, contact: **Moshe Eliya**
