
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from app.db.models.document import Document
from app.ingestion.documents.downloader import DocumentDownloader
from app.ingestion.documents.extractor import (
    DocumentExtraction,
    DocumentExtractor,
)
from app.ingestion.documents.parser import (
    DocumentParseResult,
    DocumentParser,
)
from app.ingestion.documents.resolver import (
    DocumentResolution,
    DocumentResolver,
)
from app.ingestion.documents.storage import (
    DocumentStorage,
    StoredDocument,
)
from app.knowledge.chunking.semantic import SemanticChunker
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.paper_repository import PaperRepository
from app.repositories.section_repository import SectionRepository


logger = logging.getLogger(__name__)


class DocumentService:
    """
    Coordinates the complete paper-document ingestion pipeline.

    Pipeline:

        Paper
          ↓
        DocumentResolver
          ↓
        DocumentDownloader
          ↓
        DocumentStorage
          ↓
        DocumentExtractor
          ↓
        DocumentParser
          ↓
        Document
          ↓
        DocumentSection
          ↓
        Chunk
    """

    def __init__(
        self,
        *,
        paper_repository: PaperRepository,
        document_repository: DocumentRepository,
        section_repository: SectionRepository,
        chunk_repository: ChunkRepository,
        document_resolver: DocumentResolver | None = None,
        document_downloader: DocumentDownloader | None = None,
        document_storage: DocumentStorage | None = None,
        document_extractor: DocumentExtractor | None = None,
        document_parser: DocumentParser | None = None,
        chunker: SemanticChunker | None = None,
    ) -> None:
        self.paper_repository = paper_repository
        self.document_repository = document_repository
        self.section_repository = section_repository
        self.chunk_repository = chunk_repository

        self.resolver = (
            document_resolver
            or DocumentResolver()
        )

        self.downloader = (
            document_downloader
            or DocumentDownloader()
        )

        self.storage = (
            document_storage
            or DocumentStorage()
        )

        self.extractor = (
            document_extractor
            or DocumentExtractor()
        )

        self.parser = (
            document_parser
            or DocumentParser()
        )

        self.chunker = (
            chunker
            or SemanticChunker()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ingest_paper_document(
        self,
        paper_id: int | str,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Ingest the document associated with a paper.

        If a document already exists and is fully populated with
        sections and chunks, it is considered already ingested
        unless force=True.

        Incomplete documents are automatically reprocessed.
        """

        normalized_paper_id = (
            self._normalize_paper_id(paper_id)
        )

        paper = await self.paper_repository.get_by_id(
            normalized_paper_id
        )

        if paper is None:
            raise ValueError(
                f"Paper {normalized_paper_id} does not exist."
            )

        existing = await self._get_document_for_paper(
            normalized_paper_id
        )

        if existing is not None and not force:
            section_count = (
                await self.section_repository.count_by_document_id(
                    existing.id
                )
            )

            chunk_count = (
                await self.chunk_repository.count_by_document(
                    existing.id
                )
            )

            if section_count > 0 and chunk_count > 0:
                return {
                    "status": "already_ingested",
                    "document_id": str(existing.id),
                    "paper_id": normalized_paper_id,
                    "sections": section_count,
                    "chunks": chunk_count,
                }

            logger.info(
                "Existing document is incomplete; reprocessing: "
                "paper_id=%s document_id=%s sections=%s chunks=%s",
                normalized_paper_id,
                existing.id,
                section_count,
                chunk_count,
            )

        return await self._ingest_paper(
            paper=paper,
            paper_id=normalized_paper_id,
            existing_document=existing,
        )

    async def ingest_document(
        self,
        document_id: UUID | str,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        """
        Process an already-created Document.

        This is the entry point used by the Celery ingestion worker.
        """

        document_uuid = self._normalize_uuid(
            document_id
        )

        document = await self.document_repository.get_by_id(
            document_uuid
        )

        if document is None:
            raise ValueError(
                f"Document {document_uuid} does not exist."
            )

        if document.paper_id is None:
            raise ValueError(
                f"Document {document_uuid} has no paper_id."
            )

        if not force:
            section_count = (
                await self.section_repository.count_by_document_id(
                    document.id
                )
            )

            chunk_count = (
                await self.chunk_repository.count_by_document(
                    document.id
                )
            )

            if section_count > 0 and chunk_count > 0:
                return {
                    "status": "already_ingested",
                    "document_id": str(document.id),
                    "paper_id": int(document.paper_id),
                    "sections": section_count,
                    "chunks": chunk_count,
                }

        paper_id = int(document.paper_id)

        paper = await self.paper_repository.get_by_id(
            paper_id
        )

        if paper is None:
            raise ValueError(
                f"Paper {paper_id} does not exist."
            )

        return await self._ingest_paper(
            paper=paper,
            paper_id=paper_id,
            existing_document=document,
        )

    # ------------------------------------------------------------------
    # Core ingestion
    # ------------------------------------------------------------------

    async def _ingest_paper(
        self,
        *,
        paper: Any,
        paper_id: int,
        existing_document: Document | None,
    ) -> dict[str, Any]:
        """
        Download, extract, parse, and persist a paper document.
        """

        logger.info(
            "Starting document ingestion: paper_id=%s",
            paper_id,
        )

        # --------------------------------------------------------------
        # 1. Resolve source document
        # --------------------------------------------------------------

        resolution = self.resolver.resolve(
            paper
        )

        if resolution is None:
            raise ValueError(
                f"Unable to resolve a document source "
                f"for paper {paper_id}."
            )

        logger.info(
            "Resolved document: paper_id=%s url=%s source=%s",
            paper_id,
            resolution.document_url,
            resolution.source,
        )

        # --------------------------------------------------------------
        # 2. Download PDF
        # --------------------------------------------------------------

        download_directory = (
            self.storage.root_path
            / "downloads"
            / str(paper_id)
        )

        filename = self._build_download_filename(
            paper=paper,
            resolution=resolution,
        )

        downloaded = self.downloader.download(
            resolution.document_url,
            download_directory,
            filename=filename,
        )

        logger.info(
            "Downloaded document: paper_id=%s path=%s size=%s",
            paper_id,
            downloaded.path,
            downloaded.size_bytes,
        )

        # --------------------------------------------------------------
        # 3. Store canonical document
        # --------------------------------------------------------------

        storage_key = self._build_storage_key(
            paper_id=paper_id,
            source_url=resolution.document_url,
            filename=filename,
        )

        stored = self.storage.store(
            downloaded.path,
            storage_key=storage_key,
        )

        logger.info(
            "Stored document: paper_id=%s path=%s checksum=%s",
            paper_id,
            stored.path,
            stored.checksum,
        )

        # --------------------------------------------------------------
        # 4. Extract text from PDF
        # --------------------------------------------------------------

        extraction = self.extractor.extract(
            stored.path
        )

        if not self.extractor.has_extractable_text(
            extraction
        ):
            raise ValueError(
                f"Document for paper {paper_id} contains "
                "insufficient extractable text."
            )

        logger.info(
            "Extracted document: paper_id=%s pages=%s text_length=%s",
            paper_id,
            extraction.page_count,
            len(extraction.text),
        )

        # --------------------------------------------------------------
        # 5. Parse logical sections
        # --------------------------------------------------------------

        parsed = self.parser.parse(
            extraction
        )

        if not parsed.full_text.strip():
            raise ValueError(
                f"Document for paper {paper_id} contains "
                "no extractable text."
            )

        if not parsed.sections:
            raise ValueError(
                f"Document for paper {paper_id} produced "
                "no sections."
            )

        logger.info(
            "Parsed document: paper_id=%s sections=%s pages=%s",
            paper_id,
            len(parsed.sections),
            parsed.page_count,
        )

        # --------------------------------------------------------------
        # 6. Persist Document
        # --------------------------------------------------------------

        document = await self._persist_document(
            paper=paper,
            paper_id=paper_id,
            existing_document=existing_document,
            resolution=resolution,
            downloaded=downloaded,
            stored=stored,
            extraction=extraction,
            parsed=parsed,
        )

        # --------------------------------------------------------------
        # 7. Persist Sections + Chunks
        # --------------------------------------------------------------

        section_count, chunk_count = (
            await self._persist_sections_and_chunks(
                document=document,
                parsed=parsed,
            )
        )

        logger.info(
            "Document ingestion completed: "
            "paper_id=%s document_id=%s sections=%s chunks=%s",
            paper_id,
            document.id,
            section_count,
            chunk_count,
        )

        return {
            "status": "ingested",
            "paper_id": paper_id,
            "document_id": str(document.id),
            "sections": section_count,
            "chunks": chunk_count,
            "page_count": parsed.page_count,
            "text_length": len(parsed.full_text),
        }

    # ------------------------------------------------------------------
    # Document persistence
    # ------------------------------------------------------------------

    async def _persist_document(
        self,
        *,
        paper: Any,
        paper_id: int,
        existing_document: Document | None,
        resolution: DocumentResolution,
        downloaded: Any,
        stored: StoredDocument,
        extraction: DocumentExtraction,
        parsed: DocumentParseResult,
    ) -> Document:
        metadata = self._build_document_metadata(
            paper=paper,
            resolution=resolution,
            downloaded=downloaded,
            stored=stored,
            extraction=extraction,
            parsed=parsed,
        )

        values = {
            "name": self._build_document_name(
                paper=paper,
                resolution=resolution,
            ),
            "description": getattr(
                paper,
                "abstract",
                None,
            ),
            "document_type": "pdf",
            "status": "active",
            "paper_id": paper_id,
            "metadata_": metadata,
        }

        if existing_document is None:
            document = await self.document_repository.create(
                values
            )

            logger.info(
                "Created document: "
                "paper_id=%s document_id=%s",
                paper_id,
                document.id,
            )

            return document

        document = existing_document

        # Remove old chunks first because chunks reference sections.
        await self.chunk_repository.delete_by_document_id(
            document.id
        )

        # Then remove old sections.
        await self.section_repository.delete_by_document_id(
            document.id
        )

        for field_name, value in values.items():
            setattr(
                document,
                field_name,
                value,
            )

        await self.document_repository.update(
            document
        )

        logger.info(
            "Updated document for re-ingestion: "
            "paper_id=%s document_id=%s",
            paper_id,
            document.id,
        )

        return document

    async def _persist_sections_and_chunks(
        self,
        *,
        document: Document,
        parsed: DocumentParseResult,
    ) -> tuple[int, int]:
        section_count = 0
        chunk_count = 0

        for section_index, parsed_section in enumerate(
            parsed.sections
        ):
            content = parsed_section.content.strip()

            if not content:
                continue

            section_type = (
                "document"
                if len(parsed.sections) == 1
                else "section"
            )

            section = await self.section_repository.create(
                {
                    "document_id": document.id,
                    "section_index": section_index,
                    "title": parsed_section.title,
                    "section_type": section_type,
                    "level": parsed_section.level,
                    "content": content,
                    "page_start": parsed_section.page_start,
                    "page_end": parsed_section.page_end,
                    "metadata_": {
                        "source_order": parsed_section.order,
                    },
                }
            )

            section_count += 1

            chunk_result = self.chunker.chunk(
                content,
                document_id=document.id,
                metadata={
                    "section_id": str(section.id),
                    "section_index": section_index,
                    "section_title": parsed_section.title,
                    "page_start": parsed_section.page_start,
                    "page_end": parsed_section.page_end,
                },
            )

            chunk_result.validate()

            chunk_values: list[dict[str, Any]] = []

            for chunk in chunk_result.chunks:
                chunk_metadata = dict(
                    chunk.metadata
                )

                chunk_metadata.update(
                    {
                        "chunk_type": chunk.chunk_type,
                        "character_count": chunk.character_count,
                        "previous_chunk_index": (
                            chunk.previous_chunk_index
                        ),
                        "next_chunk_index": (
                            chunk.next_chunk_index
                        ),
                        "section_index": section_index,
                    }
                )

                chunk_values.append(
                    {
                        "document_id": document.id,
                        "section_id": section.id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.text,
                        "page_number": chunk.page_start,
                        "token_count": chunk.token_count,
                        "metadata_": chunk_metadata,
                    }
                )

            if chunk_values:
                persisted_chunks = (
                    await self.chunk_repository.create_many(
                        chunk_values
                    )
                )

                chunk_count += len(
                    persisted_chunks
                )

            logger.debug(
                "Persisted section: "
                "document_id=%s section_index=%s chunks=%s",
                document.id,
                section_index,
                len(chunk_values),
            )

        return section_count, chunk_count

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _build_document_metadata(
        self,
        *,
        paper: Any,
        resolution: DocumentResolution,
        downloaded: Any,
        stored: StoredDocument,
        extraction: DocumentExtraction,
        parsed: DocumentParseResult,
    ) -> dict[str, Any]:
        return {
            "source_url": resolution.document_url,
            "final_url": getattr(
                downloaded,
                "final_url",
                resolution.document_url,
            ),
            "source": resolution.source,
            "external_id": resolution.external_id,
            "is_pdf": resolution.is_pdf,
            "content_type": getattr(
                downloaded,
                "content_type",
                None,
            ),
            "download_size_bytes": getattr(
                downloaded,
                "size_bytes",
                None,
            ),
            "storage_key": stored.storage_key,
            "storage_path": str(
                stored.path
            ),
            "size_bytes": stored.size_bytes,
            "checksum": stored.checksum,
            "page_count": parsed.page_count,
            "has_extractable_text": bool(
                extraction.text.strip()
            ),
            "full_text_length": len(
                parsed.full_text
            ),
            "section_count": len(
                parsed.sections
            ),
            "paper_id": getattr(
                paper,
                "id",
                None,
            ),
            "arxiv_id": getattr(
                paper,
                "arxiv_id",
                None,
            ),
            "doi": getattr(
                paper,
                "doi",
                None,
            ),
        }

    # ------------------------------------------------------------------
    # Naming / storage
    # ------------------------------------------------------------------

    def _build_document_name(
        self,
        *,
        paper: Any,
        resolution: DocumentResolution,
    ) -> str:
        title = getattr(
            paper,
            "title",
            None,
        )

        if title:
            return f"{title}.pdf"

        return self._build_download_filename(
            paper=paper,
            resolution=resolution,
        )

    def _build_download_filename(
        self,
        *,
        paper: Any,
        resolution: DocumentResolution,
    ) -> str:
        arxiv_id = getattr(
            paper,
            "arxiv_id",
            None,
        )

        if arxiv_id:
            safe_id = str(arxiv_id).replace(
                "/",
                "_",
            )

            return f"{safe_id}.pdf"

        source_url = resolution.document_url

        if source_url:
            candidate = Path(
                str(source_url).split("?")[0]
            ).name

            if candidate:
                if not candidate.lower().endswith(
                    ".pdf"
                ):
                    candidate = f"{candidate}.pdf"

                return candidate

        paper_id = getattr(
            paper,
            "id",
            "unknown",
        )

        return f"paper-{paper_id}.pdf"

    def _build_storage_key(
        self,
        *,
        paper_id: int,
        source_url: Any,
        filename: str | None = None,
    ) -> str:
        if not filename:
            filename = "document.pdf"

            if source_url:
                try:
                    candidate = Path(
                        str(source_url).split("?")[0]
                    ).name

                    if candidate:
                        filename = candidate
                except Exception:
                    pass

        return (
            f"papers/{paper_id}/documents/{filename}"
        )

    # ------------------------------------------------------------------
    # Repository helpers
    # ------------------------------------------------------------------

    async def _get_document_for_paper(
        self,
        paper_id: int,
    ) -> Document | None:
        if hasattr(
            self.document_repository,
            "get_by_paper_id",
        ):
            return await self.document_repository.get_by_paper_id(
                paper_id
            )

        if hasattr(
            self.document_repository,
            "find_by_paper_id",
        ):
            return await self.document_repository.find_by_paper_id(
                paper_id
            )

        raise RuntimeError(
            "DocumentRepository must provide "
            "get_by_paper_id() or find_by_paper_id()."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_paper_id(
        paper_id: int | str,
    ) -> int:
        try:
            return int(paper_id)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Invalid paper_id: {paper_id!r}"
            ) from exc

    @staticmethod
    def _normalize_uuid(
        value: UUID | str,
    ) -> UUID:
        if isinstance(value, UUID):
            return value

        try:
            return UUID(
                str(value)
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Invalid document UUID: {value!r}"
            ) from exc

