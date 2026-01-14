# Requirements Document

## Introduction

מערכת להעלאת bundles שנארזו מ-GitLab באינטרנט אל שרת GitLab ברשת air-gapped. המערכת מקבלת קובץ tar.gz שנוצר על ידי airgap-pack, פותחת אותו, ומעלה את הפרויקט לשרת GitLab הפנימי תוך שימור מלא של היסטוריית הקומיטים, branches, tags, וכל הפעילות - כך שהפרויקט ייראה כאילו נוצר ופותח ישירות ברשת הסגורה.

## Glossary

- **Target GitLab**: שרת ה-GitLab ברשת הסגורה (air-gapped) אליו מעלים את הפרויקט
- **Bundle**: קובץ tar.gz שנוצר על ידי airgap-pack ומכיל bare mirror, manifest, ואופציונלית artifacts
- **Manifest**: קובץ JSON בתוך ה-bundle שמתאר את תוכנו ומקורו
- **Mirror Push**: העלאת כל ה-refs (branches, tags) מ-repository מקומי לשרת מרוחק
- **Bare Repository**: repository ללא working directory, מכיל רק את ה-.git data
- **Project Path**: נתיב הפרויקט ב-GitLab, לדוגמה: group/subgroup/project
- **Namespace**: קבוצה או תת-קבוצה ב-GitLab שמכילה פרויקטים
- **Visibility Level**: רמת הנראות של פרויקט ב-GitLab (private, internal, public)
- **CI/CD Artifacts**: קבצי build שנארזו יחד עם הקוד ב-bundle

## Requirements

### Requirement 1

**User Story:** As a DevOps engineer, I want to upload packed repositories to my air-gapped GitLab instance, so that developers can access the code internally with full Git history.

#### Acceptance Criteria

1. WHEN a user runs airgap-ingest with `--target-gitlab-url` parameter THEN the Ingest Command SHALL accept the URL as the base address for the target GitLab instance
2. WHEN a user provides `--target-token` parameter THEN the Ingest Command SHALL use this token for GitLab API authentication
3. WHEN environment variable TARGET_GITLAB_TOKEN is set THEN the Ingest Command SHALL use this value as fallback when CLI parameter is not provided
4. WHEN a bundle is ingested THEN the Ingest Command SHALL push all branches and tags from the bundle to the target GitLab
5. WHEN the push completes THEN the Ingest Command SHALL preserve the complete commit history including author names, emails, dates, and commit messages

### Requirement 2

**User Story:** As a DevOps engineer, I want the system to automatically create projects in GitLab if they don't exist, so that I don't need to manually set up each project before ingestion.

#### Acceptance Criteria

1. WHEN ingesting a bundle and the target project does not exist THEN the Ingest Command SHALL create the project using the GitLab API
2. WHEN creating a project THEN the Ingest Command SHALL use the repo_name from the manifest as the project name
3. WHEN `--target-namespace` is provided THEN the Ingest Command SHALL create the project within the specified namespace (group/subgroup)
4. WHEN `--target-namespace` is not provided THEN the Ingest Command SHALL create the project in the user's personal namespace
5. WHEN `--visibility` is provided THEN the Ingest Command SHALL set the project visibility to the specified level (private, internal, or public)
6. WHEN `--visibility` is not provided THEN the Ingest Command SHALL default to private visibility
7. IF project creation fails due to permissions THEN the Ingest Command SHALL display an error message with the required permissions

### Requirement 3

**User Story:** As a DevOps engineer, I want to control the target project path, so that I can organize projects according to my organization's structure.

#### Acceptance Criteria

1. WHEN `--target-project-path` is provided THEN the Ingest Command SHALL use this path instead of deriving from the manifest
2. WHEN `--target-project-path` contains slashes THEN the Ingest Command SHALL interpret the path as namespace/project-name
3. WHEN the target namespace in the path does not exist THEN the Ingest Command SHALL display an error message and exit
4. WHEN `--target-project-path` is not provided THEN the Ingest Command SHALL use the repo_name from the manifest

### Requirement 4

**User Story:** As a DevOps engineer, I want to handle submodules correctly, so that projects with dependencies are fully functional in the air-gapped environment.

#### Acceptance Criteria

1. WHEN a bundle contains submodules THEN the Ingest Command SHALL upload each submodule as a separate project
2. WHEN uploading submodules THEN the Ingest Command SHALL use the same target namespace as the main project
3. WHEN `--submodule-mapping` is provided THEN the Ingest Command SHALL use the mapping file to determine target paths for submodules
4. WHEN all submodules are uploaded THEN the Ingest Command SHALL log the mapping between original URLs and new internal URLs

### Requirement 5

**User Story:** As a DevOps engineer, I want to upload artifacts to GitLab, so that build outputs are available through the GitLab interface in the air-gapped environment.

#### Acceptance Criteria

1. WHEN a bundle contains artifacts THEN the Ingest Command SHALL upload each artifact to the target GitLab project using the Generic Packages API
2. WHEN uploading artifacts THEN the Ingest Command SHALL use the job_name as the package name and pipeline_id as the version
3. WHEN artifact upload completes THEN the Ingest Command SHALL log the package URL for each uploaded artifact
4. WHEN `--skip-artifacts` flag is provided THEN the Ingest Command SHALL skip artifact upload
5. IF artifact upload fails THEN the Ingest Command SHALL display a warning and continue with remaining artifacts

### Requirement 5b

**User Story:** As a DevOps engineer, I want to optionally extract artifacts to a local directory, so that I can access build outputs directly on the file system.

#### Acceptance Criteria

1. WHEN `--artifacts-output-dir` is provided THEN the Ingest Command SHALL also extract all artifacts to the specified directory
2. WHEN extracting artifacts THEN the Ingest Command SHALL preserve the directory structure (job_name/artifacts.zip)
3. WHEN artifact extraction completes THEN the Ingest Command SHALL log the number of artifacts and total size extracted

### Requirement 6

**User Story:** As a DevOps engineer, I want to update existing projects with new commits, so that I can sync changes incrementally.

#### Acceptance Criteria

1. WHEN the target project already exists THEN the Ingest Command SHALL push new commits without recreating the project
2. WHEN pushing to an existing project THEN the Ingest Command SHALL use force-push to update refs that have diverged
3. WHEN `--no-force` flag is provided THEN the Ingest Command SHALL fail if refs have diverged instead of force-pushing
4. WHEN the push succeeds THEN the Ingest Command SHALL log the number of new commits and updated refs

### Requirement 7

**User Story:** As a DevOps engineer, I want detailed logging and error handling, so that I can troubleshoot issues during ingestion.

#### Acceptance Criteria

1. WHEN ingestion starts THEN the Ingest Command SHALL log the source bundle name and target GitLab URL
2. WHEN each major step completes THEN the Ingest Command SHALL log progress (extraction, project creation, push, artifacts)
3. IF any step fails THEN the Ingest Command SHALL display a clear error message with the failure reason
4. WHEN `--dry-run` flag is provided THEN the Ingest Command SHALL simulate all operations without making changes and log what would happen
5. WHEN ingestion completes successfully THEN the Ingest Command SHALL display a summary with project URL and statistics

### Requirement 8

**User Story:** As a DevOps engineer, I want to process multiple bundles in batch, so that I can efficiently transfer many projects.

#### Acceptance Criteria

1. WHEN `--drop-dir` is provided instead of `--tar` THEN the Ingest Command SHALL process all tar.gz files in the directory
2. WHEN processing multiple bundles THEN the Ingest Command SHALL continue with remaining bundles if one fails
3. WHEN batch processing completes THEN the Ingest Command SHALL display a summary showing successful and failed ingestions
4. WHEN `--parallel` flag is provided with a number THEN the Ingest Command SHALL process bundles in parallel up to the specified limit

