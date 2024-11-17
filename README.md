# gdrive-sync-python-util

This is a Python utility I created primarily for *personal use* and/or example code (i.e. not intended for extensive use)
to synchronize local files with Google Drive using service account credentials.
It provides basic functionality for uploading, downloading, updating, and syncing files between a local system and Google Drive.

If you are looking for something you want to use in a larger scale consider using a tool like rclone.

## Features

- **Upload files to Google Drive**: Upload a local file to your Google Drive using service account credentials.
- **Download files from Google Drive**: Download files from your Google Drive to your local system.
- **Update files on Google Drive**: Update existing files on Google Drive with new local versions.
- **Sync files**: Synchronize files between a local system and Google Drive, ensuring the most up-to-date version is reflected on both sides.

## How It Works

The script works by reading a configuration file (`sync.json`),
which specifies the files to synchronize,
the paths, and the Google Drive folder where they should be uploaded or downloaded from.
It compares the local modification times with the remote ones to decide whether to upload, download, or update a file.

## Usage

1. **Configuration (`sync.json`)**

    The `sync.json` file should contain information about your Google Drive credentials, root folder ID, and a list of files to synchronize. Here's an example:

    ```json
    {
        "details": [
            {
                "credentials_file": "path/to/credentials.json",
                "root_folder": "root_folder_id_on_google_drive",
                "files": [
                    {
                        "path": "local/path/to/file1.txt",
                        "id": "remote_file_id1"
                    },
                    {
                        "path": "local/path/to/file2.txt",
                        "id": null
                    }
                ]
            }
        ]
    }
    ```

2. **Running the Script**

    After configuring the `sync.json` file, simply run the script:

    ```bash
    python sync_script.py
    ```

    This will perform the synchronization as defined in the configuration file.

## Installation

To run this, you'll need to install the required dependencies. You can install them via `pip` using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Disclaimer

This utility was created primarily for personal use and may not be as feature-rich or user-friendly as other solutions available.
Feel free to fork or modify it,
but note that it's not intended for widespread distribution or use.

This project is not actively maintained but might get occasional updates as I improve it for my own use.
