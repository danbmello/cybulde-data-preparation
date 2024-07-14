import os

from typing import Any

import yaml

from fsspec import AbstractFileSystem, filesystem

GCS_PREFIX = "gs://"
GCS_FILE_SYSTEM_NAME = "gcs"
LOCAL_FILE_SYSTEM_NAME = "file"
TMP_FILE_PATH = "/tmp/"


def choose_file_system(path: str) -> AbstractFileSystem:
    # Based on path return file system name.
    return filesystem(GCS_FILE_SYSTEM_NAME) if path.startswith(GCS_PREFIX) else filesystem(LOCAL_FILE_SYSTEM_NAME)


# Our own open context manager.
def open_file(path: str, mode: str = "r") -> Any:
    file_system = choose_file_system(path)
    return file_system.open(path, mode)