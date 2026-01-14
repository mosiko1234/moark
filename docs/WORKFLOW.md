# Moses in the Ark - Workflow Guide

**Complete End-to-End Workflows and Process Flows**

---

## Table of Contents

1. [Overview](#overview)
2. [Pack Workflow (External Network)](#pack-workflow-external-network)
3. [Transfer Process](#transfer-process)
4. [Ingest Workflow (Air-Gapped Network)](#ingest-workflow-air-gapped-network)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting Workflows](#troubleshooting-workflows)

---

## 1. Overview

This document describes the complete end-to-end workflows for Moses in the Ark system, from creating a bundle in the external network to ingesting it in the air-gapped network.

### 1.1 System Phases

```
Phase 1: PACK          Phase 2: TRANSFER          Phase 3: INGEST
(External Network)     (Physical)                 (Air-Gapped Network)

┌──────────────┐      ┌──────────────┐          ┌──────────────┐
│              │      │              │          │              │
│  Create      │─────►│  Physical    │─────────►│  Upload to   │
│  Bundle      │      │  Transfer    │          │  Internal    │
│              │      │  via USB     │          │  GitLab      │
└──────────────┘      └──────────────┘          └──────────────┘
```

---

## 2. Pack Workflow (External Network)

### 2.1 Complete Pack Flow Diagram

```
START
  │
  ▼
┌─────────────────────────────────────────┐
│  Step 1: Launch moark-pack-ui           │
│  Command: moark-pack-ui                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 2: Enter Repository Information   │
│  ┌────────────────────────────────────┐ │
│  │ Repository URL:                    │ │
│  │ • Public: github.com/user/repo     │ │
│  │ • Private: gitlab.company/grp/repo │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 3: Authentication (if private)    │
│  ┌────────────────────────────────────┐ │
│  │ Username: [developer-username]     │ │
│  │ Password: [****************]       │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 4: Configuration Options          │
│  ┌────────────────────────────────────┐ │
│  │ ☑ Include Submodules               │ │
│  │ ☑ Download Artifacts               │ │
│  │   └─ Ref: main                     │ │
│  │ ☐ Disable SSL Verification         │ │
│  │ Output Dir: ./dist                 │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 5: Click "Pack" Button            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  System Processing:                     │
│  ┌────────────────────────────────────┐ │
│  │ 1. Validate inputs                 │ │
│  │    └─► Check URL format            │ │
│  │    └─► Test authentication         │ │
│  │                                    │ │
│  │ 2. Clone repository                │ │
│  │    └─► Display progress            │ │
│  │    └─► Handle large repos          │ │
│  │                                    │ │
│  │ 3. Process submodules (if enabled) │ │
│  │    └─► Clone each submodule        │ │
│  │    └─► Create submodule bundles    │ │
│  │                                    │ │
│  │ 4. Download artifacts (if enabled) │ │
│  │    └─► Query GitLab API            │ │
│  │    └─► Download artifact archives  │ │
│  │    └─► Extract to artifacts/       │ │
│  │                                    │ │
│  │ 5. Create Git bundle               │ │
│  │    └─► git bundle create           │ │
│  │    └─► Include all refs            │ │
│  │                                    │ │
│  │ 6. Generate manifest               │ │
│  │    └─► Create manifest.json        │ │
│  │    └─► Add metadata                │ │
│  │    └─► Calculate checksum          │ │
│  │                                    │ │
│  │ 7. Package files                   │ │
│  │    └─► Create directory structure  │ │
│  │    └─► Copy all files              │ │
│  │                                    │ │
│  │ 8. Compress to .tar.gz             │ │
│  │    └─► Compress with gzip          │ │
│  │    └─► Name: project-TIMESTAMP.gz  │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 6: Completion                     │
│  ┌────────────────────────────────────┐ │
│  │ ✅ Bundle created successfully!    │ │
│  │                                    │ │
│  │ Output: ./dist/project-20241231-   │ │
│  │         143022.tar.gz              │ │
│  │ Size: 125.4 MB                     │ │
│  │                                    │ │
│  │ Next: Copy to USB drive            │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
  │
  ▼
END
```

### 2.2 Detailed Step-by-Step Process

#### Step 2.2.1: Repository URL Processing

```
Input URL
  │
  ├─► Is it a well-known public domain?
  │   (github.com, gitlab.com, bitbucket.org)
  │   │
  │   ├─► YES: Treat as public repository
  │   │   └─► No authentication required
  │   │
  │   └─► NO: Try to parse as GitLab
  │       │
  │       ├─► Parse successful: Private GitLab
  │       │   └─► Require authentication
  │       │
  │       └─► Parse failed: Invalid URL
  │           └─► Show error message
```

#### Step 2.2.2: Authentication Flow

```
Private Repository Detected
  │
  ▼
Request Credentials
  │
  ├─► Username provided?
  │   └─► NO: Error - Username required
  │
  └─► Password provided?
      └─► NO: Error - Password required
  │
  ▼
Test Authentication
  │
  ├─► Make test API call
  │
  ├─► Success?
  │   └─► YES: Continue
  │   └─► NO: Show auth error
```

#### Step 2.2.3: Git Operations

```
1. Clone Repository
   ┌────────────────────────────────┐
   │ git clone --bare URL temp/     │
   │                                │
   │ Progress indicators:           │
   │ • Receiving objects: 75%       │
   │ • Resolving deltas: 100%       │
   └────────────────────────────────┘

2. Create Bundle
   ┌────────────────────────────────┐
   │ git bundle create repo.bundle  │
   │        --all                   │
   │                                │
   │ Includes:                      │
   │ • All branches                 │
   │ • All tags                     │
   │ • Complete history             │
   └────────────────────────────────┘

3. Process Submodules (if enabled)
   ┌────────────────────────────────┐
   │ For each submodule:            │
   │ 1. git submodule init          │
   │ 2. git submodule update        │
   │ 3. Create submodule bundle     │
   └────────────────────────────────┘
```

---

## 3. Transfer Process

### 3.1 Physical Transfer Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                 EXTERNAL NETWORK                                │
│                                                                 │
│  Developer Workstation                                          │
│  └─► ./dist/project-20241231-143022.tar.gz                    │
│       │                                                         │
│       │ Copy to USB                                            │
│       ▼                                                         │
│  ┌──────────────┐                                              │
│  │  USB Drive   │                                              │
│  │  /Volumes/USB│                                              │
│  └──────┬───────┘                                              │
└─────────┼──────────────────────────────────────────────────────┘
          │
          │ Physical Transport
          │ (Walk to air-gapped network)
          │
┌─────────▼──────────────────────────────────────────────────────┐
│                AIR-GAPPED NETWORK                               │
│                                                                 │
│  ┌──────────────┐                                              │
│  │  USB Drive   │                                              │
│  │  /Volumes/USB│                                              │
│  └──────┬───────┘                                              │
│         │                                                       │
│         │ Insert into workstation                              │
│         ▼                                                       │
│  Developer Workstation                                          │
│  └─► Ready for ingest                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Transfer Checklist

```
Before Leaving External Network:
  ☑ Bundle file created successfully
  ☑ File integrity verified
  ☑ File copied to USB drive
  ☑ USB drive safely ejected

During Physical Transfer:
  ☑ USB drive securely transported
  ☑ No intermediate connections

Upon Arrival at Air-Gapped Network:
  ☑ USB drive inserted
  ☑ Bundle file visible
  ☑ Ready to start ingest process
```

---

## 4. Ingest Workflow (Air-Gapped Network)

### 4.1 Complete Ingest Flow Diagram

```
START (First Time)
  │
  ▼
┌─────────────────────────────────────────┐
│  Step 1: Launch moark-ingest-ui         │
│  Command: moark-ingest-ui               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 2: S3 Configuration (First Run)   │
│  ┌────────────────────────────────────┐ │
│  │ S3 Endpoint: s3.internal.company   │ │
│  │ Bucket: airgap-mappings            │ │
│  │ Access Key: [optional]             │ │
│  │ Secret Key: [optional]             │ │
│  │ ☐ Disable SSL Verification         │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 3: Download Mapping Dictionary    │
│  ┌────────────────────────────────────┐ │
│  │ • Click "Save & Download Mapping"  │ │
│  │ • System connects to S3            │ │
│  │ • Downloads mapping-dict.json      │ │
│  │ • Saves to ~/.moark/               │ │
│  │ • Displays mappings in table       │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 4: Scan for Bundles               │
│  ┌────────────────────────────────────┐ │
│  │ Option A: Auto Scan                │ │
│  │ • Click "Auto Scan"                │ │
│  │ • System scans all USB devices     │ │
│  │                                    │ │
│  │ Option B: Manual Path              │ │
│  │ • Enter path: /Volumes/USB         │ │
│  │ • Click "Scan Path"                │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 5: Bundle Detection & Display     │
│  ┌────────────────────────────────────┐ │
│  │  Bundles Table:                    │ │
│  │  ┌──────────────────────────────┐ │ │
│  │  │File      │Repo│Size│Artifacts││ │
│  │  ├──────────────────────────────┤ │ │
│  │  │project...│proj│125M│ Yes     ││ │
│  │  │app...    │app │ 45M│ No      ││ │
│  │  └──────────────────────────────┘ │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 6: Select Bundle                  │
│  • Click on bundle row                  │
│  • System extracts metadata             │
│  • Checks for mapping                   │
│  ┌────────────────────────────────────┐ │
│  │ ✅ Mapping found!                  │ │
│  │ External: project-name             │ │
│  │ Internal: classified-project-alpha │ │
│  │ Target: git.internal/security/...  │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 7: Enter Git Credentials          │
│  ┌────────────────────────────────────┐ │
│  │ Git Username: [git-user]           │ │
│  │ Git Password: [***********]        │ │
│  │                                    │ │
│  │ Options:                           │ │
│  │ ☑ Verify Repository                │ │
│  │ ☐ Force Push                       │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 8: Click "Upload Bundle"          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  System Processing:                     │
│  ┌────────────────────────────────────┐ │
│  │ 1. Validate bundle                 │ │
│  │    └─► Check file integrity        │ │
│  │    └─► Verify manifest             │ │
│  │                                    │ │
│  │ 2. Extract bundle                  │ │
│  │    └─► Decompress .tar.gz          │ │
│  │    └─► Extract to temp/            │ │
│  │                                    │ │
│  │ 3. Configure Git remote            │ │
│  │    └─► Build authenticated URL     │ │
│  │    └─► Set remote origin           │ │
│  │                                    │ │
│  │ 4. Push to internal GitLab         │ │
│  │    └─► git push --mirror           │ │
│  │    └─► Display progress            │ │
│  │                                    │ │
│  │ 5. Extract artifacts (if any)      │ │
│  │    └─► Copy to output directory    │ │
│  │                                    │ │
│  │ 6. Record history                  │ │
│  │    └─► Add to history.json         │ │
│  │    └─► Update statistics           │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Step 9: Completion                     │
│  ┌────────────────────────────────────┐ │
│  │ ✅ Upload successful!              │ │
│  │                                    │ │
│  │ Repository: classified-project-a   │ │
│  │ Pushed to: git.internal/security/  │ │
│  │ Artifacts: 5 files extracted       │ │
│  │                                    │ │
│  │ History updated ✓                  │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
  │
  ▼
END
```

### 4.2 Mapping Resolution Process

```
Bundle Selected: "project-name"
  │
  ▼
Lookup in Mapping Dictionary
  │
  ├─► Found?
  │   │
  │   ├─► YES:
  │   │   ├─► Get internal_repo
  │   │   ├─► Get internal_url
  │   │   ├─► Get classification
  │   │   ├─► Display to user
  │   │   └─► Proceed with upload
  │   │
  │   └─► NO:
  │       ├─► Show error message
  │       ├─► "No mapping found for 'project-name'"
  │       ├─► "Contact admin to add mapping"
  │       └─► Cannot proceed
```

---

## 5. Common Scenarios

### 5.1 Scenario: Simple Public Repository

**Context:** Developer needs to transfer a public GitHub repository

```
PACK PHASE:
1. Launch moark-pack-ui
2. Enter URL: https://github.com/user/simple-app.git
3. No authentication needed (public)
4. Click "Pack"
5. Bundle created: simple-app-20241231.tar.gz
6. Copy to USB

TRANSFER:
Physical transport

INGEST PHASE:
1. Launch moark-ingest-ui
2. Insert USB
3. Auto Scan
4. Select simple-app bundle
5. Check mapping: "simple-app" → "internal-simple-app"
6. Enter Git credentials
7. Upload
8. Complete!
```

### 5.2 Scenario: Private GitLab with Submodules and Artifacts

**Context:** Complex project with submodules and CI/CD artifacts

```
PACK PHASE:
1. Launch moark-pack-ui
2. Enter URL: https://gitlab.company.com/team/complex-project.git
3. Enter username/password
4. Check options:
   ☑ Include Submodules
   ☑ Download Artifacts
   Ref: main
5. Click "Pack"
6. Processing:
   - Clone main repo
   - Clone 3 submodules
   - Download 15 artifacts
   - Create bundle
7. Bundle created: complex-project-20241231.tar.gz (450 MB)
8. Copy to USB

TRANSFER:
Physical transport

INGEST PHASE:
1. Launch moark-ingest-ui
2. Insert USB
3. Auto Scan
4. Select complex-project bundle
5. System shows:
   - Repo: complex-project
   - Size: 450 MB
   - Submodules: Yes
   - Artifacts: Yes
6. Check mapping: "complex-project" → "classified-alpha"
7. Enter Git credentials
8. Upload:
   - Extract bundle
   - Push main repo
   - Push submodules
   - Extract 15 artifacts
9. Complete!
```

### 5.3 Scenario: First-Time Ingest Setup

**Context:** New developer setting up ingest for first time

```
COMPLETE SETUP:
1. Install moark-ingest:
   pip install moark-ingest[ui]

2. Launch moark-ingest-ui

3. Configure S3 (First Time):
   - Endpoint: https://s3.internal.company
   - Bucket: airgap-mappings
   - Access Key: (optional)
   - Secret Key: (optional)
   - Click "Save & Download Mapping"

4. System downloads mapping dictionary:
   - Saved to ~/.moark/mapping-dict.json
   - Table populated with mappings
   - Configuration saved

5. Ready for normal use:
   - S3 settings persisted
   - Mapping dictionary cached locally
   - No need to reconfigure

SUBSEQUENT USES:
1. Launch moark-ingest-ui
2. Settings auto-loaded
3. Can refresh mapping if needed
4. Ready to scan and ingest
```

---

## 6. Troubleshooting Workflows

### 6.1 Pack Troubleshooting

```
Problem: Authentication Failure
  │
  ├─► Check credentials
  │   └─► Re-enter username/password
  │
  ├─► Check network connectivity
  │   └─► Test URL in browser
  │
  └─► Check repository access
      └─► Verify permissions

Problem: Clone Failure
  │
  ├─► Check disk space
  │   └─► Free up space if needed
  │
  ├─► Check repository size
  │   └─► Consider network timeout
  │
  └─► Check Git installation
      └─► Verify: git --version

Problem: Bundle Creation Failure
  │
  ├─► Check Git version (>= 2.0)
  │
  ├─► Check file permissions
  │
  └─► Check output directory
      └─► Must be writable
```

### 6.2 Ingest Troubleshooting

```
Problem: S3 Connection Failure
  │
  ├─► Check endpoint URL
  │   └─► Must include https://
  │
  ├─► Check network connectivity
  │   └─► Can internal network reach S3?
  │
  ├─► Check credentials
  │   └─► Try without (if using IAM)
  │
  └─► Check SSL settings
      └─► Try disabling SSL verification

Problem: No Mapping Found
  │
  ├─► Refresh mapping dictionary
  │   └─► Click "Save & Download Mapping"
  │
  ├─► Check mapping exists
  │   └─► Contact admin
  │
  └─► Verify bundle repo name
      └─► Check manifest.json

Problem: Upload Failure
  │
  ├─► Check Git credentials
  │   └─► Test manually: git push
  │
  ├─► Check repository exists
  │   └─► Create if needed
  │
  ├─► Check network connectivity
  │   └─► Can reach internal GitLab?
  │
  └─► Check permissions
      └─► User must have push access
```

---

## 7. Process Flowcharts

### 7.1 Error Handling Flow

```
Error Encountered
  │
  ├─► Recoverable?
  │   │
  │   ├─► YES:
  │   │   ├─► Show error message
  │   │   ├─► Suggest fix
  │   │   ├─► Allow retry
  │   │   └─► Log error
  │   │
  │   └─► NO:
  │       ├─► Show detailed error
  │       ├─► Save error log
  │       ├─► Cleanup resources
  │       └─► Return to ready state
```

### 7.2 Validation Flow

```
User Input
  │
  ├─► Validate format
  │   └─► Valid? Continue : Show error
  │
  ├─► Validate accessibility
  │   └─► Accessible? Continue : Show error
  │
  ├─► Validate permissions
  │   └─► Authorized? Continue : Show error
  │
  └─► Proceed with operation
```

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**For Support:** Contact Moshe Eliya


