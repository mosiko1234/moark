# Requirements Document

## Introduction

הרחבת מערכת Airgap Git Relay עם שני רכיבים עיקריים:
1. **ניהול מיפוי Repositories** - מערכת קונפיגורציה ברשת הפנימית שמאפשרת למפות שמות repositories חיצוניים לשמות פנימיים, מטעמי סיווג ואבטחה. המיפוי מאפשר להעלות קוד מבלי לחשוף את שמות ה-repositories המקוריים ברשת האינטרנט.
2. **ממשק משתמש גרפי (UI)** - ממשק web פשוט לשני השלבים: אריזה (pack) ברשת החיצונית וטעינה (ingest) ברשת הפנימית.

## Glossary

- **Repo Mapping**: קובץ קונפיגורציה (JSON/YAML) שממפה שמות repositories חיצוניים לשמות פנימיים
- **External Repo Name**: שם ה-repository כפי שמופיע ברשת האינטרנט (GitLab/GitHub חיצוני)
- **Internal Repo Name**: שם ה-repository כפי שיופיע ברשת הפנימית (GitLab airgap)
- **Pack UI**: ממשק משתמש גרפי לשלב האריזה ברשת החיצונית
- **Ingest UI**: ממשק משתמש גרפי לשלב הטעינה ברשת הפנימית
- **Bundle**: קובץ tar.gz שנוצר על ידי airgap-pack
- **Drop Folder**: תיקייה לקליטת bundles אוטומטית
- **Mapping Config**: קובץ הקונפיגורציה למיפוי שמות

## Requirements

### Requirement 1

**User Story:** As a security officer, I want to manage repository name mappings in a configuration file, so that external repository names are not exposed in the internal network.

#### Acceptance Criteria

1. WHEN the Ingest Command starts THEN the System SHALL look for a mapping configuration file at a configurable path
2. WHEN `--mapping-config` parameter is provided THEN the System SHALL load the mapping from the specified file path
3. WHEN environment variable `AIRGAP_MAPPING_CONFIG` is set THEN the System SHALL use this path as fallback when CLI parameter is not provided
4. WHEN a mapping file is loaded THEN the System SHALL support both JSON and YAML formats
5. WHEN an external repo name matches a key in the mapping THEN the System SHALL use the corresponding internal name for the target repository

### Requirement 2

**User Story:** As a DevOps engineer, I want to manage the mapping configuration easily, so that I can add, update, and remove mappings without editing files manually.

#### Acceptance Criteria

1. WHEN a user runs `airgap-mapping list` THEN the Mapping CLI SHALL display all current mappings in a readable format
2. WHEN a user runs `airgap-mapping add <external> <internal>` THEN the Mapping CLI SHALL add a new mapping entry to the configuration file
3. WHEN a user runs `airgap-mapping remove <external>` THEN the Mapping CLI SHALL remove the mapping entry for the specified external name
4. WHEN a user runs `airgap-mapping validate` THEN the Mapping CLI SHALL check the configuration file for syntax errors and report issues
5. WHEN modifying the mapping file THEN the Mapping CLI SHALL create a backup of the previous version

### Requirement 3

**User Story:** As a DevOps engineer, I want a web UI for the pack operation, so that I can easily create bundles without memorizing CLI commands.

#### Acceptance Criteria

1. WHEN a user runs `airgap-pack-ui` THEN the Pack UI Server SHALL start a local web server on a configurable port
2. WHEN the Pack UI loads THEN the Interface SHALL display a form with fields for repository URL, GitLab credentials, and pack options
3. WHEN a user fills the form and clicks "Pack" THEN the Pack UI SHALL execute the pack operation and display progress
4. WHEN the pack operation completes THEN the Pack UI SHALL display the output file path and bundle size
5. WHEN the pack operation fails THEN the Pack UI SHALL display the error message in a readable format
6. WHEN `--with-artifacts` is selected THEN the Pack UI SHALL show additional fields for artifacts configuration

### Requirement 4

**User Story:** As a DevOps engineer, I want a web UI for the ingest operation, so that I can easily upload bundles and manage mappings in the air-gapped environment.

#### Acceptance Criteria

1. WHEN a user runs `airgap-ingest-ui` THEN the Ingest UI Server SHALL start a local web server on a configurable port
2. WHEN the Ingest UI loads THEN the Interface SHALL display options to upload a bundle file or select from drop folder
3. WHEN a user uploads a bundle THEN the Ingest UI SHALL display the manifest contents including repo name, submodules, and artifacts
4. WHEN displaying bundle info THEN the Ingest UI SHALL show the mapped internal name if a mapping exists
5. WHEN a user clicks "Ingest" THEN the Ingest UI SHALL execute the ingest operation and display progress
6. WHEN the ingest operation completes THEN the Ingest UI SHALL display the target GitLab project URL and statistics

### Requirement 5

**User Story:** As a DevOps engineer, I want to manage mappings through the Ingest UI, so that I can configure name translations without using the CLI.

#### Acceptance Criteria

1. WHEN the Ingest UI loads THEN the Interface SHALL include a "Mappings" section showing current mappings
2. WHEN a user clicks "Add Mapping" THEN the Ingest UI SHALL display a form to enter external and internal names
3. WHEN a user submits a new mapping THEN the Ingest UI SHALL save it to the configuration file and update the display
4. WHEN a user clicks "Delete" on a mapping THEN the Ingest UI SHALL remove the mapping after confirmation
5. WHEN a bundle is selected THEN the Ingest UI SHALL highlight if the repo name has an existing mapping or needs one

### Requirement 6

**User Story:** As a DevOps engineer, I want to see the history of ingested bundles, so that I can track what has been transferred.

#### Acceptance Criteria

1. WHEN a bundle is successfully ingested THEN the System SHALL record the ingestion in a local history file
2. WHEN recording history THEN the System SHALL store timestamp, bundle name, source repo, target repo, and status
3. WHEN the Ingest UI loads THEN the Interface SHALL display recent ingestion history
4. WHEN a user clicks on a history entry THEN the Ingest UI SHALL show detailed information about that ingestion

### Requirement 7

**User Story:** As a user, I want the UI to work offline, so that I can use it in the air-gapped environment without internet access.

#### Acceptance Criteria

1. WHEN the UI is built THEN the Build Process SHALL bundle all dependencies locally
2. WHEN the UI loads THEN the Interface SHALL not require any external CDN or internet resources
3. WHEN the UI is served THEN the Server SHALL serve all static assets from local files

### Requirement 8

**User Story:** As a DevOps engineer, I want to configure default settings, so that I don't need to enter the same values repeatedly.

#### Acceptance Criteria

1. WHEN the Pack UI starts THEN the Interface SHALL load saved default values for GitLab URL and output directory
2. WHEN the Ingest UI starts THEN the Interface SHALL load saved default values for remote template and credentials
3. WHEN a user clicks "Save as Default" THEN the UI SHALL persist the current form values to a local configuration file
4. WHEN default values exist THEN the UI SHALL pre-populate form fields with saved values

### Requirement 9

**User Story:** As a team lead, I want to manage multiple project profiles, so that different teams or projects can have their own configurations.

#### Acceptance Criteria

1. WHEN a user clicks "New Profile" THEN the UI SHALL create a new named configuration profile
2. WHEN creating a profile THEN the UI SHALL prompt for a profile name and optional description
3. WHEN profiles exist THEN the UI SHALL display a dropdown to switch between profiles
4. WHEN a profile is selected THEN the UI SHALL load all settings associated with that profile (GitLab URL, credentials, mappings, output paths)
5. WHEN a user modifies settings THEN the UI SHALL save changes to the currently active profile
6. WHEN a user clicks "Delete Profile" THEN the UI SHALL remove the profile after confirmation
7. WHEN a user clicks "Export Profile" THEN the UI SHALL generate a JSON file with the profile configuration (excluding sensitive credentials)
8. WHEN a user clicks "Import Profile" THEN the UI SHALL load a profile from a JSON file

### Requirement 10

**User Story:** As a DevOps engineer, I want each profile to have its own mapping configuration, so that different projects can have different name translations.

#### Acceptance Criteria

1. WHEN a profile is created THEN the System SHALL create a separate mapping file for that profile
2. WHEN switching profiles THEN the System SHALL load the mappings associated with the selected profile
3. WHEN displaying mappings in the UI THEN the Interface SHALL show only mappings for the active profile
4. WHEN a user adds a mapping THEN the System SHALL save it to the active profile's mapping file
5. WHEN exporting a profile THEN the Export SHALL include the profile's mappings

