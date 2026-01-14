# Requirements Document

## Introduction

הרחבת כלי airgap-git-relay לתמיכה ב-GitLab פרטי כמקור, כולל הורדת CI/CD artifacts. הפיצ'ר מאפשר למשתמשים לארוז repositories מ-GitLab פרטי ארגוני (לא רק GitLab.com ציבורי) ולכלול artifacts מ-pipelines כחלק מה-bundle. בצד ה-ingest, הכלי יזהה ויחלץ את ה-artifacts לנתיב מוגדר.

## Glossary

- **GitLab Private Instance**: שרת GitLab פרטי המותקן בארגון (self-hosted), לדוגמה: https://gitlab.mycompany.com
- **Source GitLab**: שרת ה-GitLab ממנו מורידים את ה-repository וה-artifacts
- **Repo Path**: נתיב יחסי לפרויקט ב-GitLab, לדוגמה: group/subgroup/project
- **GitLab API**: ממשק REST של GitLab לגישה לנתונים כמו pipelines ו-artifacts
- **CI/CD Artifacts**: קבצים שנוצרים כתוצאה מהרצת pipeline ב-GitLab CI/CD
- **Pipeline**: תהליך אוטומטי ב-GitLab CI/CD שמריץ jobs
- **Job**: משימה בודדת בתוך pipeline שיכולה לייצר artifacts
- **Ref**: הפניה ל-branch או tag ב-Git
- **Bundle**: קובץ tar.gz שנוצר על ידי airgap-pack ומכיל את ה-repository, manifest, ואופציונלית artifacts
- **Manifest**: קובץ JSON בתוך ה-bundle שמתאר את תוכנו

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want to pack repositories from my organization's private GitLab instance, so that I can transfer them to an air-gapped environment.

#### Acceptance Criteria

1. WHEN a user runs airgap-pack with `--source-gitlab-url` parameter THEN the Pack Command SHALL accept the URL as the base address for the private GitLab instance
2. WHEN a user provides `--repo-path` parameter THEN the Pack Command SHALL construct the full Git URL by combining the source GitLab URL with the repo path
3. WHEN a user provides `--source-username` and `--source-token` parameters THEN the Pack Command SHALL use these credentials for authentication against the source GitLab
4. WHEN environment variables SOURCE_GITLAB_USERNAME and SOURCE_GITLAB_TOKEN are set THEN the Pack Command SHALL use these values as fallback when CLI parameters are not provided
5. WHEN `--source-gitlab-url` is provided without `--repo-path` THEN the Pack Command SHALL display an error message and exit

### Requirement 2

**User Story:** As a DevOps engineer, I want to include CI/CD artifacts in my bundle, so that I can transfer build outputs along with the source code.

#### Acceptance Criteria

1. WHEN a user provides `--with-artifacts` flag THEN the Pack Command SHALL download artifacts from the GitLab CI/CD pipelines
2. WHEN downloading artifacts THEN the Pack Command SHALL use the GitLab API with the provided authentication credentials
3. WHEN `--artifacts-ref` is not specified THEN the Pack Command SHALL download artifacts from the default branch's latest successful pipeline
4. WHEN `--artifacts-ref` is specified THEN the Pack Command SHALL download artifacts from the latest successful pipeline for that specific ref (branch or tag)
5. WHEN artifacts are downloaded THEN the Pack Command SHALL store the artifacts in an `artifacts/` directory within the bundle
6. WHEN artifacts are included THEN the Pack Command SHALL update manifest.json to include metadata about the downloaded artifacts (job names, file sizes, download timestamps)
7. IF no successful pipeline exists for the specified ref THEN the Pack Command SHALL display a warning and continue without artifacts
8. IF artifact download fails THEN the Pack Command SHALL display a warning with the error details and continue with the remaining artifacts

### Requirement 3

**User Story:** As a DevOps engineer, I want to extract artifacts from the bundle during ingestion, so that I can use the build outputs in the air-gapped environment.

#### Acceptance Criteria

1. WHEN a bundle contains an `artifacts/` directory THEN the Ingest Command SHALL detect the presence of artifacts
2. WHEN `--artifacts-output-dir` is provided THEN the Ingest Command SHALL copy all artifacts from the bundle to the specified directory
3. WHEN `--artifacts-output-dir` is not provided and artifacts exist THEN the Ingest Command SHALL skip artifact extraction and log an informational message
4. WHEN extracting artifacts THEN the Ingest Command SHALL preserve the original directory structure from the bundle
5. WHEN artifact extraction completes THEN the Ingest Command SHALL log the number of artifacts extracted and their total size

### Requirement 4

**User Story:** As a user, I want clear documentation on how to use the new GitLab private source features, so that I can configure the tool correctly.

#### Acceptance Criteria

1. WHEN the README.md is updated THEN the Documentation SHALL include examples for connecting to a private GitLab instance
2. WHEN the README.md is updated THEN the Documentation SHALL explain all new parameters (`--source-gitlab-url`, `--source-username`, `--source-token`, `--repo-path`, `--with-artifacts`, `--artifacts-ref`, `--artifacts-output-dir`)
3. WHEN the README.md is updated THEN the Documentation SHALL include a complete usage example showing the full workflow from pack to ingest with artifacts

### Requirement 5

**User Story:** As a developer, I want the manifest to accurately reflect bundle contents, so that I can programmatically inspect what was packed.

#### Acceptance Criteria

1. WHEN a bundle is created with artifacts THEN the Manifest SHALL include an `artifacts` array with metadata for each artifact
2. WHEN artifact metadata is recorded THEN the Manifest SHALL include job_name, file_name, file_size, and pipeline_id for each artifact
3. WHEN serializing the manifest to JSON THEN the Pack Command SHALL produce valid JSON that can be parsed back to equivalent data
4. WHEN parsing a manifest from JSON THEN the Ingest Command SHALL correctly reconstruct the manifest data structure
