"""S3 Client for downloading mapping dictionary from S3-compatible storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class S3Client:
    """Client for interacting with S3-compatible storage."""
    
    def __init__(
        self,
        endpoint_url: str,
        bucket_name: str,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = "us-east-1",
        verify_ssl: bool = True
    ):
        """Initialize S3 client.
        
        Args:
            endpoint_url: S3 endpoint URL (e.g., https://s3.internal.company)
            bucket_name: Bucket name containing the mapping dictionary
            access_key: AWS access key (optional if using IAM roles)
            secret_key: AWS secret key (optional if using IAM roles)
            region: AWS region (default: us-east-1)
            verify_ssl: Whether to verify SSL certificates
        """
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for S3 functionality. "
                "Install with: pip install boto3"
            )
        
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.verify_ssl = verify_ssl
        
        # Create S3 client
        session_kwargs = {}
        if access_key and secret_key:
            session_kwargs = {
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key
            }
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            region_name=region,
            verify=verify_ssl,
            **session_kwargs
        )
    
    def download_mapping_dict(self, object_key: str = "mapping-dict.json") -> Dict[str, Any]:
        """Download mapping dictionary from S3.
        
        Args:
            object_key: S3 object key for the mapping dictionary
            
        Returns:
            Dictionary containing the mappings
            
        Raises:
            ClientError: If download fails
            json.JSONDecodeError: If file is not valid JSON
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            # Read and parse JSON
            content = response['Body'].read().decode('utf-8')
            mapping_dict = json.loads(content)
            
            return mapping_dict
            
        except NoCredentialsError:
            raise RuntimeError(
                "No AWS credentials found. Please provide access_key and secret_key "
                "or configure AWS credentials."
            )
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(
                    f"Mapping dictionary not found in S3: {object_key}"
                )
            elif error_code == 'NoSuchBucket':
                raise RuntimeError(
                    f"S3 bucket not found: {self.bucket_name}"
                )
            else:
                raise RuntimeError(
                    f"Failed to download mapping dictionary: {str(e)}"
                )
    
    def save_mapping_dict_locally(
        self,
        mapping_dict: Dict[str, Any],
        local_path: Path
    ) -> None:
        """Save mapping dictionary to local file.
        
        Args:
            mapping_dict: Dictionary to save
            local_path: Local file path
        """
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_dict, f, indent=2, ensure_ascii=False)
    
    def test_connection(self) -> bool:
        """Test S3 connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False


def load_mapping_dict(local_path: Path) -> Dict[str, Any]:
    """Load mapping dictionary from local file.
    
    Args:
        local_path: Path to local mapping dictionary file
        
    Returns:
        Dictionary containing the mappings
    """
    if not local_path.exists():
        return {"mappings": {}}
    
    with open(local_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_internal_repo_info(
    mapping_dict: Dict[str, Any],
    external_name: str
) -> Dict[str, str] | None:
    """Get internal repository information from external name.
    
    Args:
        mapping_dict: Mapping dictionary
        external_name: External repository name (from bundle)
        
    Returns:
        Dictionary with internal_repo, internal_url, etc. or None if not found
    """
    mappings = mapping_dict.get("mappings", {})
    return mappings.get(external_name)

