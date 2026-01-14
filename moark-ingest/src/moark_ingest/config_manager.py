"""Configuration manager for profiles and repository mappings.

This module provides functionality to manage configuration profiles and
repository name mappings for the airgap-git-relay system.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Profile:
    """Configuration profile for a team/project."""
    name: str
    description: str = ""
    gitlab_url: str | None = None
    remote_template: str | None = None
    output_dir: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        """Create profile from dictionary."""
        return cls(**data)


@dataclass
class MappingEntry:
    """Single mapping from external to internal repo name."""
    external_name: str
    internal_name: str
    added_at: str = field(default_factory=_now_iso)
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert mapping entry to dictionary."""
        return {
            "internal_name": self.internal_name,
            "added_at": self.added_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, external_name: str, data: dict[str, Any]) -> MappingEntry:
        """Create mapping entry from dictionary."""
        return cls(
            external_name=external_name,
            internal_name=data["internal_name"],
            added_at=data.get("added_at", _now_iso()),
            notes=data.get("notes"),
        )


class ConfigManager:
    """Manages profiles, mappings, and settings.
    
    Directory structure:
        config_dir/
        ├── profiles.json           # Profile definitions
        ├── mappings/
        │   ├── default.json        # Default profile mappings
        │   └── <profile>.json      # Other profile mappings
        └── backups/                # Backup files
    """

    DEFAULT_PROFILE = "default"

    def __init__(self, config_dir: Path | str):
        """Initialize with configuration directory.
        
        Args:
            config_dir: Path to the configuration directory.
        """
        self.config_dir = Path(config_dir)
        self.profiles_file = self.config_dir / "profiles.json"
        self.mappings_dir = self.config_dir / "mappings"
        self.backups_dir = self.config_dir / "backups"
        
        self._ensure_directories()
        self._ensure_default_profile()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.mappings_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)

    def _ensure_default_profile(self) -> None:
        """Ensure default profile exists."""
        if not self.profiles_file.exists():
            default_profile = Profile(name=self.DEFAULT_PROFILE, description="Default profile")
            self._save_profiles_data({
                "active_profile": self.DEFAULT_PROFILE,
                "profiles": {self.DEFAULT_PROFILE: default_profile.to_dict()}
            })
            # Create default mapping file
            self._save_mappings_data(self.DEFAULT_PROFILE, {"profile": self.DEFAULT_PROFILE, "mappings": {}})

    def _load_profiles_data(self) -> dict[str, Any]:
        """Load profiles data from file."""
        if not self.profiles_file.exists():
            return {"active_profile": self.DEFAULT_PROFILE, "profiles": {}}
        return self._load_json_or_yaml(self.profiles_file)

    def _save_profiles_data(self, data: dict[str, Any]) -> None:
        """Save profiles data to file."""
        self._save_json(self.profiles_file, data)

    def _get_mapping_file(self, profile: str) -> Path:
        """Get the mapping file path for a profile."""
        return self.mappings_dir / f"{profile}.json"

    def _load_mappings_data(self, profile: str) -> dict[str, Any]:
        """Load mappings data for a profile."""
        mapping_file = self._get_mapping_file(profile)
        if not mapping_file.exists():
            return {"profile": profile, "mappings": {}}
        return self._load_json_or_yaml(mapping_file)

    def _save_mappings_data(self, profile: str, data: dict[str, Any]) -> None:
        """Save mappings data for a profile."""
        mapping_file = self._get_mapping_file(profile)
        self._save_json(mapping_file, data)

    def _load_json_or_yaml(self, file_path: Path) -> dict[str, Any]:
        """Load data from JSON or YAML file."""
        content = file_path.read_text(encoding="utf-8")
        
        if file_path.suffix in (".yaml", ".yml"):
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required to load YAML files. Install with: pip install pyyaml")
            return yaml.safe_load(content)
        
        return json.loads(content)

    def _save_json(self, file_path: Path, data: dict[str, Any]) -> None:
        """Save data to JSON file."""
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _create_backup(self, file_path: Path) -> Path | None:
        """Create a backup of a file before modification.
        
        Returns:
            Path to backup file, or None if source doesn't exist.
        """
        if not file_path.exists():
            return None
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backups_dir / backup_name
        shutil.copy2(file_path, backup_path)
        return backup_path

    # Profile Management

    def list_profiles(self) -> list[Profile]:
        """List all profiles.
        
        Returns:
            List of Profile objects.
        """
        data = self._load_profiles_data()
        return [Profile.from_dict(p) for p in data.get("profiles", {}).values()]

    def get_profile(self, name: str) -> Profile | None:
        """Get a profile by name.
        
        Args:
            name: Profile name.
            
        Returns:
            Profile object or None if not found.
        """
        data = self._load_profiles_data()
        profile_data = data.get("profiles", {}).get(name)
        if profile_data:
            return Profile.from_dict(profile_data)
        return None

    def create_profile(self, name: str, description: str = "") -> Profile:
        """Create a new profile.
        
        Args:
            name: Profile name.
            description: Profile description.
            
        Returns:
            Created Profile object.
            
        Raises:
            ValueError: If profile already exists.
        """
        data = self._load_profiles_data()
        if name in data.get("profiles", {}):
            raise ValueError(f"Profile '{name}' already exists")
        
        profile = Profile(name=name, description=description)
        
        if "profiles" not in data:
            data["profiles"] = {}
        data["profiles"][name] = profile.to_dict()
        
        self._save_profiles_data(data)
        
        # Create mapping file for the profile
        self._save_mappings_data(name, {"profile": name, "mappings": {}})
        
        return profile

    def update_profile(self, name: str, **kwargs: Any) -> Profile:
        """Update a profile.
        
        Args:
            name: Profile name.
            **kwargs: Fields to update.
            
        Returns:
            Updated Profile object.
            
        Raises:
            ValueError: If profile doesn't exist.
        """
        data = self._load_profiles_data()
        if name not in data.get("profiles", {}):
            raise ValueError(f"Profile '{name}' not found")
        
        profile_data = data["profiles"][name]
        for key, value in kwargs.items():
            if key in profile_data and key != "name":
                profile_data[key] = value
        profile_data["updated_at"] = _now_iso()
        
        self._save_profiles_data(data)
        return Profile.from_dict(profile_data)

    def delete_profile(self, name: str) -> bool:
        """Delete a profile.
        
        Args:
            name: Profile name.
            
        Returns:
            True if deleted, False if not found.
            
        Raises:
            ValueError: If trying to delete the default profile.
        """
        if name == self.DEFAULT_PROFILE:
            raise ValueError("Cannot delete the default profile")
        
        data = self._load_profiles_data()
        if name not in data.get("profiles", {}):
            return False
        
        del data["profiles"][name]
        
        # Update active profile if needed
        if data.get("active_profile") == name:
            data["active_profile"] = self.DEFAULT_PROFILE
        
        self._save_profiles_data(data)
        
        # Delete mapping file
        mapping_file = self._get_mapping_file(name)
        if mapping_file.exists():
            mapping_file.unlink()
        
        return True

    def export_profile(self, name: str) -> dict[str, Any]:
        """Export a profile (excluding sensitive credentials).
        
        Args:
            name: Profile name.
            
        Returns:
            Dictionary with profile data and mappings.
            
        Raises:
            ValueError: If profile doesn't exist.
        """
        profile = self.get_profile(name)
        if not profile:
            raise ValueError(f"Profile '{name}' not found")
        
        mappings = self.get_mappings(name)
        
        # Export without sensitive fields
        export_data = profile.to_dict()
        # Remove any potential sensitive fields (future-proofing)
        sensitive_fields = ["password", "token", "secret", "credential", "api_key"]
        for field_name in list(export_data.keys()):
            if any(s in field_name.lower() for s in sensitive_fields):
                del export_data[field_name]
        
        return {
            "profile": export_data,
            "mappings": {ext: entry.to_dict() for ext, entry in mappings.items()}
        }

    def import_profile(self, data: dict[str, Any]) -> Profile:
        """Import a profile from exported data.
        
        Args:
            data: Exported profile data.
            
        Returns:
            Imported Profile object.
            
        Raises:
            ValueError: If profile data is invalid or profile already exists.
        """
        if "profile" not in data:
            raise ValueError("Invalid import data: missing 'profile' key")
        
        profile_data = data["profile"]
        name = profile_data.get("name")
        if not name:
            raise ValueError("Invalid import data: missing profile name")
        
        # Check if profile exists
        if self.get_profile(name):
            raise ValueError(f"Profile '{name}' already exists")
        
        # Create profile
        profile = self.create_profile(name, profile_data.get("description", ""))
        
        # Update with additional fields
        update_fields = {k: v for k, v in profile_data.items() 
                        if k not in ("name", "description", "created_at", "updated_at")}
        if update_fields:
            profile = self.update_profile(name, **update_fields)
        
        # Import mappings
        if "mappings" in data:
            for external, mapping_data in data["mappings"].items():
                self.add_mapping(
                    name, 
                    external, 
                    mapping_data["internal_name"],
                    mapping_data.get("notes", "")
                )
        
        return profile


    # Mapping Management

    def get_mappings(self, profile: str) -> dict[str, MappingEntry]:
        """Get all mappings for a profile.
        
        Args:
            profile: Profile name.
            
        Returns:
            Dictionary of external name to MappingEntry.
        """
        data = self._load_mappings_data(profile)
        return {
            ext: MappingEntry.from_dict(ext, entry)
            for ext, entry in data.get("mappings", {}).items()
        }

    def add_mapping(
        self, 
        profile: str, 
        external: str, 
        internal: str, 
        notes: str = ""
    ) -> MappingEntry:
        """Add a new mapping.
        
        Args:
            profile: Profile name.
            external: External repository name.
            internal: Internal repository name.
            notes: Optional notes.
            
        Returns:
            Created MappingEntry.
        """
        mapping_file = self._get_mapping_file(profile)
        self._create_backup(mapping_file)
        
        data = self._load_mappings_data(profile)
        
        entry = MappingEntry(
            external_name=external,
            internal_name=internal,
            notes=notes if notes else None
        )
        
        if "mappings" not in data:
            data["mappings"] = {}
        data["mappings"][external] = entry.to_dict()
        
        self._save_mappings_data(profile, data)
        return entry

    def remove_mapping(self, profile: str, external: str) -> bool:
        """Remove a mapping.
        
        Args:
            profile: Profile name.
            external: External repository name.
            
        Returns:
            True if removed, False if not found.
        """
        mapping_file = self._get_mapping_file(profile)
        self._create_backup(mapping_file)
        
        data = self._load_mappings_data(profile)
        
        if external not in data.get("mappings", {}):
            return False
        
        del data["mappings"][external]
        self._save_mappings_data(profile, data)
        return True

    def resolve_mapping(self, profile: str, external_name: str) -> str:
        """Resolve an external name to internal name.
        
        Args:
            profile: Profile name.
            external_name: External repository name.
            
        Returns:
            Internal name if mapping exists, otherwise the original external name.
        """
        mappings = self.get_mappings(profile)
        if external_name in mappings:
            return mappings[external_name].internal_name
        return external_name

    def validate_mappings(self, profile: str) -> list[str]:
        """Validate mappings configuration.
        
        Args:
            profile: Profile name.
            
        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        mapping_file = self._get_mapping_file(profile)
        
        if not mapping_file.exists():
            errors.append(f"Mapping file not found: {mapping_file}")
            return errors
        
        try:
            data = self._load_mappings_data(profile)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON syntax: {e}")
            return errors
        except Exception as e:
            errors.append(f"Error loading file: {e}")
            return errors
        
        if "mappings" not in data:
            errors.append("Missing 'mappings' key in configuration")
            return errors
        
        for external, entry in data.get("mappings", {}).items():
            if not isinstance(entry, dict):
                errors.append(f"Invalid entry for '{external}': expected object")
                continue
            if "internal_name" not in entry:
                errors.append(f"Missing 'internal_name' for '{external}'")
        
        return errors


def load_mapping_config(config_path: Path | str) -> dict[str, str]:
    """Load a mapping configuration file (JSON or YAML).
    
    This is a convenience function for loading mapping files directly
    without using the full ConfigManager.
    
    Args:
        config_path: Path to the mapping configuration file.
        
    Returns:
        Dictionary mapping external names to internal names.
    """
    path = Path(config_path)
    content = path.read_text(encoding="utf-8")
    
    if path.suffix in (".yaml", ".yml"):
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required to load YAML files")
        data = yaml.safe_load(content)
    else:
        data = json.loads(content)
    
    # Handle both flat format and structured format
    if "mappings" in data:
        return {
            ext: entry["internal_name"] if isinstance(entry, dict) else entry
            for ext, entry in data["mappings"].items()
        }
    
    return data


def serialize_config(data: dict[str, Any], format: str = "json") -> str:
    """Serialize configuration data to string.
    
    Args:
        data: Configuration data.
        format: Output format ('json' or 'yaml').
        
    Returns:
        Serialized string.
    """
    if format == "yaml":
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML format")
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    return json.dumps(data, indent=2, ensure_ascii=False)


def deserialize_config(content: str, format: str = "json") -> dict[str, Any]:
    """Deserialize configuration string to data.
    
    Args:
        content: Configuration string.
        format: Input format ('json' or 'yaml').
        
    Returns:
        Configuration data.
    """
    if format == "yaml":
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML format")
        return yaml.safe_load(content)
    return json.loads(content)
