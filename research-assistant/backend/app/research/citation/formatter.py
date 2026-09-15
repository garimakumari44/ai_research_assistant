from __future__ import annotations

from typing import List, Literal

from app.research.models import Citation



class CitationFormatter:
    """
    Formats citations into
    different academic styles.

    Supported:

    - APA
    - IEEE
    - MLA
    - BibTeX

    """



    def format(
        self,
        citation: Citation,
        style: Literal[
            "apa",
            "ieee",
            "mla",
            "bibtex"
        ] = "apa",
    ) -> str:
        """
        Format a citation.
        """


        if style == "apa":

            return self.format_apa(
                citation
            )


        elif style == "ieee":

            return self.format_ieee(
                citation
            )


        elif style == "mla":

            return self.format_mla(
                citation
            )


        elif style == "bibtex":

            return self.format_bibtex(
                citation
            )


        raise ValueError(
            f"Unsupported citation style: {style}"
        )



    def format_apa(
        self,
        citation: Citation,
    ) -> str:
        """
        APA style.

        Example:

        Author. (Year).
        Title.
        """

        authors = ", ".join(
            citation.authors
        )


        year = citation.year or "n.d."


        return (
            f"{authors}. "
            f"({year}). "
            f"{citation.title}."
        )



    def format_ieee(
        self,
        citation: Citation,
    ) -> str:
        """
        IEEE style.

        Example:

        [1] Author,
        "Title", Year.
        """

        authors = ", ".join(
            citation.authors
        )


        year = citation.year or "n.d."


        return (
            f"{authors}, "
            f"\"{citation.title}\", "
            f"{year}."
        )



    def format_mla(
        self,
        citation: Citation,
    ) -> str:
        """
        MLA style.
        """

        authors = ", ".join(
            citation.authors
        )


        return (
            f"{authors}. "
            f"{citation.title}. "
            f"{citation.year or 'n.d.'}."
        )



    def format_bibtex(
        self,
        citation: Citation,
    ) -> str:
        """
        BibTeX format.

        Used by researchers
        for LaTeX papers.
        """

        key = (
            citation.title
            .lower()
            .replace(
                " ",
                "_"
            )
        )


        authors = (
            " and ".join(
                citation.authors
            )
        )


        return f"""
@article{{{key},
  title={{{citation.title}}},
  author={{{authors}}},
  year={{{citation.year or ''}}},
}}
""".strip()



    def format_many(
        self,
        citations: List[Citation],
        style: str = "apa",
    ) -> List[str]:
        """
        Format multiple citations.
        """

        return [
            self.format(
                citation,
                style
            )

            for citation in citations
        ]