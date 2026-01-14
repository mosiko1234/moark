# ⛵ Moses in the Ark

**Secure Air-Gap Transfer System for Git Repositories and CI/CD Artifacts**

Named after the biblical story of Moses being safely transferred in an ark, this system ensures secure code transfer across network boundaries between internet-connected and air-gapped environments.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [System Components](#system-components)
- [Security Features](#security-features)
- [Support](#support)

---

## 🎯 Overview

Moses in the Ark is a two-phase system designed to securely transfer Git repositories and CI/CD artifacts between:
- **External Network** (Internet-connected) - Pack phase
- **Internal Network** (Air-gapped) - Ingest phase

The system uses physical media (USB drives, disk-on-key) as the secure transfer mechanism, maintaining complete network isolation.

### Key Features

✅ **Physical Air-Gap** - No network connection between environments  
✅ **Smart Mapping** - Automatic repository name translation for security classification  
✅ **Full Git Support** - Repositories, submodules, and CI/CD artifacts  
✅ **Modern TUI** - Terminal-based user interface with real-time feedback  
✅ **CLI Support** - Complete command-line interface for automation  
✅ **S3 Integration** - Centralized mapping dictionary management  
✅ **Auto-Detection** - Automatic disk-on-key scanning  
✅ **Audit Trail** - Complete history tracking of all transfers  

---

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     INTERNET NETWORK                                │
│  ┌──────────────┐                                                   │
│  │  Developer   │                                                   │
│  │   Station    │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         │ Run moark-pack-ui                                         │
│         ▼                                                           │
│  ┌─────────────────────────────────────┐                          │
│  │    Moses in the Ark - Pack          │                          │
│  │  ┌──────────────────────────────┐   │                          │
│  │  │  • Clone Repository          │   │                          │
│  │  │  • Fetch Submodules          │   │                          │
│  │  │  │  (optional)                │   │                          │
│  │  │  • Download CI/CD Artifacts  │   │  ┌─────────────────┐   │
│  │  │  │  (optional)                │◄──┼──┤  GitLab API     │   │
│  │  │  • Create Git Bundle         │   │  └─────────────────┘   │
│  │  │  • Package Everything        │   │                          │
│  │  │  • Create Manifest           │   │  ┌─────────────────┐   │
│  │  └──────────┬───────────────────┘   │  │  Public GitHub  │   │
│  │             │                         │  │  GitLab.com     │   │
│  └─────────────┼─────────────────────────┘  └─────────────────┘   │
│                │                                                   │
│                │ Write to USB                                      │
│                ▼                                                   │
│       ┌────────────────┐                                          │
│       │ Disk-on-Key    │                                          │
│       │  Bundle.tar.gz │                                          │
│       └────────┬───────┘                                          │
└────────────────┼──────────────────────────────────────────────────┘
                 │
                 │ Physical Transfer
                 │
┌────────────────▼──────────────────────────────────────────────────┐
│                   AIR-GAPPED NETWORK                              │
│       ┌────────────────┐                                          │
│       │ Disk-on-Key    │                                          │
│       │  Bundle.tar.gz │                                          │
│       └────────┬───────┘                                          │
│                │                                                   │
│                │ Insert USB                                        │
│                ▼                                                   │
│  ┌──────────────┐                                                 │
│  │  Developer   │                                                 │
│  │   Station    │                                                 │
│  └──────┬───────┘                                                 │
│         │                                                         │
│         │ Run moark-ingest-ui                                     │
│         ▼                                                         │
│  ┌─────────────────────────────────────┐                        │
│  │   Moses in the Ark - Ingest         │                        │
│  │  ┌──────────────────────────────┐   │                        │
│  │  │  • Auto-scan USB Drive       │   │  ┌──────────────────┐ │
│  │  │  • Load Mapping Dictionary   │◄──┼──┤  S3 Storage      │ │
│  │  │  • Extract Bundle             │   │  │  (mapping-dict)  │ │
│  │  │  • Map External → Internal   │   │  └──────────────────┘ │
│  │  │  • Push to Internal GitLab   │   │                        │
│  │  │  • Extract Artifacts          │   │  ┌──────────────────┐ │
│  │  │  • Record History             │──►│  │  Internal GitLab │ │
│  │  └──────────────────────────────┘   │  └──────────────────┘ │
│  └─────────────────────────────────────┘                        │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
External Repo ──► Pack ──► Bundle ──► Physical Transfer ──► Ingest ──► Internal Repo
                   │                                          │
                   └─────── Metadata ──────────────► Mapping Dictionary
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git installed
- Terminal with Unicode support
- For ingest: Access to S3-compatible storage (for mapping dictionary)

### Installation & Usage

#### Pack (Internet Network)

```bash
# Install
cd moark-pack
pip install ".[ui]"

# Run TUI
moark-pack-ui

# Or use CLI
moark-pack pack --repo-url https://github.com/user/repo.git --output-dir ./dist
```

#### Ingest (Air-Gapped Network)

```bash
# Install
cd moark-ingest
pip install ".[ui]"

# Run TUI
moark-ingest-ui

# Or use CLI
moark-ingest --tar /path/to/bundle.tar.gz --remote-template "https://user:pass@git.internal/{repo}.git"
```

---

## 📚 Documentation

### Architecture & Design

- **[Architecture Documentation](docs/ARCHITECTURE.md)** - Complete system architecture, design decisions, and technical details
- **[Workflow Guide](docs/WORKFLOW.md)** - Step-by-step workflow and process flows

### Component Documentation

- **[Pack Documentation](moark-pack/DOCUMENTATION.md)** - Complete guide for the Pack component
- **[Ingest Documentation](moark-ingest/DOCUMENTATION.md)** - Complete guide for the Ingest component

### User Guides

- **[Pack README](moark-pack/README.md)** - Quick start guide for Pack
- **[Ingest README](moark-ingest/README.md)** - Quick start guide for Ingest
- **[Ingest Usage Guide](moark-ingest/USAGE_GUIDE.md)** - Detailed usage instructions

### Examples

- **[Mapping Dictionary Example](moark-ingest/example-mapping-dict.json)** - Sample mapping configuration

---

## 🔧 System Components

### 1. moark-pack (External Network)

**Purpose:** Create transferable bundles from Git repositories

**Key Features:**
- Clone from public/private Git repositories
- Support for GitLab authentication (username/password)
- Optional submodule inclusion
- Optional CI/CD artifact download
- Intelligent URL parsing
- Real-time progress feedback

**Commands:**
- `moark-pack` - CLI interface
- `moark-pack-ui` - Terminal UI interface

### 2. moark-ingest (Air-Gapped Network)

**Purpose:** Ingest bundles and upload to internal repositories

**Key Features:**
- S3-based mapping dictionary
- Auto-scan disk-on-key devices
- External → Internal name mapping
- Git credential management
- Upload history tracking
- Artifact extraction

**Commands:**
- `moark-ingest` - CLI interface
- `moark-ingest-ui` - Terminal UI interface
- `moark-mapping` - Mapping management CLI

---

## 🔐 Security Features

### Network Isolation
- ✅ Physical air-gap maintained at all times
- ✅ No network connection between environments
- ✅ USB-based transfer only

### Credential Management
- ✅ Passwords never stored or logged
- ✅ SSL verification enabled by default
- ✅ Credentials used only during operations
- ✅ Secure memory handling

### Access Control
- ✅ Classification-aware naming
- ✅ Mapping-based authorization
- ✅ Audit trail for all transfers
- ✅ User authentication required

### Data Integrity
- ✅ Git bundle verification
- ✅ Manifest validation
- ✅ Checksum verification
- ✅ Complete metadata tracking

---

## 💻 Platform Support

| Platform | Pack | Ingest | Auto-Scan |
|----------|------|--------|-----------|
| macOS    | ✅   | ✅     | ✅        |
| Linux    | ✅   | ✅     | ✅        |
| Windows  | ✅   | ✅     | ✅        |

---

## 🎨 Terminal UI Features

Both TUI applications include:
- Real-time output streaming
- Responsive layout (adapts to terminal size)
- Interactive tables (bundles, mappings, history)
- Color-coded status indicators
- Keyboard shortcuts
- Progress indicators
- Error handling and validation

---

## 📦 Directory Structure

```
airgap-git-relay/
├── README.md                          # This file
├── docs/
│   ├── ARCHITECTURE.md               # System architecture
│   └── WORKFLOW.md                   # Detailed workflows
├── moark-pack/                       # Pack component
│   ├── README.md                     # Pack quick start
│   ├── DOCUMENTATION.md              # Pack detailed docs
│   ├── pyproject.toml                # Pack package config
│   └── src/moark_pack/              # Pack source code
│       ├── __init__.py
│       ├── pack.py                   # CLI implementation
│       ├── pack_ui.py                # TUI implementation
│       ├── gitlab_client.py          # GitLab API client
│       └── utils.py                  # Utilities
└── moark-ingest/                     # Ingest component
    ├── README.md                     # Ingest quick start
    ├── DOCUMENTATION.md              # Ingest detailed docs
    ├── USAGE_GUIDE.md                # Detailed usage guide
    ├── example-mapping-dict.json     # Example mapping config
    ├── pyproject.toml                # Ingest package config
    └── src/moark_ingest/            # Ingest source code
        ├── __init__.py
        ├── ingest.py                 # CLI implementation
        ├── ingest_ui.py              # TUI implementation
        ├── config_manager.py         # Configuration management
        ├── history_manager.py        # History tracking
        ├── mapping_cli.py            # Mapping CLI
        ├── s3_client.py              # S3 integration
        ├── s3_settings.py            # S3 configuration
        ├── bundle_scanner.py         # USB scanning
        └── utils.py                  # Utilities
```

---

## 🤝 Contributing

This is a proprietary internal tool. For questions or support, contact the development team.

---

## 📞 Support

For support or questions, contact: **Moshe Eliya**

---

## 📖 Story Behind the Name

The name **"Moses in the Ark"** comes from the biblical story where baby Moses was placed in an ark (תיבה) and safely transferred through dangerous waters. 

Similarly, this system:
- 🎯 Safely transfers code "bundles" (like Moses in his ark)
- 🌊 Crosses the dangerous gap between networks (like the river)
- 🛡️ Protects the contents during transfer (like the ark protected Moses)
- 🎁 Delivers securely to the destination (like Moses reached safety)

Just as the ark protected Moses through his journey, **Moses in the Ark** protects your code during the air-gap transfer! ⛵✨

---

## 📄 License

Proprietary - Internal use only

---

**Made with ⛵ by the Security Infrastructure Team**
