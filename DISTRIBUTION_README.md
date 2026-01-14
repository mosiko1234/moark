# Moses in the Ark - Distribution Packages

## 📦 Available Packages

This directory contains offline installation bundles for the **Moses in the Ark** system.

### Package Files

| File | Size | Purpose | Target Network |
|------|------|---------|----------------|
| `moark-pack-offline-bundle.tar.gz` | 3.3 MB | Create Git bundles | Internet-Connected |
| `moark-ingest-offline-bundle.tar.gz` | 17 MB | Load Git bundles | Air-Gapped |
| `DEPLOYMENT_GUIDE.md` | 9.3 KB | Deployment instructions | Both |
| `CHECKSUMS.txt` | - | SHA256 checksums | - |

---

## 🚀 Quick Start

### For Developers on Internet-Connected Network

```bash
# Extract the pack bundle
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

### For Developers on Air-Gapped Network

```bash
# Extract the ingest bundle
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

---

## ✅ Verify Package Integrity

Before installation, verify the packages haven't been corrupted:

```bash
shasum -a 256 -c CHECKSUMS.txt
```

Expected output:
```
moark-ingest-offline-bundle.tar.gz: OK
moark-pack-offline-bundle.tar.gz: OK
```

---

## 📋 What's Inside Each Bundle?

### moark-pack-offline-bundle.tar.gz
```
moark-pack-offline-bundle/
├── INSTALL.txt                 # Installation instructions
├── moark-pack/                 # Source code
│   ├── pyproject.toml
│   ├── README.md
│   ├── requirements.txt
│   └── src/moark_pack/
│       ├── __init__.py
│       ├── pack.py             # Main CLI
│       ├── pack_ui.py          # Terminal UI
│       ├── gitlab_client.py
│       └── utils.py
└── wheels/                     # 21 Python packages
    ├── textual-7.0.0-py3-none-any.whl
    ├── typer-0.21.1-py3-none-any.whl
    ├── gitpython-3.1.46-py3-none-any.whl
    ├── requests-2.32.5-py3-none-any.whl
    └── ... (17 more)
```

### moark-ingest-offline-bundle.tar.gz
```
moark-ingest-offline-bundle/
├── INSTALL.txt                 # Installation instructions
├── moark-ingest/               # Source code
│   ├── pyproject.toml
│   ├── README.md
│   ├── USAGE_GUIDE.md
│   ├── DOCUMENTATION.md
│   ├── requirements.txt
│   ├── example-mapping-dict.json
│   └── src/moark_ingest/
│       ├── __init__.py
│       ├── ingest.py           # Main CLI
│       ├── ingest_ui.py        # Terminal UI
│       ├── mapping_cli.py      # Mapping management
│       ├── config_manager.py
│       ├── history_manager.py
│       ├── s3_client.py
│       ├── s3_settings.py
│       ├── bundle_scanner.py
│       └── utils.py
└── wheels/                     # 20 Python packages
    ├── textual-7.0.0-py3-none-any.whl
    ├── typer-0.21.1-py3-none-any.whl
    ├── boto3-1.42.22-py3-none-any.whl
    ├── botocore-1.42.22-py3-none-any.whl
    └── ... (16 more)
```

---

## 🔧 System Requirements

### Both Packages
- **Python:** 3.10 or higher
- **pip:** Latest version recommended
- **Git:** 2.20 or higher
- **OS:** macOS, Linux, or Windows

### moark-pack (Internet)
- Internet connection for accessing GitLab/GitHub
- Minimum 100 MB free disk space

### moark-ingest (Air-Gapped)
- Access to internal S3 bucket
- Access to internal Git repositories
- Minimum 1 GB free disk space (for bundle extraction)

---

## 🔄 Typical Workflow

### Step 1: On Internet-Connected Network (moark-pack)

1. Install `moark-pack` on developer workstation
2. Launch `moark-pack-ui`
3. Enter repository URL and credentials
4. Click "Pack" to create bundle
5. Bundle saved to `./dist/repo-name-TIMESTAMP.tar.gz`
6. Copy bundle to USB drive

### Step 2: Physical Transfer

1. Safely eject USB drive
2. Transport to air-gapped network facility
3. Follow security protocols for media transfer

### Step 3: On Air-Gapped Network (moark-ingest)

1. Install `moark-ingest` on developer workstation
2. Launch `moark-ingest-ui`
3. Configure S3 settings (first time only)
4. Download mapping dictionary
5. Insert USB drive with bundle
6. Scan for bundles
7. Select bundle and enter Git credentials
8. Click "Upload Bundle"
9. Repository pushed to internal Git

---

## 📚 Documentation

Full documentation available in:

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[docs/WORKFLOW.md](docs/WORKFLOW.md)** - Detailed workflows
- **[moark-pack/README.md](moark-pack/README.md)** - Pack tool documentation
- **[moark-ingest/README.md](moark-ingest/README.md)** - Ingest tool documentation
- **[moark-ingest/USAGE_GUIDE.md](moark-ingest/USAGE_GUIDE.md)** - Step-by-step guide

---

## 🔐 Security Notes

### Credentials
- Never store credentials in scripts or configuration files
- Use Personal Access Tokens for GitLab authentication
- Rotate credentials regularly

### Mapping Dictionary
- Maps external repository names to internal classified names
- Managed by security/DevOps team
- Stored in internal S3 bucket

### Bundle Transfer
- Scan bundles for malware before ingestion
- Verify checksums after transfer
- Follow organizational security protocols

---

## 🆘 Troubleshooting

### Installation Issues

**Problem:** `command not found: moark-pack`  
**Solution:** Ensure pip's bin directory is in PATH, or use: `python3 -m moark_pack.pack --help`

**Problem:** `ModuleNotFoundError: No module named 'textual'`  
**Solution:** Install UI dependencies: `pip install textual>=0.40.0`

### Runtime Issues

**Problem:** SSL certificate verification failed  
**Solution:** Use `--insecure` flag or check "Disable SSL Verification" in UI

**Problem:** HTTP Basic: Access denied  
**Solution:** Use Personal Access Token instead of password

**Problem:** No mapping found for repository  
**Solution:** Download latest mapping dictionary from S3

---

## 📊 Package Statistics

### moark-pack Dependencies (21 packages)
- Core: typer, requests, gitpython
- UI: textual, rich, pygments
- Total wheel size: ~3 MB

### moark-ingest Dependencies (20 packages)
- Core: typer, boto3
- UI: textual, rich, pygments
- S3: botocore, s3transfer
- Total wheel size: ~16 MB

---

## 📞 Support

For support or questions, contact: **Moshe Eliya**

---

## 📝 Version Information

- **System:** Moses in the Ark (Moark)
- **Version:** 0.1.0
- **Release Date:** January 2026
- **Python:** 3.10+

---

## 🎯 Next Steps

1. **Read:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. **Install:** Follow instructions in bundle's `INSTALL.txt`
3. **Configure:** Set up S3 for air-gapped network (ingest only)
4. **Test:** Try packing and ingesting a test repository
5. **Deploy:** Roll out to development teams

---

**Moses in the Ark** - Secure Git Repository Transfer for Air-Gapped Networks  
⛵ Biblical name, modern security


