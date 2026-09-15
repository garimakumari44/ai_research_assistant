from typing import List, Dict, Any

from app.retrieval.models import RetrievedDocument



class MetadataFilter:
    """
    Filters retrieved documents using metadata.

    Examples:

    source filtering
    date filtering
    document type filtering
    permission filtering
    """



    def __init__(self):
        pass



    def match(
        self,
        metadata: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """
        Check whether metadata satisfies filters.

        Example:

        metadata:

        {
            "type":"paper",
            "year":2025
        }


        filters:

        {
            "type":"paper"
        }


        returns:

        True
        """



        for key, value in filters.items():


            # Metadata does not contain field

            if key not in metadata:

                return False



            # Exact matching

            if metadata[key] != value:

                return False



        return True



    def apply(
        self,
        documents: List[RetrievedDocument],
        filters: Dict[str, Any] | None
    ) -> List[RetrievedDocument]:
        """
        Apply metadata filtering.

        If no filters exist,
        return all documents.
        """



        if not filters:

            return documents



        filtered_documents = []



        for document in documents:


            if self.match(
                document.metadata,
                filters
            ):

                filtered_documents.append(
                    document
                )



        return filtered_documents



    def filter_by_source(
        self,
        documents: List[RetrievedDocument],
        source: str
    ) -> List[RetrievedDocument]:
        """
        Convenience filter.

        Example:

        source="arxiv"
        """

        return [

            doc

            for doc in documents

            if doc.source == source

        ]