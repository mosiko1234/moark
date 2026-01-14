"""Bundle Scanner - Auto-detect and scan bundles from disk-on-key or drop folder."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class BundleInfo:
    """Information about a scanned bundle."""
    
    def __init__(
        self,
        file_path: Path,
        repo_name: str,
        size: int,
        created_at: str | None = None,
        has_submodules: bool = False,
        has_artifacts: bool = False
    ):
        self.file_path = file_path
        self.repo_name = repo_name
        self.size = size
        self.created_at = created_at
        self.has_submodules = has_submodules
        self.has_artifacts = has_artifacts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': str(self.file_path),
            'repo_name': self.repo_name,
            'size': self.size,
            'size_mb': round(self.size / (1024 * 1024), 2),
            'created_at': self.created_at,
            'has_submodules': self.has_submodules,
            'has_artifacts': self.has_artifacts
        }


def scan_bundles(directory: Path) -> List[BundleInfo]:
    """Scan directory for bundle files.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of BundleInfo objects
    """
    if not directory.exists():
        return []
    
    bundles = []
    
    # Find all .tar.gz files
    for bundle_file in directory.glob("*.tar.gz"):
        try:
            bundle_info = extract_bundle_info(bundle_file)
            if bundle_info:
                bundles.append(bundle_info)
        except Exception:
            # Skip invalid bundles
            continue
    
    # Sort by modification time (newest first)
    bundles.sort(key=lambda b: b.file_path.stat().st_mtime, reverse=True)
    
    return bundles


def extract_bundle_info(bundle_file: Path) -> BundleInfo | None:
    """Extract information from bundle file.
    
    Args:
        bundle_file: Path to bundle file
        
    Returns:
        BundleInfo object or None if invalid
    """
    try:
        # Get file size
        size = bundle_file.stat().st_size
        
        # Try to extract manifest
        with tarfile.open(bundle_file, 'r:gz') as tar:
            # Look for manifest.json
            manifest_path = None
            for member in tar.getmembers():
                if member.name.endswith('manifest.json'):
                    manifest_path = member
                    break
            
            if not manifest_path:
                # No manifest, derive repo name from filename
                repo_name = bundle_file.stem.replace('.tar', '')
                return BundleInfo(
                    file_path=bundle_file,
                    repo_name=repo_name,
                    size=size
                )
            
            # Read manifest
            manifest_file = tar.extractfile(manifest_path)
            if manifest_file:
                manifest_data = json.loads(manifest_file.read().decode('utf-8'))
                
                return BundleInfo(
                    file_path=bundle_file,
                    repo_name=manifest_data.get('repo_name', bundle_file.stem),
                    size=size,
                    created_at=manifest_data.get('packed_at'),
                    has_submodules=bool(manifest_data.get('submodules', [])),
                    has_artifacts=bool(manifest_data.get('artifacts', []))
                )
    
    except Exception:
        return None
    
    return None


def find_disk_on_key_paths() -> List[Path]:
    """Find potential disk-on-key mount points.
    
    Returns:
        List of potential mount point paths
    """
    import platform
    
    system = platform.system()
    potential_paths = []
    
    if system == 'Darwin':  # macOS
        volumes_dir = Path('/Volumes')
        if volumes_dir.exists():
            for volume in volumes_dir.iterdir():
                if volume.is_dir() and volume.name != 'Macintosh HD':
                    potential_paths.append(volume)
    
    elif system == 'Linux':
        # Check common mount points
        media_dir = Path('/media') / Path.home().name
        if media_dir.exists():
            for mount in media_dir.iterdir():
                if mount.is_dir():
                    potential_paths.append(mount)
        
        # Also check /mnt
        mnt_dir = Path('/mnt')
        if mnt_dir.exists():
            for mount in mnt_dir.iterdir():
                if mount.is_dir():
                    potential_paths.append(mount)
    
    elif system == 'Windows':
        # Check drives D: through Z:
        for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
            drive = Path(f'{letter}:/')
            if drive.exists():
                potential_paths.append(drive)
    
    return potential_paths


def auto_scan_for_bundles() -> List[BundleInfo]:
    """Auto-scan for bundles on disk-on-key.
    
    Returns:
        List of found bundles
    """
    all_bundles = []
    
    # Scan potential disk-on-key paths
    for path in find_disk_on_key_paths():
        bundles = scan_bundles(path)
        all_bundles.extend(bundles)
    
    return all_bundles

