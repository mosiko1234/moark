# Design Document

## Overview

מסמך זה מתאר את העיצוב להרחבת מערכת Airgap Git Relay עם:
1. **מערכת מיפוי Repositories** - ניהול קונפיגורציה למיפוי שמות repos חיצוניים לפנימיים
2. **ממשק משתמש גרפי (UI)** - ממשקי web לשלבי Pack ו-Ingest
3. **ניהול פרופילים** - תמיכה במספר קונפיגורציות לצוותים/פרויקטים שונים

המערכת תשתמש ב-FastAPI לצד השרת ו-HTML/CSS/JavaScript vanilla לצד הלקוח (ללא frameworks חיצוניים) כדי להבטיח עבודה offline ברשת airgap.

## Architecture

```mermaid
flowchart TB
    subgraph External["External Network"]
        PACK_UI["Pack UI<br/>(FastAPI + HTML)"]
        PACK_CLI["airgap-pack CLI"]
        PACK_UI -->|"Execute"| PACK_CLI
    end
    
    subgraph Transfer["Physical Transfer"]
        BUNDLE[("tar.gz Bundle")]
        USB[("USB Drive")]
    end
    
    subgraph Internal["Internal Network (Air-Gapped)"]
        INGEST_UI["Ingest UI<br/>(FastAPI + HTML)"]
        INGEST_CLI["airgap-ingest CLI"]
        MAPPING_CLI["airgap-mapping CLI"]
        
        subgraph Config["Configuration"]
            PROFILES[("profiles.json")]
            MAPPINGS[("mappings/<profile>.json")]
            HISTORY[("history.json")]
        end
        
        INGEST_UI -->|"Execute"| INGEST_CLI
        INGEST_UI -->|"Manage"| MAPPING_CLI
        INGEST_CLI -->|"Read"| MAPPINGS
        MAPPING_CLI -->|"Read/Write"| MAPPINGS
        INGEST_UI -->|"Read/Write"| PROFILES
        INGEST_CLI -->|"Write"| HISTORY
    end
    
    PACK_CLI --> BUNDLE
    BUNDLE --> USB
    USB --> INGEST_UI
```

## Components and Interfaces

### 1. Configuration Manager (`config_manager.py`)

מודול לניהול קונפיגורציה, פרופילים ומיפויים.

```python
@dataclass
class Profile:
    """Configuration profile for a team/project."""
    name: str
    description: str
    gitlab_url: str | None
    remote_template: str | None
    output_dir: str | None
    created_at: str
    updated_at: str

@dataclass  
class MappingEntry:
    """Single mapping from external to internal repo name."""
    external_name: str
    internal_name: str
    added_at: str
    notes: str | None

class ConfigManager:
    """Manages profiles, mappings, and settings."""
    
    def __init__(self, config_dir: Path):
        """Initialize with configuration directory."""
        
    # Profile Management
    def list_profiles(self) -> list[Profile]: ...
    def get_profile(self, name: str) -> Profile | None: ...
    def create_profile(self, name: str, description: str = "") -> Profile: ...
    def update_profile(self, name: str, **kwargs) -> Profile: ...
    def delete_profile(self, name: str) -> bool: ...
    def export_profile(self, name: str) -> dict: ...
    def import_profile(self, data: dict) -> Profile: ...
    
    # Mapping Management
    def get_mappings(self, profile: str) -> dict[str, MappingEntry]: ...
    def add_mapping(self, profile: str, external: str, internal: str, notes: str = "") -> MappingEntry: ...
    def remove_mapping(self, profile: str, external: str) -> bool: ...
    def resolve_mapping(self, profile: str, external_name: str) -> str: ...
```

### 2. Mapping CLI (`mapping_cli.py`)

פקודות CLI לניהול מיפויים.

```python
app = typer.Typer(help="Manage repository name mappings.")

@app.command("list")
def list_mappings(
    profile: str = typer.Option("default", "--profile", "-p"),
    config_dir: Path = typer.Option(None, "--config-dir", envvar="AIRGAP_CONFIG_DIR"),
) -> None:
    """List all mappings for a profile."""

@app.command("add")
def add_mapping(
    external: str = typer.Argument(..., help="External repository name"),
    internal: str = typer.Argument(..., help="Internal repository name"),
    profile: str = typer.Option("default", "--profile", "-p"),
    notes: str = typer.Option("", "--notes", "-n"),
) -> None:
    """Add a new mapping."""

@app.command("remove")
def remove_mapping(
    external: str = typer.Argument(..., help="External repository name to remove"),
    profile: str = typer.Option("default", "--profile", "-p"),
) -> None:
    """Remove a mapping."""

@app.command("validate")
def validate_mappings(
    profile: str = typer.Option("default", "--profile", "-p"),
) -> None:
    """Validate mapping configuration."""
```

### 3. History Manager (`history_manager.py`)

מודול לניהול היסטוריית העלאות.

```python
@dataclass
class HistoryEntry:
    """Record of a single ingestion."""
    id: str
    timestamp: str
    bundle_name: str
    source_repo: str
    target_repo: str
    profile: str
    status: str  # "success" | "failed"
    error_message: str | None
    artifacts_count: int
    duration_seconds: float

class HistoryManager:
    """Manages ingestion history."""
    
    def __init__(self, history_file: Path):
        """Initialize with history file path."""
        
    def add_entry(self, entry: HistoryEntry) -> None: ...
    def get_entries(self, limit: int = 50) -> list[HistoryEntry]: ...
    def get_entry(self, entry_id: str) -> HistoryEntry | None: ...
    def clear_history(self) -> None: ...
```

### 4. Pack UI Server (`pack_ui.py`)

שרת FastAPI לממשק האריזה.

```python
app = FastAPI(title="Airgap Pack UI")

# Static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static/pack"), name="static")

@app.get("/")
async def index() -> HTMLResponse:
    """Serve the main Pack UI page."""

@app.get("/api/profiles")
async def get_profiles() -> list[dict]:
    """Get all profiles."""

@app.post("/api/profiles")
async def create_profile(data: ProfileCreate) -> dict:
    """Create a new profile."""

@app.get("/api/profiles/{name}/settings")
async def get_profile_settings(name: str) -> dict:
    """Get settings for a profile."""

@app.put("/api/profiles/{name}/settings")
async def update_profile_settings(name: str, data: SettingsUpdate) -> dict:
    """Update profile settings."""

@app.post("/api/pack")
async def execute_pack(data: PackRequest) -> StreamingResponse:
    """Execute pack operation with streaming progress."""

class PackRequest(BaseModel):
    profile: str
    repo_url: str | None
    source_gitlab_url: str | None
    repo_path: str | None
    source_username: str | None
    source_token: str | None
    with_submodules: bool
    with_artifacts: bool
    artifacts_ref: str | None
    output_dir: str
```

### 5. Ingest UI Server (`ingest_ui.py`)

שרת FastAPI לממשק הטעינה.

```python
app = FastAPI(title="Airgap Ingest UI")

app.mount("/static", StaticFiles(directory="static/ingest"), name="static")

@app.get("/")
async def index() -> HTMLResponse:
    """Serve the main Ingest UI page."""

# Profile endpoints
@app.get("/api/profiles")
async def get_profiles() -> list[dict]: ...

@app.post("/api/profiles")
async def create_profile(data: ProfileCreate) -> dict: ...

@app.delete("/api/profiles/{name}")
async def delete_profile(name: str) -> dict: ...

@app.get("/api/profiles/{name}/export")
async def export_profile(name: str) -> dict: ...

@app.post("/api/profiles/import")
async def import_profile(data: dict) -> dict: ...

# Mapping endpoints
@app.get("/api/mappings")
async def get_mappings(profile: str = "default") -> list[dict]: ...

@app.post("/api/mappings")
async def add_mapping(data: MappingCreate) -> dict: ...

@app.delete("/api/mappings/{external}")
async def delete_mapping(external: str, profile: str = "default") -> dict: ...

# Bundle endpoints
@app.post("/api/bundles/upload")
async def upload_bundle(file: UploadFile) -> dict:
    """Upload and analyze a bundle."""

@app.get("/api/bundles/drop-folder")
async def list_drop_folder() -> list[dict]:
    """List bundles in drop folder."""

@app.get("/api/bundles/{bundle_id}/manifest")
async def get_manifest(bundle_id: str) -> dict:
    """Get manifest from uploaded bundle."""

@app.post("/api/ingest")
async def execute_ingest(data: IngestRequest) -> StreamingResponse:
    """Execute ingest operation with streaming progress."""

# History endpoints
@app.get("/api/history")
async def get_history(limit: int = 50) -> list[dict]: ...

@app.get("/api/history/{entry_id}")
async def get_history_entry(entry_id: str) -> dict: ...
```

## Data Models

### Profile Configuration (`profiles.json`)

```json
{
  "active_profile": "team-alpha",
  "profiles": {
    "default": {
      "name": "default",
      "description": "Default profile",
      "gitlab_url": null,
      "remote_template": "https://{username}:{password}@git.internal/{repo}.git",
      "output_dir": "./dist",
      "created_at": "2024-12-24T10:00:00Z",
      "updated_at": "2024-12-24T10:00:00Z"
    },
    "team-alpha": {
      "name": "team-alpha",
      "description": "Team Alpha project configuration",
      "gitlab_url": "https://gitlab.company.com",
      "remote_template": "https://{username}:{password}@git.internal/alpha/{repo}.git",
      "output_dir": "./alpha-dist",
      "created_at": "2024-12-24T11:00:00Z",
      "updated_at": "2024-12-24T12:00:00Z"
    }
  }
}
```

### Mapping Configuration (`mappings/<profile>.json`)

```json
{
  "profile": "team-alpha",
  "mappings": {
    "external-repo-name": {
      "internal_name": "internal/path/repo",
      "added_at": "2024-12-24T10:00:00Z",
      "notes": "Main application repository"
    },
    "another-external": {
      "internal_name": "internal/libs/another",
      "added_at": "2024-12-24T11:00:00Z",
      "notes": null
    }
  }
}
```

### History File (`history.json`)

```json
{
  "entries": [
    {
      "id": "abc123",
      "timestamp": "2024-12-24T14:30:00Z",
      "bundle_name": "project-20241224T143000Z.tar.gz",
      "source_repo": "external-project",
      "target_repo": "internal/project",
      "profile": "team-alpha",
      "status": "success",
      "error_message": null,
      "artifacts_count": 3,
      "duration_seconds": 45.2
    }
  ]
}
```

### Directory Structure

```
~/.airgap-relay/
├── profiles.json           # Profile definitions
├── mappings/
│   ├── default.json        # Default profile mappings
│   ├── team-alpha.json     # Team Alpha mappings
│   └── team-beta.json      # Team Beta mappings
├── history.json            # Ingestion history
└── temp/                   # Temporary files for uploads
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. 
Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the acceptance criteria analysis, the following properties must hold:

### Property 1: Mapping Resolution Correctness
*For any* mapping configuration and any external repository name that exists as a key in the mapping, resolving that name SHALL return the corresponding internal name value.

**Validates: Requirements 1.5**

### Property 2: Configuration Format Round-Trip
*For any* valid mapping configuration data structure, serializing to JSON and then parsing back SHALL produce an equivalent data structure. Similarly for YAML format.

**Validates: Requirements 1.4**

### Property 3: Add Mapping Persistence
*For any* valid external name and internal name pair, after calling the add_mapping function, the mapping SHALL exist in the configuration file with the correct values.

**Validates: Requirements 2.2, 5.3**

### Property 4: Remove Mapping Correctness
*For any* existing mapping entry, after calling the remove_mapping function with that external name, the mapping SHALL no longer exist in the configuration.

**Validates: Requirements 2.3, 5.4**

### Property 5: Backup Creation on Modification
*For any* modification operation (add or remove mapping), the system SHALL create a backup file containing the previous configuration state before applying the change.

**Validates: Requirements 2.5**

### Property 6: Profile Settings Loading
*For any* profile with saved settings, when that profile is selected/loaded, the returned settings SHALL match the values stored in the profile's configuration.

**Validates: Requirements 8.1, 8.2, 8.4, 9.4, 10.2**

### Property 7: Profile Settings Saving
*For any* settings modification while a profile is active, the changes SHALL be persisted to that specific profile's configuration file, not affecting other profiles.

**Validates: Requirements 9.5, 10.4**

### Property 8: Profile Creation with Mapping File
*For any* newly created profile, the system SHALL create a corresponding mapping file for that profile in the mappings directory.

**Validates: Requirements 10.1**

### Property 9: Export Excludes Sensitive Credentials
*For any* profile export operation, the exported JSON SHALL NOT contain password, token, or other sensitive credential fields.

**Validates: Requirements 9.7**

### Property 10: Export Includes Mappings
*For any* profile export operation, the exported JSON SHALL include all mappings associated with that profile.

**Validates: Requirements 10.5**

### Property 11: History Recording Completeness
*For any* successful ingestion operation, the history entry SHALL contain all required fields: timestamp, bundle_name, source_repo, target_repo, profile, and status.

**Validates: Requirements 6.1, 6.2**

### Property 12: No External Resource Dependencies
*For any* HTML page served by the UI, all referenced resources (CSS, JavaScript, images) SHALL be served from local paths, with no external CDN or internet URLs.

**Validates: Requirements 7.2, 7.3**

## Error Handling

### Configuration Errors

| Error Condition | Handling |
|----------------|----------|
| Mapping file not found | Create empty mapping file with warning |
| Invalid JSON/YAML syntax | Display parse error with line number, abort operation |
| Missing required fields | Display validation error, abort operation |
| Profile not found | Return 404 error with available profiles list |
| Duplicate profile name | Return 409 conflict error |

### Operation Errors

| Error Condition | Handling |
|----------------|----------|
| Bundle upload fails | Display error, allow retry |
| Manifest parse error | Display error with details, reject bundle |
| Ingest operation fails | Record failure in history, display error |
| Git push fails | Display git error output, suggest troubleshooting |
| File permission error | Display permission error with required permissions |

### UI Error Display

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict | None = None
    suggestion: str | None = None
```

## Testing Strategy

### Property-Based Testing

The project will use **Hypothesis** for property-based testing in Python.

Each property-based test MUST:
1. Be annotated with the property number and requirements reference
2. Run a minimum of 100 iterations
3. Use smart generators that constrain to valid input spaces

### Unit Tests

Unit tests will cover:
- ConfigManager initialization and file handling
- Individual API endpoint responses
- CLI command parsing and execution
- Error condition handling

### Test File Structure

```
tests/
├── test_config_manager.py      # ConfigManager unit tests
├── test_mapping_cli.py         # Mapping CLI tests
├── test_history_manager.py     # History manager tests
├── test_pack_ui_api.py         # Pack UI API tests
├── test_ingest_ui_api.py       # Ingest UI API tests
├── test_properties.py          # Property-based tests
└── conftest.py                 # Shared fixtures
```

### Property Test Format

```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(
    external=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))),
    internal=st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')))
)
def test_property_3_add_mapping_persistence(external: str, internal: str, tmp_config_dir):
    """
    **Feature: repo-mapping-and-ui, Property 3: Add Mapping Persistence**
    **Validates: Requirements 2.2, 5.3**
    
    For any valid external/internal name pair, after adding,
    the mapping should exist in the configuration.
    """
    manager = ConfigManager(tmp_config_dir)
    manager.add_mapping("default", external, internal)
    
    mappings = manager.get_mappings("default")
    assert external in mappings
    assert mappings[external].internal_name == internal
```

