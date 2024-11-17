"""
Module for synchronizing local files with Google Drive using service account credentials.

Classes:
    Syncable: Represents a file to be synchronized with its local path and optional remote file ID.
    ServiceAccount: Manages interactions with the Google Drive API for file upload, download, update, and synchronization.

Functions:
    sync_from_file(sync_json: Path) -> None: Reads synchronization details from a JSON file and performs file synchronization.
    main() -> None: Entry point for running the synchronization process.
"""

import json

from pathlib import Path                   
from datetime import datetime, timezone
from typing import Any, NoReturn, Optional, cast

from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest, MediaFileUpload
from google.oauth2 import service_account

class Syncable:
    """
    Represents a file to be synchronized.

    Attributes:
        path (Path): The local path to the file.
        id (Optional[str]): The unique ID of the file on Google Drive, if it exists.
    """
    def __init__(self, path: Path, file_id: Optional[str] = None):
        self.path = path
        self.id = file_id

class ServiceAccount: 
    """
    Handles Google Drive API operations using a service account.

    Attributes:
        SCOPES (list[str]): The Google Drive API scopes required for the operations.
        credentials (service_account.Credentials): The service account credentials.
        service (googleapiclient.discovery.Resource): The Google Drive API service instance.
        root (str): The root folder ID for operations on Google Drive.
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, credentials: service_account.Credentials, root_dir: str) -> None:
        self.credentials = credentials

        # Build the Drive service
        self.service = build('drive', 'v3', credentials=credentials)

        self.root = root_dir

    def upload(self, file: Syncable, folder_id: Optional[str] = None) -> Syncable | NoReturn:
        """
        Uploads a local file to Google Drive.

        Args:
            file (Syncable): The file to upload.
            folder_id (Optional[str]): The ID of the parent folder in Google Drive.
        """
        metadata: dict[str, Any] = {
                'name': file.path.name,
                'parents' : [folder_id if folder_id else self.root]
                }

        media = MediaFileUpload(str(file.path))

        request: HttpRequest = self.service.files().create(
                body = metadata,
                media_body=media,
                fields='id',
            )

        # Associate the new ID to the file
        file.id = request.execute().get('id')

        print(f"File uploaded successfully. File ID: {file.id}")

        return file


    def update(self, file: Syncable) -> None | NoReturn:
        """
        Updates an existing file on Google Drive with a local version.

        Args:
            file (Syncable): The file to update.
        """
        metadata: dict[str, Any] = {'name': file.path.name}

        media = MediaFileUpload(str(file.path))

        request: HttpRequest = self.service.files().update(
                body = metadata,
                fileId = file.id,
                media_body=media,
                )

        response = request.execute()
        print(f"File updated successfully. File ID: {response.get('id')}")


    def download(self, file: Syncable) -> None | NoReturn:
        """
        Downloads a file from Google Drive to the local system.

        Args:
            file (Syncable): The file to download.
        """
        request: HttpRequest = self.service.files().get_media(
                fileId = file.id,
                )

        response: bytes = request.execute()
        print(f"File {file.path} downloaded successfully.")

        file.path.write_bytes(response)

    def last_mod(self, file: Syncable) -> tuple[datetime, datetime]:
        """
        Gets the modification times of a file locally and on Google Drive.

        Args:
            file (Syncable): The file to check.

        Returns:
            tuple[datetime, datetime]: A tuple containing the local and remote modification times.
        """
        request: HttpRequest = self.service.files().get(
                fileId = file.id,
                fields='modifiedTime'
                )

        response = request.execute()

        local_modtime = datetime.fromtimestamp(file.path.stat().st_mtime, tz=timezone.utc)
        remote_modtime = datetime.fromisoformat(response.get('modifiedTime'))

        return local_modtime, remote_modtime

    def sync(self, file: Syncable) -> None:
        """
        Synchronizes a file between the local system and Google Drive.

        Args:
            file (Syncable): The file to synchronize.
        """
        if file.id == None:
            self.upload(file)
            return

        local_modtime, remote_modtime = self.last_mod(file)

        if local_modtime > remote_modtime:
            self.update(file)
            return

        if local_modtime < remote_modtime:
            self.download(file)
            return

    @staticmethod
    def credentials_from_file(path: Path) -> service_account.Credentials:
        """
        Loads service account credentials from a file.

        Args:
            path (Path): The path to the service account credentials file.

        Returns:
            service_account.Credentials: The loaded credentials.
        """
        return service_account.Credentials.from_service_account_file(
                str(path), scopes=ServiceAccount.SCOPES)
        

def sync_from_file(sync_json: Path) -> None:
    """
    Reads synchronization details from a JSON file and performs file synchronization.

    Args:
        sync_json (Path): Path to the JSON file containing synchronization details.
    """
    with sync_json.open() as f:
        # Example structure of `sync.json`:
        # {
        #     "details": [
        #         {
        #             "credentials_file": "path/to/credentials.json",
        #             "root_folder": "root_folder_id_on_google_drive",
        #             "files": [
        #                 {
        #                     "path": "local/path/to/file1.txt",
        #                     "id": "remote_file_id1"  # Optional: Leave null or omit if the file doesn't exist remotely yet.
        #                 },
        #                 {
        #                     "path": "local/path/to/file2.txt",
        #                     "id": null  # File not yet uploaded to Google Drive.
        #                 }
        #             ]
        #         },
        #         {
        #             "credentials_file": "path/to/other_credentials.json",
        #             "root_folder": "another_root_folder_id",
        #             "files": [
        #                 {
        #                     "path": "local/path/to/another_file.docx",
        #                     "id": "remote_file_id2"
        #                 }
        #             ]
        #         }
        #     ]
        # }
        sync_details: dict[str, list[dict[str, Any]]] = json.load(f)

    for details in sync_details["details"]:
        # load the credentials
        credentials_file = Path(details["credentials_file"])
        credentials = ServiceAccount.credentials_from_file(credentials_file)

        root_dir = details["root_folder"]

        # create service account instance
        service = ServiceAccount(credentials, root_dir)

        # perform the sync operations
        files_details: list[dict[str, str]] = details["files"]

        files = map(lambda file: 
                    Syncable(Path(file["path"]), file.get("id", None)),
                    files_details)

        for file, file_detail in zip(files, files_details):
            service.sync(file)
            
            # update the id
            file_detail["id"] = cast(str, file.id)

        # update the sync file
        with sync_json.open("w") as f:
            json.dump(sync_details, f, indent=4)


def main() -> None:
    """
    Entry point for running the synchronization process.
    """
    sync_from_file(Path("sync.json"))

if __name__ == "__main__":
    main()
