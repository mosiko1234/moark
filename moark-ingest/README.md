# ⛵ Moses in the Ark - Ingest

**Moses in the Ark** is a secure air-gap transfer system for Git repositories and CI/CD artifacts.

The **Ingest** tool loads bundles in air-gapped networks and uploads them to internal Git repositories.

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
moark-ingest-ui
```

Opens an interactive terminal interface for loading bundles. The interface includes:
- **S3 Configuration**: Configure S3 connection for downloading mapping dictionary
- **Bundle Scanner**: Auto-scan disk-on-key or specific folders for bundles
- **Bundles Table**: View all available bundles with details
- **Mappings Table**: View external → internal repository mappings
- **Upload**: Automatically upload bundles to the correct internal repository
- **History**: View recent uploads

#### Workflow in TUI:

1. **Configure S3 (First Time)**:
   - Enter S3 endpoint URL (e.g., `https://s3.internal.company`)
   - Enter bucket name
   - Enter access key and secret key (optional)
   - Click "Save & Download Mapping" to download the mapping dictionary

2. **Scan for Bundles**:
   - Click "Auto Scan" to automatically scan all disk-on-key devices
   - Or enter a specific path and click "Scan Path"
   - The table will display all found bundles

3. **Select Bundle**:
   - Click on a row in the Bundles table
   - The system will automatically check if a mapping exists for the bundle

4. **Upload**:
   - Enter username and password for internal Git
   - Click "Upload Bundle"
   - The system will extract the bundle and upload it to the correct internal repository

### CLI Usage

#### Load from bundle file

```bash
export MOARK_REMOTE_TEMPLATE="https://{username}:{password}@git.internal/{repo}.git"
export MOARK_REMOTE_USERNAME=alice
export MOARK_REMOTE_PASSWORD=secret
moark-ingest --tar ./dist/project-....tar.gz --profile default
```

With artifact extraction:
```bash
moark-ingest \
  --tar ./dist/project-....tar.gz \
  --profile default \
  --artifacts-output-dir ./extracted-artifacts
```

## Repository Mapping Management

The system supports mapping external repository names to internal names for security and classification purposes.

### Mapping CLI

List all mappings:
```bash
moark-mapping list
moark-mapping list --profile team-alpha
```

Add mapping:
```bash
moark-mapping add external-repo-name internal/repo/path
moark-mapping add external-repo-name internal/repo/path --profile team-alpha --notes "Main app"
```

Remove mapping:
```bash
moark-mapping remove external-repo-name
moark-mapping remove external-repo-name --profile team-alpha
```

Validate configuration:
```bash
moark-mapping validate
moark-mapping validate --profile team-alpha
```

### Environment Variables

- `MOARK_CONFIG_DIR` - Configuration directory (default: `~/.moark`)
- `MOARK_REMOTE_TEMPLATE` - URL template for internal remote
- `MOARK_REMOTE_USERNAME` - Username for internal Git
- `MOARK_REMOTE_PASSWORD` - Password for internal Git

## Configuration Structure

```
~/.moark/
├── profiles.json           # Profile settings
├── mappings/
│   ├── default.json        # Mappings for default profile
│   ├── team-alpha.json     # Mappings for team alpha
│   └── team-beta.json      # Mappings for team beta
├── history.json            # Ingestion history
├── s3_settings.json        # S3 settings (endpoint, bucket, credentials)
├── mapping-dict.json       # Mapping dictionary downloaded from S3
└── backups/                # Automatic backups
```

## Mapping Dictionary

The system uses a mapping dictionary stored in S3 to convert external repository names (from the internet network) to internal names (in the air-gapped network).

### Dictionary File Structure

See example in `example-mapping-dict.json`:

```json
{
  "_description": "Repository name mapping dictionary",
  "_version": "1.0",
  "mappings": {
    "yossi": {
      "internal_repo": "project-alpha",
      "internal_url": "https://git.internal.company/security/project-alpha.git",
      "description": "Security project - classified",
      "team": "security-team",
      "classification": "secret"
    }
  }
}
```

### S3 Configuration

On first run, configure S3 details:
- **Endpoint URL**: S3 server address (e.g., `https://s3.internal.company`)
- **Bucket Name**: Bucket containing the dictionary file
- **Access Key / Secret Key**: Authentication credentials (optional if using IAM roles)

Settings are saved in `~/.moark/s3_settings.json` and loaded automatically on subsequent runs.

## Parameters

### Ingest Parameters

- `--tar`: Bundle file to transfer
- `--remote-template`: URL template for internal remote (or ENV: `MOARK_REMOTE_TEMPLATE`)
- `--username`, `--password`: Authentication credentials (or ENV: `MOARK_REMOTE_USERNAME`/`MOARK_REMOTE_PASSWORD`)
- `--profile`: Profile to use (default: `default`)
- `--mapping-config`: Configuration directory path (or ENV: `MOARK_CONFIG_DIR`)
- `--artifacts-output-dir`: Directory for extracting artifacts (optional)

### Mapping CLI Parameters

- `--profile`, `-p`: Profile name (default: `default`)
- `--config-dir`: Configuration directory (or ENV: `MOARK_CONFIG_DIR`)
- `--notes`, `-n`: Notes for mapping (in add command)
- `--force`, `-f`: Skip confirmation (in remove command)

## Note

This package is intended for developers in the internal (air-gapped) network. It uses a mapping dictionary to convert external repository names to internal names before uploading to internal Git.

## For Support

For support or questions, contact: **Moshe Eliya**
