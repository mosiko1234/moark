# Moses in the Ark - Deployment Guide

## 📦 Package Distribution

This repository contains two separate packages for secure Git repository transfer between internet-connected and air-gapped networks.

---

## 🌐 Package 1: moark-pack (Internet-Connected Network)

**File:** `moark-pack-offline-bundle.tar.gz` (3.3 MB)

### Purpose
Create bundled Git repositories with optional CI/CD artifacts from external sources (GitLab, GitHub, etc.)

### Target Users
Developers working on internet-connected machines who need to package repositories for transfer to air-gapped networks.

### Installation Location
Install on each developer's workstation that has internet access.

### Bundle Contents
- `moark-pack/` - Source code
- `wheels/` - 21 Python dependencies
- `INSTALL.txt` - Installation instructions

### Quick Start
```bash
# Extract
tar -xzf moark-pack-offline-bundle.tar.gz
cd moark-pack-offline-bundle

# Install dependencies
pip install --no-index --find-links=wheels wheels/*.whl

# Install package
cd moark-pack
pip install -e ".[ui]"

# Launch UI
moark-pack-ui
```

### Available Commands
- `moark-pack` - CLI for creating bundles
- `moark-pack-ui` - Terminal UI (TUI)

### Typical Workflow
1. Developer launches `moark-pack-ui`
2. Enters repository URL and credentials
3. Clicks "Pack" to create bundle
4. Bundle is saved to `./dist/` directory
5. Copies bundle to disk-on-key/USB drive
6. Physically transfers drive to air-gapped network

---

## 🔒 Package 2: moark-ingest (Air-Gapped Network)

**File:** `moark-ingest-offline-bundle.tar.gz` (17 MB)

### Purpose
Load bundled Git repositories from external sources into internal air-gapped Git repositories using a mapping dictionary.

### Target Users
Developers working on air-gapped machines who need to import repositories from external sources.

### Installation Location
Install on each developer's workstation in the air-gapped network.

### Bundle Contents
- `moark-ingest/` - Source code
- `wheels/` - 20 Python dependencies (including boto3 for S3)
- `INSTALL.txt` - Installation instructions
- `example-mapping-dict.json` - Example mapping configuration

### Quick Start
```bash
# Extract
tar -xzf moark-ingest-offline-bundle.tar.gz
cd moark-ingest-offline-bundle

# Install dependencies
pip install --no-index --find-links=wheels wheels/*.whl

# Install package
cd moark-ingest
pip install -e ".[ui]"

# Launch UI
moark-ingest-ui
```

### Available Commands
- `moark-ingest` - CLI for loading bundles
- `moark-ingest-ui` - Terminal UI (TUI)
- `moark-mapping` - Manage repository mappings

### Typical Workflow
1. Developer launches `moark-ingest-ui`
2. Configures S3 settings (first time only)
3. Downloads mapping dictionary from S3
4. Inserts disk-on-key/USB drive with bundle
5. Scans for available bundles
6. Selects bundle to ingest
7. Enters Git credentials
8. Clicks "Upload Bundle" to push to internal repository

---

## 🗺️ Mapping Dictionary

The mapping dictionary is a JSON file that maps external repository names to internal, security-classified repository names.

### Example Structure
```json
{
  "version": "1.0",
  "mappings": {
    "external-project-name": {
      "internal_repo": "classified-alpha",
      "internal_url": "https://git.internal/classified-alpha.git",
      "description": "Production system"
    }
  }
}
```

### Storage
- Stored in S3 bucket (accessible from air-gapped network)
- Updated by security/DevOps team
- Downloaded automatically by `moark-ingest`

### Management
```bash
# List all mappings
moark-mapping list

# Add a new mapping
moark-mapping add

# Remove a mapping
moark-mapping remove

# Validate configuration
moark-mapping validate
```

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERNET-CONNECTED NETWORK                       │
│                                                                     │
│  Developer's Workstation                                           │
│  ┌──────────────────┐                                              │
│  │  moark-pack-ui   │                                              │
│  │                  │                                              │
│  │  1. Enter URL    │                                              │
│  │  2. Enter creds  │                                              │
│  │  3. Click Pack   │                                              │
│  └─────────┬────────┘                                              │
│            │                                                        │
│            v                                                        │
│  ┌──────────────────┐                                              │
│  │  Bundle Created  │                                              │
│  │  repo-*.tar.gz   │                                              │
│  └─────────┬────────┘                                              │
└────────────┼───────────────────────────────────────────────────────┘
             │
             │  Physical Transfer
             │  (USB Drive)
             │
┌────────────▼───────────────────────────────────────────────────────┐
│                       AIR-GAPPED NETWORK                           │
│                                                                     │
│  Developer's Workstation                                           │
│  ┌──────────────────┐                                              │
│  │ moark-ingest-ui  │                                              │
│  │                  │                                              │
│  │  1. Scan USB     │                                              │
│  │  2. Select bundle│                                              │
│  │  3. Enter creds  │                                              │
│  │  4. Upload       │                                              │
│  └─────────┬────────┘                                              │
│            │                                                        │
│            v                                                        │
│  ┌──────────────────┐      ┌─────────────────┐                    │
│  │  Mapping Dict    │◄─────┤  S3 Bucket      │                    │
│  │  (from S3)       │      │  (Internal)     │                    │
│  └─────────┬────────┘      └─────────────────┘                    │
│            │                                                        │
│            v                                                        │
│  ┌──────────────────┐                                              │
│  │  Internal Git    │                                              │
│  │  Repository      │                                              │
│  └──────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Pre-Deployment Checklist

### For Internet-Connected Network (moark-pack)
- [ ] Python 3.10+ installed
- [ ] Git installed
- [ ] Access to external GitLab/GitHub
- [ ] USB drives/disk-on-keys available for transfer

### For Air-Gapped Network (moark-ingest)
- [ ] Python 3.10+ installed
- [ ] Git installed
- [ ] Internal S3 accessible
- [ ] Mapping dictionary uploaded to S3
- [ ] Internal Git repositories created
- [ ] Developer credentials provisioned

---

## 🔐 Security Considerations

### moark-pack
- Credentials are never stored permanently
- Supports `--insecure` flag for self-signed certificates
- Can use Personal Access Tokens instead of passwords

### moark-ingest
- S3 credentials saved locally in `~/.moark/s3_settings.json`
- Mapping dictionary prevents accidental disclosure of classified names
- All operations logged to `~/.moark/history.json`

---

## 📞 Support

For support or questions, contact: **Moshe Eliya**

---

## 📄 Additional Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Workflow Details](docs/WORKFLOW.md)
- [moark-pack Documentation](moark-pack/README.md)
- [moark-ingest Documentation](moark-ingest/README.md)
- [moark-ingest Usage Guide](moark-ingest/USAGE_GUIDE.md)

---

**Moses in the Ark** - Secure Git Repository Transfer for Air-Gapped Networks  
Version: 0.1.0


