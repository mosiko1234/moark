# Moses in the Ark - Pack Documentation

**Complete Documentation for the Pack Component**

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Command Reference](#command-reference)
4. [Terminal UI Guide](#terminal-ui-guide)
5. [Configuration](#configuration)
6. [Examples](#examples)
7. [API Reference](#api-reference)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## 1. Overview

The **Pack** component of Moses in the Ark is responsible for creating portable bundles from Git repositories in internet-connected networks. These bundles can then be physically transferred to air-gapped networks for ingestion.

### 1.1 Features

- ✅ Clone public and private Git repositories
- ✅ Support for GitLab, GitHub, and Bitbucket
- ✅ Username/Password authentication for GitLab
- ✅ Optional submodule inclusion
- ✅ Optional CI/CD artifact download
- ✅ Intelligent URL parsing
- ✅ Real-time progress feedback
- ✅ Terminal UI and CLI interfaces

### 1.2 System Requirements

- Python 3.10 or higher
- Git 2.0 or higher
- Terminal with Unicode support
- Internet connectivity
- Sufficient disk space for cloning repositories

---

## 2. Installation

### 2.1 Standard Installation

```bash
# Navigate to pack directory
cd moark-pack

# Install with UI support
pip install ".[ui]"

# Or install CLI only
pip install .
```

### 2.2 Development Installation

```bash
# Install in editable mode
pip install -e ".[ui]"
```

### 2.3 Verify Installation

```bash
# Check CLI availability
moark-pack --version

# Check TUI availability
moark-pack-ui --help
```

---

## 3. Command Reference

### 3.1 CLI Command: `moark-pack pack`

**Basic Syntax:**
```bash
moark-pack pack [OPTIONS]
```

**Common Options:**

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--repo-url` | TEXT | * | Public repository URL |
| `--source-gitlab-url` | TEXT | * | Private GitLab base URL |
| `--repo-path` | TEXT | * | GitLab repository path |
| `--source-username` | TEXT | | GitLab username |
| `--source-password` | TEXT | | GitLab password |
| `--output-dir` | PATH | | Output directory (default: ./dist) |
| `--repo-name` | TEXT | | Override repository name |
| `--with-submodules` | FLAG | | Include submodules |
| `--with-artifacts` | FLAG | | Download CI/CD artifacts |
| `--artifacts-ref` | TEXT | | Branch/tag for artifacts (default: main) |
| `--insecure` | FLAG | | Disable SSL verification |

**Note:** Either `--repo-url` (for public) OR `--source-gitlab-url` + `--repo-path` (for private) must be provided.

### 3.2 Terminal UI Command: `moark-pack-ui`

**Basic Syntax:**
```bash
moark-pack-ui
```

Launches the interactive terminal user interface.

---

## 4. Terminal UI Guide

### 4.1 UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ⛵ Moses in the Ark - Create Bundle                         │
│ For support or questions, contact: Moshe Eliya             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Repository URL:                                             │
│ [https://gitlab.com/group/project.git_________________]     │
│                                                             │
│ Username:                                                   │
│ [deploy-user___________________________________]            │
│                                                             │
│ Password:                                                   │
│ [********_______________________________________]            │
│                                                             │
│ Output Directory:                                           │
│ [./dist________________________________________]            │
│                                                             │
│ Repository Name (override):                                 │
│ [auto___________________________________________]            │
│                                                             │
│ ☑ Include Submodules    ☑ Download Artifacts              │
│                                                             │
│ Artifacts Ref (branch/tag):                                 │
│ [main___________________________________________]            │
│                                                             │
│ ☐ Disable SSL Verification                                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Output:                                                     │
│ Starting pack operation...                                  │
│ Cloning repository...                                       │
│ ✓ Repository cloned successfully                           │
│ Creating bundle...                                          │
│ ✓ Bundle created: project-20241231-143022.tar.gz          │
├─────────────────────────────────────────────────────────────┤
│         [Pack]        [Clear]        [Quit]                │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 UI Elements

**Input Fields:**
- **Repository URL:** Full Git repository URL
  - Public: `https://github.com/user/repo.git`
  - Private: `https://gitlab.company.com/group/project.git`
- **Username:** GitLab username (for private repos)
- **Password:** GitLab password (masked input)
- **Output Directory:** Where to save the bundle
- **Repository Name:** Optional override for bundle naming

**Checkboxes:**
- **Include Submodules:** Clone and bundle submodules
- **Download Artifacts:** Fetch CI/CD artifacts from GitLab
- **Disable SSL Verification:** Skip SSL certificate validation

**Buttons:**
- **Pack:** Start the packing process
- **Clear:** Clear the output log
- **Quit:** Exit the application

### 4.3 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Navigate between fields |
| `Enter` | Activate focused button |
| `Space` | Toggle checkbox |
| `q` | Quit application |
| `Ctrl+C` | Force quit |

---

## 5. Configuration

### 5.1 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SOURCE_GITLAB_PASSWORD` | GitLab password | `my-password` |

### 5.2 Output Structure

```
output-dir/
└── project-name-YYYYMMDD-HHMMSS.tar.gz
```

### 5.3 Bundle Contents

```
bundle.tar.gz
├── manifest.json           # Bundle metadata
├── repo.bundle             # Main repository bundle
├── submodules/             # Submodule bundles (optional)
│   ├── submodule1.bundle
│   └── submodule2.bundle
└── artifacts/              # CI/CD artifacts (optional)
    ├── job1/
    │   ├── artifact1.zip
    │   └── logs.txt
    └── job2/
        └── binary
```

---

## 6. Examples

### 6.1 Pack a Public Repository

```bash
# Using CLI
moark-pack pack \
  --repo-url https://github.com/user/public-project.git \
  --output-dir ./dist

# Using TUI
moark-pack-ui
# 1. Enter: https://github.com/user/public-project.git
# 2. Click "Pack"
```

### 6.2 Pack a Private GitLab Repository

```bash
# Using CLI
moark-pack pack \
  --source-gitlab-url https://gitlab.company.com \
  --repo-path team/private-project \
  --source-username deploy-user \
  --source-password my-password \
  --output-dir ./dist

# Using environment variable for password
export SOURCE_GITLAB_PASSWORD=my-password
moark-pack pack \
  --source-gitlab-url https://gitlab.company.com \
  --repo-path team/private-project \
  --source-username deploy-user \
  --output-dir ./dist
```

### 6.3 Pack with Submodules

```bash
moark-pack pack \
  --repo-url https://github.com/user/project-with-subs.git \
  --with-submodules \
  --output-dir ./dist
```

### 6.4 Pack with CI/CD Artifacts

```bash
moark-pack pack \
  --source-gitlab-url https://gitlab.company.com \
  --repo-path team/backend-service \
  --source-username deploy-user \
  --source-password my-password \
  --with-artifacts \
  --artifacts-ref main \
  --output-dir ./dist
```

### 6.5 Pack with Custom Name

```bash
moark-pack pack \
  --repo-url https://github.com/user/project.git \
  --repo-name my-custom-name \
  --output-dir ./dist

# Output: my-custom-name-20241231-143022.tar.gz
```

### 6.6 Pack with SSL Verification Disabled

```bash
moark-pack pack \
  --source-gitlab-url https://gitlab.internal.company \
  --repo-path team/project \
  --source-username user \
  --source-password pass \
  --insecure \
  --output-dir ./dist
```

---

## 7. API Reference

### 7.1 Python API

```python
from moark_pack.gitlab_client import GitLabClient, GitLabConfig
from moark_pack.utils import run_command, parse_gitlab_url

# Create GitLab configuration
config = GitLabConfig(
    base_url="https://gitlab.company.com",
    username="deploy-user",
    password="my-password",
    verify_ssl=True
)

# Create client
client = GitLabClient(config)

# Get repository info
repo_info = client.get_repository("group/project")

# Parse GitLab URL
base_url, repo_path = parse_gitlab_url(
    "https://gitlab.company.com/group/project.git"
)
```

### 7.2 Module Reference

**moark_pack.pack**
- `pack()` - Main packing function
- `validate_inputs()` - Input validation
- `create_manifest()` - Generate metadata

**moark_pack.gitlab_client**
- `GitLabConfig` - Configuration class
- `GitLabClient` - API client class
- `build_clone_url()` - Construct authenticated URL

**moark_pack.utils**
- `parse_gitlab_url()` - Parse repository URL
- `run_command()` - Execute shell command
- `validate_url()` - URL validation

---

## 8. Best Practices

### 8.1 Security

✅ **DO:**
- Use environment variables for passwords
- Enable SSL verification (default)
- Use dedicated deployment credentials
- Verify bundle integrity before transfer

❌ **DON'T:**
- Store passwords in scripts
- Disable SSL verification without reason
- Use personal credentials for automation
- Share bundle files insecurely

### 8.2 Performance

✅ **DO:**
- Use local network when possible
- Check available disk space first
- Clean up old bundles regularly
- Use compression for large repos

❌ **DON'T:**
- Pack unnecessary submodules
- Download all artifacts if not needed
- Keep temporary files
- Pack very large repositories without planning

### 8.3 Workflow

✅ **DO:**
- Use TUI for interactive work
- Use CLI for automation
- Test with small repos first
- Document bundle contents
- Verify bundle before transfer

❌ **DON'T:**
- Pack sensitive data unnecessarily
- Skip verification steps
- Ignore error messages
- Delete source bundles too quickly

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue: "Authentication failed"**
```
Cause: Invalid credentials or insufficient permissions

Solution:
1. Verify username and password
2. Check repository access permissions
3. Try accessing repository in browser
4. Contact repository administrator
```

**Issue: "Clone failed: Repository not found"**
```
Cause: Invalid URL or missing repository

Solution:
1. Verify repository URL is correct
2. Check repository exists
3. Verify you have read access
4. Test URL in browser
```

**Issue: "Insufficient disk space"**
```
Cause: Not enough space for cloning and bundling

Solution:
1. Check available space: df -h
2. Clean up old bundles
3. Use different output directory
4. Remove unnecessary files
```

**Issue: "SSL certificate verification failed"**
```
Cause: Self-signed or invalid SSL certificate

Solution:
1. Verify SSL certificate is valid
2. Update system certificates
3. As last resort, use --insecure flag
```

**Issue: "Submodule clone failed"**
```
Cause: Submodule URL inaccessible or authentication issues

Solution:
1. Check submodule URLs in .gitmodules
2. Verify access to submodule repositories
3. Try without --with-submodules first
4. Clone submodules manually to test
```

### 9.2 Debug Mode

```bash
# Run with verbose output
moark-pack pack \
  --repo-url https://github.com/user/repo.git \
  --output-dir ./dist \
  --verbose

# Check Git operations
git clone --verbose <url>
git bundle verify repo.bundle
```

### 9.3 Log Files

```bash
# TUI logs are displayed in real-time
# For CLI, redirect output:
moark-pack pack ... 2>&1 | tee pack.log
```

---

## 10. Advanced Usage

### 10.1 Automation Script

```bash
#!/bin/bash
# pack-repositories.sh

REPOS=(
  "https://github.com/user/repo1.git"
  "https://github.com/user/repo2.git"
  "https://github.com/user/repo3.git"
)

OUTPUT_DIR="./bundles"
mkdir -p "$OUTPUT_DIR"

for repo in "${REPOS[@]}"; do
  echo "Packing $repo..."
  moark-pack pack \
    --repo-url "$repo" \
    --output-dir "$OUTPUT_DIR" \
    --with-submodules
  
  if [ $? -eq 0 ]; then
    echo "✓ Success: $repo"
  else
    echo "✗ Failed: $repo"
  fi
done
```

### 10.2 Integration with CI/CD

```yaml
# .gitlab-ci.yml
pack-for-airgap:
  stage: package
  script:
    - pip install moark-pack
    - moark-pack pack \
        --source-gitlab-url $CI_SERVER_URL \
        --repo-path $CI_PROJECT_PATH \
        --source-username $GITLAB_USER \
        --source-password $GITLAB_TOKEN \
        --with-artifacts \
        --artifacts-ref $CI_COMMIT_REF_NAME \
        --output-dir ./airgap-bundles
  artifacts:
    paths:
      - airgap-bundles/
    expire_in: 1 week
```

---

## 11. FAQ

**Q: Can I pack multiple repositories at once?**
A: Not in a single bundle. Create separate bundles for each repository.

**Q: What's the maximum repository size?**
A: No hard limit, but consider available disk space (2-3x repo size) and network bandwidth.

**Q: Can I pack from BitBucket or other Git providers?**
A: Yes for cloning, but artifact download is GitLab-specific.

**Q: How long does packing take?**
A: Depends on repository size and network speed. Small repos: 1-2 minutes. Large repos: 10-30 minutes.

**Q: Can I resume a failed pack operation?**
A: No, you need to restart the operation.

**Q: Are Git LFS files included?**
A: Yes, if Git LFS is installed and configured.

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**For Support:** Contact Moshe Eliya


