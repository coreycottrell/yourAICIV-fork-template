# Google Drive Operations Skill

**Version:** 1.0.0
**Created:** 2026-02-04
**Author:** ${CIV_NAME} (CTO)

## Purpose

Full read/write access to Google Drive for documentation, file management, and agent deliverables.

## When to Use

- Uploading documentation to team folders
- Creating folder structures for projects
- Saving agent deliverables (specs, reports, designs)
- Downloading files shared by humans
- Organizing project files for human team visibility

## Service Account

```
Email: ${GDRIVE_SERVICE_ACCOUNT_EMAIL}
Access: Editor on all folders within "${CIV_NAME} Inbox"
```

## Available Folders

```
${CIV_NAME} Inbox/
├── 000. ${HUMAN_NAME} and ${PROJECT_NAME} Source of Truth Docs
├── 001. C Level and AI Training - ${CIV_NAME} (CTO)
├── 002. Marketing and Automation Expert (CMO)
├── 003. Sales and Money Making (CRO)
├── 004. Social Media Strategist (LinkedIn)
├── 005. Content Creation Specialist
├── 006. Strategic Planning (CSO)
├── 007. Technologist & Futurist - ${CIV_NAME} (CTO)
├── 008. Full Stack Developer
├── 009. AI/ML Engineer
├── 010. UI/UX Designer
├── 011. QA Engineer
├── 012. DevOps Engineer
├── 013. Data Scientist
├── 014. Data Engineer
└── 015. Security Engineer
```

## Usage

### Python API

```python
from tools.gdrive_manager import GDriveManager

manager = GDriveManager()

# List shared folders
folders = manager.list_shared_folders()

# Find a folder
folder_id = manager.find_folder("008. Full Stack Developer")

# List files in a folder
files = manager.list_files(folder_id)

# Upload a file to a path (creates folders if needed)
manager.upload_to_path(
    "/path/to/local/file.md",
    "001. ${PROJECT_NAME} platform build",  # Path within root folder
    root_folder_name="007. Technologist & Futurist - ${CIV_NAME} (CTO)"
)

# Upload content directly (no local file needed)
manager.upload_content_to_path(
    content="# Feature Spec\n\nThis is the spec...",
    filename="feature-spec.md",
    drive_path="Specs",
    root_folder_name="008. Full Stack Developer"
)

# Create folder structure
folder_id = manager.ensure_folder_path(
    "Project X/Phase 1/Designs",
    root_folder_id=some_folder_id
)

# Download a file
local_path = manager.download_file(file_id, Path("./downloads"))
```

### CLI Commands

```bash
# List folders shared with service account
python3 tools/gdrive_manager.py list-shared

# List files in a folder
python3 tools/gdrive_manager.py list "008. Full Stack Developer"

# Upload a file
python3 tools/gdrive_manager.py upload ./file.md "Path/In/Drive"

# Create a folder path
python3 tools/gdrive_manager.py mkdir "New Project/Docs"
```

## Agent Integration

When agents complete deliverables, they should upload to their respective folders:

| Agent | Folder |
|-------|--------|
| Full Stack Developer | 008. Full Stack Developer Training |
| AI/ML Engineer | 009. AI/ML Engineer Training |
| UI/UX Designer | 010. UI/UX Designer Training |
| QA Engineer | 011. QA Engineer Training |
| DevOps Engineer | 012. DevOps Engineer Training |
| Data Scientist | 013. Data Scientist Training |
| Data Engineer | 014. Data Engineer Training |
| Security Engineer | 015. Security Engineer |

## Credentials

- **Location:** `.credentials/google-drive-service-account.json`
- **Scope:** Full drive access (`https://www.googleapis.com/auth/drive`)
- **Type:** Service Account

## Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

## File Types Supported

| Extension | MIME Type |
|-----------|-----------|
| .md | text/markdown |
| .txt | text/plain |
| .html | text/html |
| .json | application/json |
| .py | text/x-python |
| .pdf | application/pdf |
| .png/.jpg | image/* |
| .csv | text/csv |

Google Docs/Sheets/Slides are automatically exported to PDF/CSV when downloading.
