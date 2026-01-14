# ⛵ Moses in the Ark - Usage Guide

## Overview

**Moses in the Ark - Ingest** is the tool for developers in air-gapped networks. It allows uploading bundles created in internet-connected networks (using **Moses in the Ark - Pack**) to internal repositories.

## Complete Workflow

### Step 1: Installation (One Time)

```bash
cd moark-ingest
pip install ".[ui]"
```

This installs the tool with all dependencies, including:
- `textual` - For the terminal user interface
- `boto3` - For S3 connection
- `typer` - For CLI

### Step 2: First Run - S3 Configuration

On first run, configure the S3 connection where the mapping dictionary is stored:

```bash
moark-ingest-ui
```

In the opened interface:

1. **Fill in S3 details**:
   - **S3 Endpoint URL**: `https://s3.internal.company` (or any other S3 address)
   - **S3 Bucket Name**: `moark-mappings` (or your bucket name)
   - **S3 Access Key**: Access key (optional)
   - **S3 Secret Key**: Secret key (optional)
   - **Disable SSL Verification**: Check if there are SSL certificate issues

2. **Click "💾 Save & Download Mapping"**:
   - Settings will be saved in `~/.moark/s3_settings.json`
   - Mapping dictionary will be automatically downloaded from S3
   - The table will update with the mappings

### Step 3: Transfer Bundle from Disk-on-Key

After a developer in the internet network created a bundle using `moark-pack-ui` and transferred it on a disk-on-key:

1. **Insert the Disk-on-Key into the computer**

2. **Auto Scan**:
   - Click "🔎 Auto Scan"
   - The system will automatically scan all connected disk-on-key devices
   - All found bundles will appear in the "Available Bundles" table

   **Or scan a specific path**:
   - Enter the path in "Scan Path" (e.g., `/Volumes/USB/bundles`)
   - Click "📁 Scan Path"

3. **Select Bundle**:
   - Click on the appropriate row in the Bundles table
   - The system will automatically check if a mapping exists for the bundle
   - If a mapping exists, you'll see: "✅ Mapping found: internal-repo-name"
   - If no mapping exists, you'll see: "⚠️ No mapping found"

### Step 4: Upload to Internal Repository

1. **Enter internal Git credentials**:
   - **Target Git Username**: Your username in internal Git
   - **Target Git Password**: Your password

2. **Select options** (optional):
   - **Verify Repository**: Verify repository integrity before upload
   - **Force Push**: Force upload (use carefully!)

3. **Click "⬆️ Upload Bundle"**:
   - The system will extract the bundle
   - Upload the code to the appropriate internal repository (according to mapping)
   - Display progress in the log
   - Update the history table

### Step 5: Verification and History

- **"Recent Ingests" Table**: Shows recent uploads
- **"🔄 Refresh" Button**: Refreshes all data (mappings, bundles, history)
- **"Repository Mappings" Table**: Shows all available mappings

## Example Mapping Dictionary

The dictionary file in S3 should be in the following format:

```json
{
  "_description": "Repository name mapping dictionary",
  "_version": "1.0",
  "_last_updated": "2024-01-15T10:00:00Z",
  "mappings": {
    "yossi": {
      "internal_repo": "project-alpha",
      "internal_url": "https://git.internal.company/security/project-alpha.git",
      "description": "Security project - classified",
      "team": "security-team",
      "classification": "secret"
    },
    "david-app": {
      "internal_repo": "customer-portal",
      "internal_url": "https://git.internal.company/products/customer-portal.git",
      "description": "Customer-facing portal",
      "team": "product-team",
      "classification": "internal"
    }
  }
}
```

## CLI Usage (Without UI)

If you prefer working with CLI:

```bash
# Download mapping dictionary from S3 (one time)
# Need to set variables:
export AWS_ENDPOINT_URL=https://s3.internal.company
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Manual upload
moark-ingest \
  --tar /Volumes/USB/yossi.tar.gz \
  --remote-template "https://git-user:password@git.internal.company/{repo}.git" \
  --username git-user \
  --password your-password \
  --profile default
```

## Tips and Best Practices

1. **Update Mapping Dictionary**:
   - Click "💾 Save & Download Mapping" to download the latest version of the dictionary
   - Do this before each upload of a new bundle

2. **Auto Scan**:
   - Use "Auto Scan" instead of manually entering paths
   - This saves time and prevents errors

3. **Verify Mapping**:
   - Before uploading, ensure there's a mapping for the bundle
   - If no mapping exists, contact the system administrator to add the mapping to S3

4. **Save Credentials**:
   - Git credentials are not saved for security reasons
   - You'll need to enter them for each upload

5. **Check History**:
   - Use the history table to track previous uploads
   - This helps identify issues or duplicates

## Troubleshooting

### "❌ Error: Cannot connect to S3"
- Check the S3 Endpoint address
- Ensure there's network access to S3
- If there are SSL issues, check "Disable SSL Verification"

### "❌ Error: No mapping found for repository"
- The dictionary doesn't contain a mapping for this bundle
- Download an updated dictionary from S3
- Contact the system administrator to add the mapping

### "❌ Error: Bundle file does not exist"
- Ensure the disk-on-key is connected
- Scan the path again
- Check that the bundle file wasn't deleted

### "❌ Upload operation failed"
- Check Git credentials
- Ensure you have permissions to update the internal repository
- Check the log for more details

## For Support

For support or questions, contact: **Moshe Eliya**
