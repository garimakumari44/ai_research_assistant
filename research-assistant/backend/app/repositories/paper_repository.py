from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.author import Author
from app.db.models.paper import Paper, PaperAuthor
from app.db.models.venue import Venue
from app.papers.schemas.search import PaperSearchRequest


class PaperRepository:
    """
    Repository responsible for persistence and retrieval of papers.

    Responsibilities:
        - database CRUD
        - filtering
        - searching
        - pagination
        - counting
        - identity/deduplication lookups
        - author relationship synchronization

    The repository does not perform:
        - provider API calls
        - normalization of external paper data
        - research orchestration
        - external paper discovery
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================================================================
    # RELATIONSHIP LOADERS
    # ==================================================================

    @staticmethod
    def _paper_load_options():
        return (
            selectinload(Paper.author_links).selectinload(
                PaperAuthor.author
            ),
            selectinload(Paper.venue),
        )

    @staticmethod
    def _paper_full_load_options():
        return (
            selectinload(Paper.author_links).selectinload(
                PaperAuthor.author
            ),
            selectinload(Paper.topic_links),
            selectinload(Paper.method_links),
            selectinload(Paper.dataset_links),
            selectinload(Paper.citations_made),
            selectinload(Paper.citations_received),
            selectinload(Paper.venue),
        )

    # ==================================================================
    # AUTHOR HELPERS
    # ==================================================================

    @staticmethod
    def _normalize_author_name(
        name: str | None,
    ) -> str:
        """
        Normalize an author name for matching.

        This is intentionally conservative. We only:
            - convert to string
            - strip surrounding whitespace
            - collapse repeated whitespace
            - lowercase for lookup

        The stored Author.full_name remains untouched.
        """
        if not name:
            return ""

        return " ".join(
            str(name).strip().split()
        ).casefold()

    @staticmethod
    def _get_domain_author_value(
        author: Any,
        *names: str,
    ) -> Any:
        """
        Safely retrieve the first available attribute/key from
        a domain author object or dictionary.
        """
        for name in names:
            if isinstance(author, dict):
                value = author.get(name)
            else:
                value = getattr(
                    author,
                    name,
                    None,
                )

            if value is not None:
                return value

        return None

    # ==================================================================
    # CREATE
    # ==================================================================

    async def create(
        self,
        paper: Paper,
    ) -> Paper:
        self.session.add(paper)

        await self.session.flush()

        statement = (
            select(Paper)
            .options(*self._paper_load_options())
            .where(Paper.id == paper.id)
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one()

    # ==================================================================
    # SYNC AUTHORS
    # ==================================================================

    async def sync_authors(
        self,
        paper: Paper,
        authors: Sequence[Any] | None,
    ) -> Paper:
        """
        Synchronize a paper's authors.

        Behavior:
            - removes stale paper-author links
            - reuses existing Author records
            - creates missing Author records
            - preserves provider/domain author order
            - prefers ORCID for author identity when available
            - falls back to normalized full name
            - avoids duplicate author links
            - reloads the paper with author relationships

        This method intentionally does not delete Author records
        themselves. An Author may be linked to multiple papers.
        """

        if paper.id is None:
            raise ValueError(
                "Cannot synchronize authors for a paper without an ID."
            )

        normalized_authors: list[dict[str, Any]] = []

        seen_keys: set[tuple[str, str]] = set()

        for index, incoming_author in enumerate(
            authors or []
        ):
            if incoming_author is None:
                continue

            name = self._get_domain_author_value(
                incoming_author,
                "name",
                "full_name",
            )

            if name is None:
                continue

            name = str(name).strip()

            if not name:
                continue

            orcid = self._get_domain_author_value(
                incoming_author,
                "orcid",
            )

            if orcid is not None:
                orcid = str(orcid).strip() or None

            affiliation = self._get_domain_author_value(
                incoming_author,
                "affiliation",
            )

            if affiliation is not None:
                affiliation = (
                    str(affiliation).strip()
                    or None
                )

            given_name = self._get_domain_author_value(
                incoming_author,
                "given_name",
            )

            if given_name is not None:
                given_name = (
                    str(given_name).strip()
                    or None
                )

            family_name = self._get_domain_author_value(
                incoming_author,
                "family_name",
            )

            if family_name is not None:
                family_name = (
                    str(family_name).strip()
                    or None
                )

            author_id = self._get_domain_author_value(
                incoming_author,
                "author_id",
                "id",
            )

            if author_id is not None:
                author_id = str(
                    author_id
                ).strip() or None

            normalized_name = (
                self._normalize_author_name(
                    name
                )
            )

            if not normalized_name:
                continue

            # ----------------------------------------------------------
            # Deduplicate incoming authors.
            #
            # ORCID is preferred because it is a stronger identity
            # signal than name matching.
            # ----------------------------------------------------------

            if orcid:
                dedupe_key = (
                    "orcid",
                    orcid.casefold(),
                )
            else:
                dedupe_key = (
                    "name",
                    normalized_name,
                )

            if dedupe_key in seen_keys:
                continue

            seen_keys.add(dedupe_key)

            normalized_authors.append(
                {
                    "name": name,
                    "orcid": orcid,
                    "affiliation": affiliation,
                    "given_name": given_name,
                    "family_name": family_name,
                    "author_id": author_id,
                    "position": index,
                }
            )

        # --------------------------------------------------------------
        # Remove existing links for this paper.
        #
        # Do not delete Author rows themselves.
        # --------------------------------------------------------------

        existing_links_statement = select(
            PaperAuthor
        ).where(
            PaperAuthor.paper_id == paper.id
        )

        existing_links_result = (
            await self.session.execute(
                existing_links_statement
            )
        )

        existing_links = (
            existing_links_result.scalars().all()
        )

        for link in existing_links:
            await self.session.delete(link)

        await self.session.flush()

        # --------------------------------------------------------------
        # Re-create links in the incoming order.
        # --------------------------------------------------------------

        for author_data in normalized_authors:
            name = author_data["name"]
            orcid = author_data["orcid"]
            affiliation = author_data[
                "affiliation"
            ]
            given_name = author_data[
                "given_name"
            ]
            family_name = author_data[
                "family_name"
            ]

            author: Author | None = None

            # ----------------------------------------------------------
            # 1. Match by ORCID when available.
            # ----------------------------------------------------------

            if orcid:
                statement = (
                    select(Author)
                    .where(
                        func.lower(
                            Author.orcid
                        )
                        == orcid.casefold()
                    )
                    .limit(1)
                )

                result = await self.session.execute(
                    statement
                )

                author = (
                    result.scalar_one_or_none()
                )

            # ----------------------------------------------------------
            # 2. Fall back to normalized full name.
            # ----------------------------------------------------------

            if author is None:
                statement = (
                    select(Author)
                    .where(
                        func.lower(
                            func.trim(
                                Author.full_name
                            )
                        )
                        == name.casefold()
                    )
                    .limit(1)
                )

                result = await self.session.execute(
                    statement
                )

                author = (
                    result.scalar_one_or_none()
                )

            # ----------------------------------------------------------
            # 3. Create missing Author.
            # ----------------------------------------------------------

            if author is None:
                author = Author(
                    full_name=name,
                    orcid=orcid,
                    given_name=given_name,
                    family_name=family_name,
                    affiliation=affiliation,
                )

                self.session.add(author)

                await self.session.flush()

            else:
                # ------------------------------------------------------
                # Fill missing information without overwriting
                # existing high-quality data.
                # ------------------------------------------------------

                changed = False

                if (
                    orcid
                    and not author.orcid
                ):
                    author.orcid = orcid
                    changed = True

                if (
                    given_name
                    and not author.given_name
                ):
                    author.given_name = given_name
                    changed = True

                if (
                    family_name
                    and not author.family_name
                ):
                    author.family_name = family_name
                    changed = True

                if (
                    affiliation
                    and not author.affiliation
                ):
                    author.affiliation = (
                        affiliation
                    )
                    changed = True

                if changed:
                    await self.session.flush()

            # ----------------------------------------------------------
            # Create paper-author relationship.
            # ----------------------------------------------------------

            link = PaperAuthor(
                paper_id=paper.id,
                author_id=author.id,
                author_order=author_data[
                    "position"
                ],
            )

            self.session.add(link)

        await self.session.flush()

        # --------------------------------------------------------------
        # Reload the paper so the returned object contains the
        # synchronized author relationships.
        # --------------------------------------------------------------

        statement = (
            select(Paper)
            .options(*self._paper_load_options())
            .where(Paper.id == paper.id)
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one()

    # ==================================================================
    # GET BY ID
    # ==================================================================

    async def get_by_id(
        self,
        paper_id: int | str,
        *,
        load_relationships: bool = False,
    ) -> Optional[Paper]:

        try:
            normalized_id = int(
                paper_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        statement = select(Paper).where(
            Paper.id == normalized_id
        )

        if load_relationships:
            statement = statement.options(
                *self._paper_full_load_options()
            )
        else:
            statement = statement.options(
                *self._paper_load_options()
            )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # GET BY DOI
    # ==================================================================

    async def get_by_doi(
        self,
        doi: str,
    ) -> Optional[Paper]:

        if not doi:
            return None

        statement = (
            select(Paper)
            .options(*self._paper_load_options())
            .where(
                Paper.doi == doi.strip()
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # GET BY ARXIV ID
    # ==================================================================

    async def get_by_arxiv_id(
        self,
        arxiv_id: str,
    ) -> Optional[Paper]:

        if not arxiv_id:
            return None

        statement = (
            select(Paper)
            .options(*self._paper_load_options())
            .where(
                Paper.arxiv_id
                == arxiv_id.strip()
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # GET BY PMID
    # ==================================================================

    async def get_by_pmid(
        self,
        pmid: str,
    ) -> Optional[Paper]:

        if not pmid:
            return None

        statement = (
            select(Paper)
            .options(*self._paper_load_options())
            .where(
                Paper.pmid
                == pmid.strip()
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # GET BY PROVIDER ID
    # ==================================================================

    async def get_by_provider_id(
        self,
        provider: str,
        provider_paper_id: str,
    ) -> Optional[Paper]:

        if (
            not provider
            or not provider_paper_id
        ):
            return None

        statement = (
            select(Paper)
            .options(*self._paper_load_options())
            .where(
                Paper.provider
                == provider.strip(),
                Paper.provider_paper_id
                == provider_paper_id.strip(),
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    # ==================================================================
    # GET BY EXTERNAL ID
    # ==================================================================

    async def get_by_external_id(
        self,
        provider: str,
        external_id: str,
    ) -> Optional[Paper]:

        return await self.get_by_provider_id(
            provider=provider,
            provider_paper_id=external_id,
        )

    # ==================================================================
    # GET BY CANONICAL KEY
    # ==================================================================

    async def get_by_canonical_key(
        self,
        canonical_key: str,
    ) -> Optional[Paper]:

        if not canonical_key:
            return None

        canonical_key = (
            canonical_key.strip()
        )

        if canonical_key.startswith(
            "doi:"
        ):
            return await self.get_by_doi(
                canonical_key.removeprefix(
                    "doi:"
                ).strip()
            )

        if canonical_key.startswith(
            "arxiv:"
        ):
            return await self.get_by_arxiv_id(
                canonical_key.removeprefix(
                    "arxiv:"
                ).strip()
            )

        if canonical_key.startswith(
            "pmid:"
        ):
            return await self.get_by_pmid(
                canonical_key.removeprefix(
                    "pmid:"
                ).strip()
            )

        if ":" in canonical_key:
            provider, provider_id = (
                canonical_key.split(
                    ":",
                    1,
                )
            )

            return await self.get_by_provider_id(
                provider.strip(),
                provider_id.strip(),
            )

        return None

    # ==================================================================
    # FIND EXISTING
    # ==================================================================

    async def find_existing(
        self,
        *,
        doi: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        pmid: Optional[str] = None,
        provider: Optional[str] = None,
        provider_paper_id: Optional[str] = None,
        canonical_key: Optional[str] = None,
    ) -> Optional[Paper]:

        if doi:
            paper = await self.get_by_doi(
                doi
            )

            if paper:
                return paper

        if arxiv_id:
            paper = await self.get_by_arxiv_id(
                arxiv_id
            )

            if paper:
                return paper

        if pmid:
            paper = await self.get_by_pmid(
                pmid
            )

            if paper:
                return paper

        if (
            provider
            and provider_paper_id
        ):
            paper = (
                await self.get_by_provider_id(
                    provider,
                    provider_paper_id,
                )
            )

            if paper:
                return paper

        if canonical_key:
            paper = (
                await self.get_by_canonical_key(
                    canonical_key
                )
            )

            if paper:
                return paper

        return None

    # ==================================================================
    # SEARCH
    # ==================================================================

    async def search(
        self,
        request: PaperSearchRequest,
    ) -> tuple[Sequence[Paper], int]:
        """
        Search papers using the supplied filters.

        Free-text search covers:
            - title
            - abstract
            - DOI
            - arXiv ID
            - PMID
            - provider paper ID
            - author full name
            - venue name
        """

        conditions = []

        # --------------------------------------------------------------
        # FREE TEXT
        # --------------------------------------------------------------

        if request.query:
            query = request.query.strip()

            if query:
                pattern = f"%{query}%"

                conditions.append(
                    or_(
                        Paper.title.ilike(
                            pattern
                        ),
                        Paper.abstract.ilike(
                            pattern
                        ),
                        Paper.doi.ilike(
                            pattern
                        ),
                        Paper.arxiv_id.ilike(
                            pattern
                        ),
                        Paper.pmid.ilike(
                            pattern
                        ),
                        Paper.provider_paper_id.ilike(
                            pattern
                        ),

                        # Author search
                        Paper.author_links.any(
                            PaperAuthor.author.has(
                                Author.full_name.ilike(
                                    pattern
                                )
                            )
                        ),

                        # Venue search
                        Paper.venue.has(
                            Venue.name.ilike(
                                pattern
                            )
                        ),
                    )
                )

        # --------------------------------------------------------------
        # DOI
        # --------------------------------------------------------------

        if request.doi:
            doi = request.doi.strip()

            if doi:
                conditions.append(
                    Paper.doi.ilike(
                        f"%{doi}%"
                    )
                )

        # --------------------------------------------------------------
        # PROVIDER
        # --------------------------------------------------------------

        provider = (
            request.provider
            or request.source
        )

        if provider:
            provider = provider.strip()

            if provider:
                conditions.append(
                    Paper.provider == provider
                )

        # --------------------------------------------------------------
        # PROVIDER PAPER ID
        # --------------------------------------------------------------

        if request.provider_paper_id:
            provider_paper_id = (
                request.provider_paper_id.strip()
            )

            if provider_paper_id:
                conditions.append(
                    Paper.provider_paper_id.ilike(
                        f"%{provider_paper_id}%"
                    )
                )

        # --------------------------------------------------------------
        # VENUE
        # --------------------------------------------------------------

        if request.venue:
            venue_value = (
                request.venue.strip()
            )

            if venue_value:
                if venue_value.isdigit():
                    conditions.append(
                        Paper.venue_id
                        == int(venue_value)
                    )
                else:
                    conditions.append(
                        Paper.venue.has(
                            Venue.name.ilike(
                                f"%{venue_value}%"
                            )
                        )
                    )

        # --------------------------------------------------------------
        # AUTHOR
        # --------------------------------------------------------------

        if request.author:
            author_value = (
                request.author.strip()
            )

            if author_value:
                conditions.append(
                    Paper.author_links.any(
                        PaperAuthor.author.has(
                            Author.full_name.ilike(
                                f"%{author_value}%"
                            )
                        )
                    )
                )

        # --------------------------------------------------------------
        # YEAR
        # --------------------------------------------------------------

        if request.year is not None:
            conditions.append(
                Paper.year == request.year
            )

        # --------------------------------------------------------------
        # PUBLICATION DATE FROM
        # --------------------------------------------------------------

        if request.published_from:
            conditions.append(
                Paper.publication_date
                >= request.published_from
            )

        # --------------------------------------------------------------
        # PUBLICATION DATE TO
        # --------------------------------------------------------------

        if request.published_to:
            end_date = (
                request.published_to
                + timedelta(days=1)
            )

            conditions.append(
                Paper.publication_date
                < end_date
            )

        # --------------------------------------------------------------
        # CATEGORY
        # --------------------------------------------------------------

        if request.category:
            from app.db.models.topic import Topic

            category_value = (
                request.category.strip()
            )

            if category_value:
                category_pattern = (
                    f"%{category_value}%"
                )

                conditions.append(
                    Paper.topic_links.any(
                        Paper.topic_links.property
                        .mapper.class_
                        .topic.has(
                            Topic.name.ilike(
                                category_pattern
                            )
                        )
                    )
                )

        # --------------------------------------------------------------
        # COUNT
        # --------------------------------------------------------------

        count_statement = select(
            func.count(Paper.id)
        )

        if conditions:
            count_statement = (
                count_statement.where(
                    *conditions
                )
            )

        count_result = (
            await self.session.execute(
                count_statement
            )
        )

        total = int(
            count_result.scalar_one()
            or 0
        )

        # --------------------------------------------------------------
        # DATA QUERY
        # --------------------------------------------------------------

        statement = (
            select(Paper)
            .options(
                *self._paper_load_options()
            )
        )

        if conditions:
            statement = statement.where(
                *conditions
            )

        # --------------------------------------------------------------
        # SORT
        # --------------------------------------------------------------

        sort_column = (
            Paper.publication_date
        )

        sort_by = request.sort_by

        if sort_by == "title":
            sort_column = Paper.title

        elif sort_by == "citation_count":
            sort_column = Paper.citation_count

        elif sort_by == "created_at":
            sort_column = Paper.created_at

        elif sort_by == "updated_at":
            sort_column = Paper.updated_at

        elif sort_by == "year":
            sort_column = Paper.year

        elif sort_by == "publication_date":
            sort_column = (
                Paper.publication_date
            )

        if request.sort_order == "asc":
            statement = statement.order_by(
                sort_column.asc().nullslast(),
                Paper.id.asc(),
            )
        else:
            statement = statement.order_by(
                sort_column.desc().nullslast(),
                Paper.id.desc(),
            )

        # --------------------------------------------------------------
        # PAGINATION
        # --------------------------------------------------------------

        page_size = max(
            int(request.page_size),
            1,
        )

        offset = max(
            int(request.offset),
            0,
        )

        statement = (
            statement
            .offset(offset)
            .limit(page_size)
        )

        # --------------------------------------------------------------
        # EXECUTE
        # --------------------------------------------------------------

        result = await self.session.execute(
            statement
        )

        papers = (
            result
            .scalars()
            .unique()
            .all()
        )

        return papers, total

    # ==================================================================
    # SIMPLE TEXT SEARCH
    # ==================================================================

    async def search_text(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Paper]:

        query = query.strip()

        if not query:
            return []

        pattern = f"%{query}%"

        statement = (
            select(Paper)
            .options(
                *self._paper_load_options()
            )
            .where(
                or_(
                    Paper.title.ilike(
                        pattern
                    ),
                    Paper.abstract.ilike(
                        pattern
                    ),
                    Paper.doi.ilike(
                        pattern
                    ),
                    Paper.arxiv_id.ilike(
                        pattern
                    ),
                    Paper.pmid.ilike(
                        pattern
                    ),
                    Paper.provider_paper_id.ilike(
                        pattern
                    ),

                    # Author
                    Paper.author_links.any(
                        PaperAuthor.author.has(
                            Author.full_name.ilike(
                                pattern
                            )
                        )
                    ),

                    # Venue
                    Paper.venue.has(
                        Venue.name.ilike(
                            pattern
                        )
                    ),
                )
            )
            .order_by(
                Paper.publication_date
                .desc()
                .nullslast(),
                Paper.id.desc(),
            )
            .offset(
                max(
                    int(offset),
                    0,
                )
            )
            .limit(
                max(
                    int(limit),
                    1,
                )
            )
        )

        result = await self.session.execute(
            statement
        )

        return (
            result
            .scalars()
            .unique()
            .all()
        )

    # ==================================================================
    # LIST
    # ==================================================================

    async def list(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Paper]:

        statement = (
            select(Paper)
            .options(
                *self._paper_load_options()
            )
            .order_by(
                Paper.publication_date
                .desc()
                .nullslast(),
                Paper.id.desc(),
            )
            .offset(
                max(
                    int(offset),
                    0,
                )
            )
            .limit(
                max(
                    int(limit),
                    1,
                )
            )
        )

        result = await self.session.execute(
            statement
        )

        return (
            result
            .scalars()
            .unique()
            .all()
        )

    # ==================================================================
    # UPDATE
    # ==================================================================

    async def update(
        self,
        paper_id: int | str,
        values: dict,
    ) -> Optional[Paper]:

        paper = await self.get_by_id(
            paper_id,
            load_relationships=False,
        )

        if paper is None:
            return None

        for field, value in values.items():
            if not hasattr(
                paper,
                field,
            ):
                continue

            setattr(
                paper,
                field,
                value,
            )

        await self.session.flush()

        statement = (
            select(Paper)
            .options(
                *self._paper_load_options()
            )
            .where(
                Paper.id == paper.id
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one()

    # ==================================================================
    # DELETE
    # ==================================================================

    async def delete(
        self,
        paper_id: int | str,
    ) -> bool:

        paper = await self.get_by_id(
            paper_id,
            load_relationships=False,
        )

        if paper is None:
            return False

        await self.session.delete(paper)

        await self.session.flush()

        return True

    # ==================================================================
    # COUNT
    # ==================================================================

    async def count(self) -> int:

        statement = select(
            func.count(Paper.id)
        )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
            or 0
        )