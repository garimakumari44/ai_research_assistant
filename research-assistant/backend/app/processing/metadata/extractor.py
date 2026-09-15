"""
Metadata extraction utilities.

Responsible for extracting
raw metadata from documents.
"""

from pathlib import Path
from datetime import datetime


class MetadataExtractor:


    def extract_file_metadata(
        self,
        file_path: str,
    ) -> dict:
        """
        Extract metadata from local files.
        """


        path = Path(file_path)


        if not path.exists():
            raise FileNotFoundError(
                file_path
            )


        stats = path.stat()


        return {

            "file_name": path.name,

            "file_extension": path.suffix.lower(),

            "file_size": stats.st_size,

            "created_at": datetime.fromtimestamp(
                stats.st_ctime
            ),

            "modified_at": datetime.fromtimestamp(
                stats.st_mtime
            ),

        }



    def extract_source_metadata(
        self,
        source_type: str,
        source,
    ) -> dict:
        """
        Extract metadata based on source.
        """


        metadata = {

            "source_type": source_type,

        }


        if source_type == "url":

            metadata["url"] = source



        elif source_type == "github":

            metadata["repository"] = source



        elif source_type == "arxiv":

            metadata["paper_id"] = source



        return metadata