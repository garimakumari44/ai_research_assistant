from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional


@dataclass(slots=True)
class StoredDocument:
    """
    Result of storing a document.
    """

    storage_key: str
    path: Path
    size_bytes: int
    checksum: str


class DocumentStorage:
    """
    Local document storage abstraction.

    The ingestion pipeline should interact with this class rather
    than directly manipulating filesystem paths.

    Later this can be replaced with:

        S3
        MinIO
        Azure Blob Storage
        Google Cloud Storage
    """

    def __init__(
        self,
        root_path: str | Path = "storage/documents",
    ) -> None:
        self.root_path = Path(root_path)

        self.root_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def store(
        self,
        source: str | Path | BinaryIO,
        *,
        storage_key: Optional[str] = None,
    ) -> StoredDocument:
        """
        Store a document.

        Args:
            source:
                Local path or binary stream.

            storage_key:
                Optional logical storage key.

        Returns:
            StoredDocument
        """

        if storage_key is None:
            storage_key = self._generate_storage_key(
                source
            )

        safe_key = self._sanitize_key(
            storage_key
        )

        destination = self._resolve_key(
            safe_key
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Prevent accidental self-copy.
        if (
            isinstance(source, (str, Path))
            and Path(source).resolve()
            == destination.resolve()
        ):
            checksum = self._calculate_checksum(
                destination
            )

            return StoredDocument(
                storage_key=safe_key,
                path=destination,
                size_bytes=destination.stat().st_size,
                checksum=checksum,
            )

        if isinstance(source, (str, Path)):
            source_path = Path(source)

            if not source_path.exists():
                raise FileNotFoundError(
                    "Source document does not exist: "
                    f"{source_path}"
                )

            if not source_path.is_file():
                raise ValueError(
                    "Source document is not a file: "
                    f"{source_path}"
                )

            shutil.copy2(
                source_path,
                destination,
            )

        else:
            self._store_stream(
                source,
                destination,
            )

        checksum = self._calculate_checksum(
            destination
        )

        return StoredDocument(
            storage_key=safe_key,
            path=destination,
            size_bytes=destination.stat().st_size,
            checksum=checksum,
        )

    def exists(
        self,
        storage_key: str,
    ) -> bool:
        """
        Determine whether a stored document exists.
        """

        try:
            path = self._resolve_key(
                storage_key
            )
        except ValueError:
            return False

        return (
            path.exists()
            and path.is_file()
        )

    def get_path(
        self,
        storage_key: str,
    ) -> Path:
        """
        Resolve a storage key to its filesystem path.
        """

        path = self._resolve_key(
            storage_key
        )

        if not path.exists():
            raise FileNotFoundError(
                "Stored document does not exist: "
                f"{storage_key}"
            )

        if not path.is_file():
            raise ValueError(
                "Stored document path is not a file: "
                f"{storage_key}"
            )

        return path

    def delete(
        self,
        storage_key: str,
    ) -> None:
        """
        Delete a stored document.
        """

        path = self._resolve_key(
            storage_key
        )

        if path.exists():
            if not path.is_file():
                raise ValueError(
                    "Cannot delete non-file storage path: "
                    f"{storage_key}"
                )

            path.unlink()

    def _resolve_key(
        self,
        storage_key: str,
    ) -> Path:
        safe_key = self._sanitize_key(
            storage_key
        )

        root = self.root_path.resolve()

        path = (
            root / safe_key
        ).resolve()

        # Defense against path traversal.
        if path != root and root not in path.parents:
            raise ValueError(
                "Storage key escapes storage root."
            )

        return path

    @staticmethod
    def _sanitize_key(
        storage_key: str,
    ) -> str:
        """
        Sanitize a logical storage key.

        Nested keys such as:

            papers/123/document.pdf

        are allowed.

        Path traversal such as:

            ../../secret.pdf

        is rejected.
        """

        if not storage_key:
            raise ValueError(
                "Storage key cannot be empty."
            )

        key = storage_key.replace(
            "\\",
            "/",
        ).strip("/")

        parts = key.split("/")

        cleaned_parts: list[str] = []

        for part in parts:
            part = part.strip()

            if not part:
                continue

            if part in (".", ".."):
                raise ValueError(
                    "Invalid path component in storage key."
                )

            cleaned_parts.append(part)

        if not cleaned_parts:
            raise ValueError(
                "Invalid storage key."
            )

        return "/".join(cleaned_parts)

    @staticmethod
    def _generate_storage_key(
        source: str | Path | BinaryIO,
    ) -> str:
        """
        Generate a deterministic storage key.

        For file paths, the source path is used as a temporary
        identity. The actual content checksum is calculated after
        storage and should be persisted by DocumentService.
        """

        if isinstance(source, (str, Path)):
            path = Path(source)

            filename = (
                path.name
                or "document.pdf"
            )

            digest = hashlib.sha256(
                str(
                    path.absolute()
                ).encode("utf-8")
            ).hexdigest()[:16]

            return (
                f"documents/"
                f"{digest}/"
                f"{filename}"
            )

        return "documents/document.bin"

    @staticmethod
    def _calculate_checksum(
        path: Path,
    ) -> str:
        """
        Calculate SHA-256 checksum of a stored document.
        """

        digest = hashlib.sha256()

        with path.open("rb") as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _store_stream(
        source: BinaryIO,
        destination: Path,
    ) -> None:
        """
        Store a binary stream.
        """

        with destination.open("wb") as output:
            shutil.copyfileobj(
                source,
                output,
            )