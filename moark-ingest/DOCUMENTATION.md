# Moses in the Ark - Ingest Documentation

**Complete Documentation for the Ingest Component**

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Command Reference](#command-reference)
4. [Terminal UI Guide](#terminal-ui-guide)
5. [S3 Configuration](#s3-configuration)
6. [Mapping Dictionary](#mapping-dictionary)
7. [Examples](#examples)
8. [API Reference](#api-reference)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## 1. Overview

The **Ingest** component of Moses in the Ark is responsible for loading bundles in air-gapped networks and uploading them to internal Git repositories using a mapping dictionary.

### 1.1 Features

- ✅ S3-based mapping dictionary management
- ✅ Auto-scan disk-on-key devices
- ✅ External → Internal name mapping
- ✅ Git credential management
- ✅ Upload history tracking
- ✅ Artifact extraction
- ✅ Terminal UI and CLI interfaces
- ✅ Mapping management CLI

### 1.2 System Requirements

- Python 3.10 or higher
- Git 2.0 or higher
- Terminal with Unicode support
- Access to S3-compatible storage (for mapping dictionary)
- Access to internal Git server

---

## 2. Installation

### 2.1 Standard Installation

```bash
# Navigate to ingest directory
cd moark-ingest

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
moark-ingest --version
moark-mapping --version

# Check TUI availability
moark-ingest-ui --help
```

---

## 3. Command Reference

### 3.1 CLI Command: `moark-ingest`

**Basic Syntax:**
```bash
moark-ingest [OPTIONS]
```

**Common Options:**

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--tar` | PATH | ✓ | Bundle file path |
| `--remote-template` | TEXT | ✓ | Git remote URL template |
| `--username` | TEXT | | Git username |
| `--password` | TEXT | | Git password |
| `--profile` | TEXT | | Configuration profile (default: default) |
| `--mapping-config` | PATH | | Configuration directory |
| `--artifacts-output-dir` | PATH | | Directory for extracted artifacts |
| `--force` | FLAG | | Force push to repository |
| `--insecure` | FLAG | | Disable SSL verification |

**Environment Variables:**
- `MOARK_REMOTE_TEMPLATE` - Git remote URL template
- `MOARK_REMOTE_USERNAME` - Git username
- `MOARK_REMOTE_PASSWORD` - Git password
- `MOARK_CONFIG_DIR` - Configuration directory

### 3.2 Terminal UI Command: `moark-ingest-ui`

**Basic Syntax:**
```bash
moark-ingest-ui [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--config-dir PATH` | Configuration directory |

### 3.3 Mapping CLI Command: `moark-mapping`

**Subcommands:**

```bash
# List mappings
moark-mapping list [--profile PROFILE]

# Add mapping
moark-mapping add EXTERNAL INTERNAL [--profile PROFILE] [--notes TEXT]

# Remove mapping
moark-mapping remove EXTERNAL [--profile PROFILE] [--force]

# Validate configuration
moark-mapping validate [--profile PROFILE]
```

---

## 4. Terminal UI Guide

### 4.1 UI Layout

```
┌──────────────────────────────────────────────────────────────┐
│ ⛵ Moses in the Ark - Load Bundle                            │
│ For support or questions, contact: Moshe Eliya              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 🔧 S3 Configuration                                          │
│                                                              │
│ S3 Endpoint URL:                                             │
│ [https://s3.internal.company_____________________]           │
│                                                              │
│ S3 Bucket Name:                                              │
│ [airgap-mappings________________________________]            │
│                                                              │
│ S3 Access Key (optional):                                    │
│ [access-key_____________________________________]            │
│                                                              │
│ S3 Secret Key (optional):                                    │
│ [**************_________________________________]            │
│                                                              │
│ ☐ Disable SSL Verification                                  │
│           [💾 Save & Download Mapping]                       │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│ 🔍 Bundle Scanner                                            │
│                                                              │
│ Scan Path (disk-on-key or folder):                          │
│ [/Volumes/USB or auto-scan___________________]              │
│              [🔎 Auto Scan]  [📁 Scan Path]                 │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│ 📦 Available Bundles                                         │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ File           │Repo Name│Size(MB)│Artifacts│        │   │
│ ├──────────────────────────────────────────────────────┤   │
│ │ project-202... │project  │  125.4 │   Yes   │        │   │
│ │ app-20241231...│app      │   45.2 │   No    │        │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│ 🗺️  Repository Mappings (External → Internal)               │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ External │Internal Repo  │Internal URL      │Team   │   │
│ ├──────────────────────────────────────────────────────┤   │
│ │ project  │classified-a   │git.internal/...  │sec    │   │
│ │ app      │internal-app   │git.internal/...  │dev    │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│ ⬆️  Upload Settings                                          │
│                                                              │
│ Target Git Username:                                         │
│ [git-user_______________________________________]            │
│                                                              │
│ Target Git Password:                                         │
│ [**************_________________________________]            │
│                                                              │
│ ☑ Verify Repository    ☐ Force Push                        │
│                                                              │
│ ─────────────────────────────────────────────────────────── │
│ 📜 Recent Ingests                                            │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Bundle    │Source→Target   │Status  │Time          │   │
│ ├──────────────────────────────────────────────────────┤   │
│ │ project...│proj→class-a    │✅ ok   │2024-12-31... │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Output:                                                      │
│ Ready to ingest bundle...                                    │
├──────────────────────────────────────────────────────────────┤
│    [⬆️ Upload Bundle]  [🔄 Refresh]  [🗑️  Clear Log]  [❌ Quit]│
└──────────────────────────────────────────────────────────────┘
```

### 4.2 UI Sections

**S3 Configuration Section:**
- Configure S3 endpoint and credentials
- Download mapping dictionary
- Save configuration for future use

**Bundle Scanner Section:**
- Auto-scan all USB devices
- Manual path scanning
- Display found bundles

**Bundles Table:**
- Shows all available bundles
- Click to select for upload
- Displays metadata (size, artifacts, etc.)

**Mappings Table:**
- Shows external → internal mappings
- Loaded from S3 dictionary
- Updated when dictionary refreshed

**Upload Settings:**
- Git credentials input
- Upload options (verify, force push)

**History Table:**
- Recent ingest operations
- Status and timestamp
- Source and target repositories

### 4.3 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Navigate between fields |
| `Enter` | Activate focused button / Select table row |
| `Space` | Toggle checkbox |
| `↑` / `↓` | Navigate table rows |
| `q` | Quit application |
| `Ctrl+C` | Force quit |

---

## 5. S3 Configuration

### 5.1 First-Time Setup

```bash
# Launch TUI
moark-ingest-ui

# In S3 Configuration section:
1. S3 Endpoint URL: https://s3.internal.company
2. S3 Bucket Name: airgap-mappings
3. S3 Access Key: (optional if using IAM)
4. S3 Secret Key: (optional if using IAM)
5. Click "Save & Download Mapping"
```

### 5.2 S3 Configuration File

Location: `~/.moark/s3_settings.json`

```json
{
  "endpoint_url": "https://s3.internal.company",
  "bucket_name": "airgap-mappings",
  "access_key": "AKIAIOSFODNN7EXAMPLE",
  "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region": "us-east-1",
  "verify_ssl": true
}
```

### 5.3 Supported S3 Implementations

- ✅ AWS S3
- ✅ MinIO
- ✅ Ceph Object Gateway
- ✅ Dell EMC ECS
- ✅ Any S3-compatible storage

---

## 6. Mapping Dictionary

### 6.1 Dictionary Structure

```json
{
  "_description": "Repository name mapping dictionary",
  "_version": "1.0",
  "_last_updated": "2024-12-31T10:00:00Z",
  "mappings": {
    "external-repo-name": {
      "internal_repo": "internal-repo-name",
      "internal_url": "https://git.internal.company/group/project.git",
      "description": "Project description",
      "team": "team-name",
      "classification": "secret"
    }
  }
}
```

### 6.2 Dictionary Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_description` | string | No | Human-readable description |
| `_version` | string | No | Dictionary version |
| `_last_updated` | string | No | ISO 8601 timestamp |
| `mappings` | object | Yes | External → Internal mappings |

**Mapping Entry Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `internal_repo` | string | Yes | Internal repository name |
| `internal_url` | string | Yes | Full Git URL for internal repo |
| `description` | string | No | Project description |
| `team` | string | No | Owning team |
| `classification` | string | No | Security classification |

### 6.3 Example Dictionary

See: `example-mapping-dict.json`

### 6.4 Dictionary Management

**Update Dictionary:**
1. Edit dictionary in S3
2. In TUI, click "Save & Download Mapping"
3. Local cache updated automatically

**Manual Dictionary:**
Location: `~/.moark/mapping-dict.json`

Can be edited manually if S3 is unavailable.

---

## 7. Examples

### 7.1 Complete First-Time Setup

```bash
# 1. Install
pip install moark-ingest[ui]

# 2. Launch TUI
moark-ingest-ui

# 3. Configure S3
#    - Enter endpoint and credentials
#    - Click "Save & Download Mapping"

# 4. Insert USB drive

# 5. Scan for bundles
#    - Click "Auto Scan"

# 6. Select bundle from table

# 7. Enter Git credentials

# 8. Click "Upload Bundle"
```

### 7.2 CLI Ingest

```bash
# Basic ingest
moark-ingest \
  --tar /path/to/bundle.tar.gz \
  --remote-template "https://{username}:{password}@git.internal/{repo}.git" \
  --username git-user \
  --password git-password

# With environment variables
export MOARK_REMOTE_TEMPLATE="https://git.internal/{repo}.git"
export MOARK_REMOTE_USERNAME="git-user"
export MOARK_REMOTE_PASSWORD="git-password"

moark-ingest --tar /path/to/bundle.tar.gz
```

### 7.3 Ingest with Artifact Extraction

```bash
moark-ingest \
  --tar /path/to/bundle.tar.gz \
  --remote-template "https://user:pass@git.internal/{repo}.git" \
  --username git-user \
  --password git-password \
  --artifacts-output-dir ./extracted-artifacts
```

### 7.4 Force Push

```bash
moark-ingest \
  --tar /path/to/bundle.tar.gz \
  --remote-template "https://user:pass@git.internal/{repo}.git" \
  --username git-user \
  --password git-password \
  --force
```

### 7.5 Using Profiles

```bash
# Create profile with mapping
moark-mapping add \
  external-name \
  internal/repo/path \
  --profile production \
  --notes "Production repository"

# Ingest with profile
moark-ingest \
  --tar /path/to/bundle.tar.gz \
  --profile production \
  --remote-template "https://user:pass@git.internal/{repo}.git"
```

### 7.6 Mapping Management

```bash
# List all mappings
moark-mapping list

# List for specific profile
moark-mapping list --profile production

# Add new mapping
moark-mapping add \
  external-app \
  internal/apps/production-app \
  --notes "Main application"

# Remove mapping
moark-mapping remove external-app

# Validate configuration
moark-mapping validate
```

---

## 8. API Reference

### 8.1 Python API

```python
from moark_ingest.s3_client import S3Client, load_mapping_dict, get_internal_repo_info
from moark_ingest.bundle_scanner import scan_bundles, auto_scan_for_bundles
from moark_ingest.history_manager import HistoryManager

# S3 client
s3_client = S3Client(
    endpoint_url="https://s3.internal.company",
    bucket_name="airgap-mappings",
    access_key="access-key",
    secret_key="secret-key"
)

# Download mapping dictionary
mapping_dict = s3_client.download_mapping_dict()

# Scan for bundles
bundles = auto_scan_for_bundles()

# Get internal repo info
internal_info = get_internal_repo_info(mapping_dict, "external-name")

# History management
history = HistoryManager("~/.moark/history.json")
entries = history.get_entries(limit=10)
```

### 8.2 Module Reference

**moark_ingest.ingest**
- `ingest()` - Main ingest function
- `extract_bundle()` - Extract tar.gz
- `push_to_remote()` - Push to Git

**moark_ingest.s3_client**
- `S3Client` - S3 client class
- `download_mapping_dict()` - Download dictionary
- `get_internal_repo_info()` - Lookup mapping

**moark_ingest.bundle_scanner**
- `BundleInfo` - Bundle metadata class
- `scan_bundles()` - Scan directory
- `auto_scan_for_bundles()` - Auto-detect USB
- `find_disk_on_key_paths()` - Find mount points

**moark_ingest.history_manager**
- `HistoryManager` - History tracking
- `add_entry()` - Record transfer
- `get_entries()` - Query history

**moark_ingest.s3_settings**
- `S3Settings` - Settings manager
- `load()` / `save()` - Persistence
- `is_configured()` - Check setup

---

## 9. Best Practices

### 9.1 Security

✅ **DO:**
- Keep mapping dictionary updated
- Use individual Git credentials
- Enable repository verification
- Review history regularly
- Keep S3 credentials secure

❌ **DON'T:**
- Share Git credentials
- Skip mapping validation
- Force push without reason
- Ignore upload errors
- Store credentials in scripts

### 9.2 Operations

✅ **DO:**
- Update mapping dictionary before ingesting
- Scan USB drive before manual entry
- Verify bundle integrity
- Check history for duplicates
- Clean up extracted artifacts

❌ **DON'T:**
- Skip S3 configuration
- Ignore mapping errors
- Delete bundles immediately after upload
- Upload without verification
- Mix environments (dev/prod)

### 9.3 Workflow

✅ **DO:**
- Use TUI for interactive work
- Use CLI for automation
- Document mapping changes
- Keep audit trail
- Test with small bundles first

❌ **DON'T:**
- Bypass mapping system
- Upload to wrong repository
- Skip error messages
- Delete history files
- Modify configuration manually

---

## 10. Troubleshooting

### 10.1 Common Issues

**Issue: "Cannot connect to S3"**
```
Cause: Network connectivity or configuration issue

Solution:
1. Verify endpoint URL format (https://...)
2. Test network connectivity: ping s3.internal.company
3. Check S3 credentials
4. Try disabling SSL verification (temporarily)
5. Verify bucket exists and is accessible
```

**Issue: "No mapping found for repository"**
```
Cause: Missing entry in mapping dictionary

Solution:
1. Refresh mapping dictionary (Click "Save & Download")
2. Verify bundle repo name in manifest
3. Check dictionary in S3
4. Contact admin to add mapping
5. Add manual mapping if needed
```

**Issue: "Upload failed: Authentication required"**
```
Cause: Invalid or missing Git credentials

Solution:
1. Verify username and password
2. Check account has push access
3. Test credentials manually: git push
4. Verify internal GitLab is accessible
5. Check network connectivity
```

**Issue: "Bundle file not found"**
```
Cause: USB drive not mounted or wrong path

Solution:
1. Verify USB drive is inserted
2. Check mount point: ls /Volumes (macOS)
3. Try auto-scan instead of manual path
4. Verify file extension is .tar.gz
5. Check file permissions
```

**Issue: "Repository does not exist"**
```
Cause: Internal repository not created

Solution:
1. Create repository in internal GitLab
2. Verify repository URL in mapping
3. Check user has access to repository
4. Test URL manually
```

### 10.2 Debug Information

**View Configuration:**
```bash
# S3 settings
cat ~/.moark/s3_settings.json

# Mapping dictionary
cat ~/.moark/mapping-dict.json

# History
cat ~/.moark/history.json
```

**Test S3 Connection:**
```bash
# Using AWS CLI (if available)
aws s3 --endpoint-url https://s3.internal.company ls s3://airgap-mappings/
```

**Verify Bundle:**
```bash
# Check bundle contents
tar -tzf bundle.tar.gz

# Extract manifest only
tar -xzf bundle.tar.gz manifest.json
cat manifest.json
```

### 10.3 Log Files

TUI logs are displayed in real-time in the output section.

For CLI, redirect output:
```bash
moark-ingest ... 2>&1 | tee ingest.log
```

---

## 11. Advanced Usage

### 11.1 Automation Script

```bash
#!/bin/bash
# auto-ingest.sh - Automated bundle ingestion

BUNDLE_DIR="/Volumes/USB"
CONFIG_DIR="~/.moark"

# Find all bundles
for bundle in "$BUNDLE_DIR"/*.tar.gz; do
  echo "Processing: $bundle"
  
  moark-ingest \
    --tar "$bundle" \
    --remote-template "$MOARK_REMOTE_TEMPLATE" \
    --username "$MOARK_REMOTE_USERNAME" \
    --password "$MOARK_REMOTE_PASSWORD" \
    --config-dir "$CONFIG_DIR"
  
  if [ $? -eq 0 ]; then
    echo "✓ Success: $bundle"
    # Optionally move to processed folder
    mv "$bundle" "$BUNDLE_DIR/processed/"
  else
    echo "✗ Failed: $bundle"
  fi
done
```

### 11.2 Scheduled Updates

```bash
# Cron job to refresh mapping dictionary daily
0 9 * * * /usr/local/bin/refresh-mappings.sh

# refresh-mappings.sh
#!/bin/bash
export MOARK_CONFIG_DIR="~/.moark"
python3 -c "
from moark_ingest.s3_settings import S3Settings
from moark_ingest.s3_client import S3Client
settings = S3Settings('$MOARK_CONFIG_DIR/s3_settings.json')
if settings.is_configured():
    client = S3Client(
        settings.get_endpoint_url(),
        settings.get_bucket_name(),
        settings.get_access_key(),
        settings.get_secret_key()
    )
    mapping = client.download_mapping_dict()
    client.save_mapping_dict_locally(mapping, '$MOARK_CONFIG_DIR/mapping-dict.json')
    print('Mapping dictionary updated')
"
```

---

## 12. FAQ

**Q: How often should I update the mapping dictionary?**
A: Daily or before each major ingestion. Click "Save & Download Mapping" in TUI.

**Q: Can I ingest multiple bundles at once?**
A: Yes in TUI (select one at a time), or use automation script for CLI.

**Q: What happens if mapping is missing?**
A: Upload will fail. Contact admin to add mapping to dictionary.

**Q: Can I override the mapping?**
A: Not directly. Add manual mapping using `moark-mapping add`.

**Q: How long are history entries kept?**
A: Indefinitely. Clean up manually if needed.

**Q: Can I use without S3?**
A: Yes, create manual mapping dictionary at `~/.moark/mapping-dict.json`.

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**For Support:** Contact Moshe Eliya


