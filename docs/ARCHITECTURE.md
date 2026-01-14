# Moses in the Ark - System Architecture

**Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Development Team  

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [Security Architecture](#security-architecture)
6. [Technology Stack](#technology-stack)
7. [Design Decisions](#design-decisions)
8. [Deployment Architecture](#deployment-architecture)

---

## 1. Overview

### 1.1 Purpose

Moses in the Ark is a secure air-gap transfer system designed to safely move Git repositories and CI/CD artifacts between internet-connected and air-gapped networks while maintaining:
- Complete network isolation
- Security classification compliance
- Full audit trail
- Data integrity

### 1.2 Architecture Principles

1. **Physical Air-Gap:** No network connection between environments
2. **Separation of Concerns:** Independent pack and ingest components
3. **Security First:** Classification-aware, credential-safe design
4. **User-Friendly:** Terminal UI for ease of use
5. **Automation-Ready:** Complete CLI support
6. **Auditability:** Full history and logging

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL ENVIRONMENT                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Internet-Connected Network                     │ │
│  │                                                                   │ │
│  │  ┌─────────────┐         ┌──────────────┐    ┌───────────────┐  │ │
│  │  │             │         │              │    │               │  │ │
│  │  │  Developer  │────────►│  moark-pack  │───►│  Bundle File  │  │ │
│  │  │   Workstation│         │              │    │   .tar.gz     │  │ │
│  │  │             │         │              │    │               │  │ │
│  │  └─────────────┘         └──────┬───────┘    └───────┬───────┘  │ │
│  │                                  │                    │          │ │
│  │                                  │                    │          │ │
│  │                         ┌────────▼────────┐           │          │ │
│  │                         │  External Data  │           │          │ │
│  │                         │   Sources:      │           │          │ │
│  │                         │  • GitLab       │           │          │ │
│  │                         │  • GitHub       │           │          │ │
│  │                         │  • BitBucket    │           │          │ │
│  │                         └─────────────────┘           │          │ │
│  └───────────────────────────────────────────────────────┼──────────┘ │
└────────────────────────────────────────────────────────────┼───────────┘
                                                             │
                      ┌──────────────────────────────────────┘
                      │
                      │ Physical Transfer
                      │ (USB Drive / Disk-on-Key)
                      │
                      │
┌─────────────────────▼──────────────────────────────────────────────────┐
│                       INTERNAL ENVIRONMENT                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    Air-Gapped Network                             │ │
│  │                                                                   │ │
│  │  ┌───────────────┐    ┌────────────────┐    ┌─────────────────┐ │ │
│  │  │               │    │                │    │                 │ │ │
│  │  │  Bundle File  │───►│  moark-ingest  │───►│  Internal Git   │ │ │
│  │  │   .tar.gz     │    │                │    │   Repository    │ │ │
│  │  │               │    │                │    │                 │ │ │
│  │  └───────────────┘    └────────┬───────┘    └─────────────────┘ │ │
│  │                                 │                                │ │
│  │                        ┌────────▼─────────┐                      │ │
│  │                        │  Internal Data   │                      │ │
│  │                        │   Sources:       │                      │ │
│  │                        │  • S3 Storage    │                      │ │
│  │                        │  • Config Files  │                      │ │
│  │                        │  • History DB    │                      │ │
│  │                        └──────────────────┘                      │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Diagram

```
┌────────────────┐
│                │
│   Developer    │
│                │
└───────┬────────┘
        │
        │ 1. Initiates Pack
        │
        ▼
┌────────────────────────────────────────────────┐
│           moark-pack Component                 │
│  ┌──────────────────────────────────────────┐ │
│  │  pack_ui.py (TUI) / pack.py (CLI)       │ │
│  │              │                            │ │
│  │              ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  gitlab_client.py    │               │ │
│  │  │   • Authenticate     │               │ │
│  │  │   • Fetch Metadata   │               │ │
│  │  │   • Download Artifacts│              │ │
│  │  └──────────┬───────────┘               │ │
│  │             │                            │ │
│  │             ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  Git Operations      │               │ │
│  │  │   • Clone            │               │ │
│  │  │   • Bundle           │               │ │
│  │  │   • Submodules       │               │ │
│  │  └──────────┬───────────┘               │ │
│  │             │                            │ │
│  │             ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  Package & Compress  │               │ │
│  │  │   • Create Manifest  │               │ │
│  │  │   • Add Artifacts    │               │ │
│  │  │   • Compress to .tar.gz│            │ │
│  │  └──────────┬───────────┘               │ │
│  └─────────────┼────────────────────────────┘ │
└────────────────┼─────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │  Bundle File   │
        │   .tar.gz      │
        └───────┬────────┘
                │
                │ Physical Transfer
                │
                ▼
        ┌────────────────┐
        │  USB Device    │
        └───────┬────────┘
                │
                │ 2. Transfer to Air-Gap
                │
                ▼
┌────────────────────────────────────────────────┐
│         moark-ingest Component                 │
│  ┌──────────────────────────────────────────┐ │
│  │  ingest_ui.py (TUI) / ingest.py (CLI)   │ │
│  │              │                            │ │
│  │              ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  s3_client.py        │               │ │
│  │  │   • Download Mapping │               │ │
│  │  │   • Validate Config  │               │ │
│  │  └──────────┬───────────┘               │ │
│  │             │                            │ │
│  │             ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  bundle_scanner.py   │               │ │
│  │  │   • Detect USB       │               │ │
│  │  │   • Scan Bundles     │               │ │
│  │  │   • Extract Metadata │               │ │
│  │  └──────────┬───────────┘               │ │
│  │             │                            │ │
│  │             ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  Mapping & Validation│               │ │
│  │  │   • Lookup Internal  │               │ │
│  │  │   • Verify Access    │               │ │
│  │  └──────────┬───────────┘               │ │
│  │             │                            │ │
│  │             ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  Git Operations      │               │ │
│  │  │   • Extract Bundle   │               │ │
│  │  │   • Push to Internal │               │ │
│  │  └──────────┬───────────┘               │ │
│  │             │                            │ │
│  │             ▼                            │ │
│  │  ┌──────────────────────┐               │ │
│  │  │  history_manager.py  │               │ │
│  │  │   • Record Transfer  │               │ │
│  │  │   • Update Audit     │               │ │
│  │  └──────────────────────┘               │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

---

## 3. Component Design

### 3.1 moark-pack (External Network Component)

#### Purpose
Create portable bundles from Git repositories for air-gap transfer.

#### Core Modules

**pack.py** - Main CLI Interface
```
Responsibilities:
  • Command-line argument parsing
  • Parameter validation
  • Orchestrate packing process
  • Error handling and reporting

Key Functions:
  • pack() - Main entry point
  • validate_inputs() - Input validation
  • create_manifest() - Generate metadata
```

**pack_ui.py** - Terminal User Interface
```
Responsibilities:
  • Interactive TUI using Textual
  • Real-time progress feedback
  • Form validation
  • Async command execution

Components:
  • PackTUI App class
  • Input forms
  • Log display
  • Progress indicators
```

**gitlab_client.py** - GitLab Integration
```
Responsibilities:
  • GitLab API authentication
  • Repository metadata fetching
  • Artifact download
  • URL construction

Classes:
  • GitLabConfig - Configuration
  • GitLabClient - API client
```

**utils.py** - Utility Functions
```
Functions:
  • parse_gitlab_url() - URL parsing
  • run_command() - Shell execution
  • validate_url() - URL validation
```

#### Data Structures

**Bundle Structure:**
```
bundle-name.tar.gz
├── manifest.json           # Metadata
├── repo.bundle             # Git bundle
├── submodules/             # Submodules (optional)
│   └── submodule.bundle
└── artifacts/              # CI/CD artifacts (optional)
    ├── job1/
    └── job2/
```

**Manifest Format:**
```json
{
  "version": "1.0",
  "repo_name": "project-name",
  "repo_url": "https://gitlab.com/group/project.git",
  "packed_at": "2024-12-31T10:00:00Z",
  "packed_by": "user@example.com",
  "git_ref": "main",
  "has_submodules": true,
  "submodules": ["path/to/submodule"],
  "has_artifacts": true,
  "artifacts": [
    {
      "job_name": "build",
      "job_id": 12345,
      "ref": "main"
    }
  ],
  "checksum": "sha256:..."
}
```

### 3.2 moark-ingest (Internal Network Component)

#### Purpose
Ingest bundles and upload to internal Git repositories with mapping support.

#### Core Modules

**ingest.py** - Main CLI Interface
```
Responsibilities:
  • Bundle extraction
  • Git operations
  • Remote configuration
  • Artifact handling

Key Functions:
  • ingest() - Main entry point
  • extract_bundle() - Unpack archive
  • push_to_remote() - Git push
```

**ingest_ui.py** - Terminal User Interface
```
Responsibilities:
  • S3 configuration interface
  • Bundle scanning interface
  • Mapping table display
  • Upload orchestration

Components:
  • IngestTUI App class
  • S3 configuration form
  • Bundle selection table
  • Mapping display table
  • History table
```

**s3_client.py** - S3 Integration
```
Responsibilities:
  • S3 connection management
  • Mapping dictionary download
  • Configuration validation

Classes:
  • S3Client - Main client
  
Functions:
  • download_mapping_dict()
  • test_connection()
```

**s3_settings.py** - S3 Configuration
```
Responsibilities:
  • Settings persistence
  • Configuration validation

Classes:
  • S3Settings - Settings manager
```

**bundle_scanner.py** - USB Detection
```
Responsibilities:
  • Detect USB devices
  • Scan for bundles
  • Extract bundle metadata

Classes:
  • BundleInfo - Bundle metadata

Functions:
  • auto_scan_for_bundles()
  • scan_bundles()
  • find_disk_on_key_paths()
```

**config_manager.py** - Configuration Management
```
Responsibilities:
  • Profile management
  • Configuration persistence

Classes:
  • ConfigManager - Main manager
  • Profile - Configuration profile
```

**history_manager.py** - History Tracking
```
Responsibilities:
  • Transfer history
  • Audit trail
  • Query interface

Classes:
  • HistoryManager - History tracking
  • HistoryEntry - Single entry
```

**mapping_cli.py** - Mapping Management
```
Responsibilities:
  • Mapping CRUD operations
  • Validation
  • CLI interface

Functions:
  • list_mappings()
  • add_mapping()
  • remove_mapping()
  • validate_config()
```

#### Data Structures

**Mapping Dictionary:**
```json
{
  "_description": "Repository mapping dictionary",
  "_version": "1.0",
  "_last_updated": "2024-12-31T10:00:00Z",
  "mappings": {
    "external-name": {
      "internal_repo": "internal-name",
      "internal_url": "https://git.internal/project.git",
      "description": "Project description",
      "team": "team-name",
      "classification": "secret"
    }
  }
}
```

**History Entry:**
```json
{
  "timestamp": "2024-12-31T10:00:00Z",
  "bundle_name": "project-20241231.tar.gz",
  "source_repo": "external-name",
  "target_repo": "internal-name",
  "profile": "default",
  "user": "user@example.com",
  "status": "success",
  "artifacts_count": 5,
  "error_message": null
}
```

---

## 4. Data Flow

### 4.1 Pack Flow

```
1. User Input
   └─► Validate inputs
       └─► Check repository accessibility
           └─► Authenticate (if needed)
               └─► Clone repository
                   └─► Fetch submodules (optional)
                       └─► Download artifacts (optional)
                           └─► Create Git bundle
                               └─► Generate manifest
                                   └─► Package all files
                                       └─► Compress to .tar.gz
                                           └─► Output bundle file
```

### 4.2 Ingest Flow

```
1. Configure S3 (first time)
   └─► Download mapping dictionary
       └─► Save locally
           
2. Scan for bundles
   └─► Detect USB devices
       └─► Find .tar.gz files
           └─► Extract metadata
               └─► Display in table

3. Select bundle
   └─► Lookup mapping
       └─► Validate access
           └─► Request credentials
               └─► Extract bundle
                   └─► Configure Git remote
                       └─► Push to internal GitLab
                           └─► Extract artifacts (optional)
                               └─► Record history
```

### 4.3 State Diagram

```
Pack States:
  IDLE ──► VALIDATING ──► CLONING ──► BUNDLING ──► COMPRESSING ──► COMPLETE
    │                         │            │             │             │
    └─────────────────────────┴────────────┴─────────────┴────► ERROR

Ingest States:
  IDLE ──► S3_CONFIG ──► SCANNING ──► SELECTED ──► UPLOADING ──► COMPLETE
    │          │            │            │             │            │
    └──────────┴────────────┴────────────┴─────────────┴────► ERROR
```

---

## 5. Security Architecture

### 5.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                   Physical Security Layer                    │
│  • Air-gap enforcement                                      │
│  • USB-only transfer                                         │
│  • No network bridging                                      │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                Authentication & Authorization                │
│  • User authentication (Git credentials)                    │
│  • Mapping-based authorization                              │
│  • Classification verification                              │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Data Security Layer                       │
│  • Credential non-persistence                               │
│  • SSL/TLS verification                                     │
│  • Secure memory handling                                   │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Audit & Compliance                        │
│  • Complete history logging                                 │
│  • Transfer tracking                                        │
│  • Classification enforcement                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Security Controls

**Pack Component:**
- Credential input validation
- SSL certificate verification
- No credential storage
- Secure API token handling

**Ingest Component:**
- Mapping dictionary validation
- Classification enforcement
- Access control verification
- Complete audit trail

**Transport:**
- Physical media only
- No network transmission
- Encrypted storage support (OS-level)

---

## 6. Technology Stack

### 6.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10+ | Primary language |
| CLI Framework | Typer | 0.9+ | Command-line interface |
| TUI Framework | Textual | 0.40+ | Terminal user interface |
| HTTP Client | Requests | 2.31+ | API communication |
| Git | GitPython | 3.1+ | Git operations |
| S3 | Boto3 | 1.28+ | S3 integration |
| Build System | Hatchling | Latest | Package building |

### 6.2 Dependencies

**Pack Dependencies:**
- typer - CLI framework
- requests - HTTP client
- gitpython - Git operations
- textual - Terminal UI

**Ingest Dependencies:**
- typer - CLI framework
- boto3 - S3 client
- textual - Terminal UI

---

## 7. Design Decisions

### 7.1 Key Architectural Decisions

**Decision 1: Physical Air-Gap**
- **Rationale:** Security requirement, complete network isolation
- **Trade-offs:** Manual transfer required, potential for human error
- **Mitigation:** Auto-scanning, validation, audit trail

**Decision 2: Two Independent Components**
- **Rationale:** Separation of concerns, independent deployment
- **Trade-offs:** Code duplication, separate maintenance
- **Benefits:** Clear boundaries, easier security review

**Decision 3: S3-Based Mapping**
- **Rationale:** Centralized configuration, easy updates
- **Trade-offs:** Requires S3 access in air-gap
- **Benefits:** Single source of truth, version control

**Decision 4: Terminal UI (not Web)**
- **Rationale:** No additional server, simpler deployment
- **Trade-offs:** Less familiar interface
- **Benefits:** Lightweight, no port conflicts, scriptable

**Decision 5: Username/Password Authentication**
- **Rationale:** User-specific credentials, better audit
- **Trade-offs:** More user input required
- **Benefits:** Individual accountability, no shared tokens

### 7.2 Alternative Approaches Considered

**Network-Based Transfer:**
- Rejected: Violates air-gap requirement
- Alternative: Current physical transfer

**Single Monolithic Tool:**
- Rejected: Violates separation of environments
- Alternative: Two independent components

**Token-Based Authentication:**
- Rejected: Shared secrets, poor audit trail
- Alternative: Username/password per user

**Web UI:**
- Rejected: Additional complexity, port management
- Alternative: Terminal UI

---

## 8. Deployment Architecture

### 8.1 Installation Model

**Pack (External Network):**
```
Developer Workstation
  ├── Python 3.10+
  ├── Git
  ├── pip install moark-pack[ui]
  └── Configuration: None required
```

**Ingest (Air-Gapped Network):**
```
Developer Workstation
  ├── Python 3.10+
  ├── Git
  ├── pip install moark-ingest[ui]
  └── Configuration:
      ├── S3 endpoint (first run)
      ├── S3 credentials (first run)
      └── ~/.moark/
          ├── s3_settings.json
          ├── mapping-dict.json
          └── history.json
```

### 8.2 Configuration Management

**Pack Configuration:**
- No persistent configuration required
- All parameters per-run

**Ingest Configuration:**
```
~/.moark/
├── s3_settings.json          # S3 connection details
├── mapping-dict.json         # Downloaded from S3
├── history.json              # Transfer history
├── profiles.json             # User profiles (optional)
└── mappings/                 # Manual mappings (optional)
    └── default.json
```

---

## 9. Error Handling & Recovery

### 9.1 Pack Error Scenarios

| Error | Detection | Recovery |
|-------|-----------|----------|
| Network failure | HTTP timeout | Retry with backoff |
| Authentication failure | API 401 | Request credentials |
| Git clone failure | Exit code != 0 | Clean workspace, retry |
| Insufficient disk space | OS error | Alert user, cleanup |
| Invalid URL | Parse error | Request valid input |

### 9.2 Ingest Error Scenarios

| Error | Detection | Recovery |
|-------|-----------|----------|
| S3 connection failure | Boto3 exception | Check configuration |
| No mapping found | Dictionary lookup | Alert user |
| Git push failure | Exit code != 0 | Check credentials |
| Bundle corruption | Manifest validation | Reject bundle |
| USB not detected | No device found | Manual path entry |

---

## 10. Performance Considerations

### 10.1 Pack Performance

- **Git Clone:** Depends on repo size and network
- **Bundle Creation:** Fast, local operation
- **Compression:** CPU-bound, ~1-5 minutes for large repos
- **Artifacts Download:** Network-bound

### 10.2 Ingest Performance

- **S3 Download:** Network-bound, one-time per session
- **Bundle Extraction:** I/O-bound, ~30 seconds
- **Git Push:** Network-bound, depends on internal network
- **USB Scanning:** I/O-bound, <1 second

---

## 11. Future Enhancements

### 11.1 Planned Features

- [ ] Bundle signing and verification
- [ ] Incremental bundle updates
- [ ] Multiple bundle queuing
- [ ] Advanced filtering and search
- [ ] Graphical UI option
- [ ] Windows native packaging

### 11.2 Under Consideration

- [ ] Encryption at rest
- [ ] Multi-destination support
- [ ] Automated testing framework
- [ ] Plugin system for custom workflows

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Maintained By:** Development Team


