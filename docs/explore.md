# AI Research Assistant — Explore & Adaptive Retrieval Architecture

## 1. Overview

The **Explore module** is the research discovery and retrieval interface of the AI Research Assistant.

It allows users to search across an indexed research corpus using:

- Dense semantic retrieval
- BM25 / keyword retrieval
- Metadata filtering
- Reciprocal Rank Fusion
- Unified candidate ranking
- Cross-encoder reranking
- Top-K evidence selection

The Explore pipeline combines multiple retrieval signals and returns ranked research results to the Next.js Explore UI.

```mermaid
flowchart TD

    UI[Next.js Explore UI]

    API[FastAPI Explore API<br/>POST /api/v1/explore]

    V[Request Validation]

    N[Query Normalization]

    C[Adaptive Retrieval Controller]

    QA[Query Analysis]

    RP[Retrieval Planning]

    RE[Retrieval Execution]

    F[Reciprocal Rank Fusion]

    UR[Unified Candidate Ranking]

    R[Cross-Encoder Reranker]

    TOP[Top-K Relevant Evidence]

    RF[Result Formatting]

    RESP[Explore API Response]

    RESULTS[Next.js Search Results]

    UI --> API
    API --> V
    V --> N
    N --> C
    C --> QA
    QA --> RP
    RP --> RE

    RE --> F

    F --> UR
    UR --> R
    R --> TOP
    TOP --> RF
    RF --> RESP
    RESP --> RESULTS
```

---

# 2. Explore Request Flow

The Explore request begins in the Next.js frontend and travels through the FastAPI API into the Adaptive Retrieval Controller.

```mermaid
sequenceDiagram

    participant UI as Next.js Explore UI
    participant API as FastAPI Explore API
    participant V as Request Validation
    participant N as Query Normalization
    participant C as Adaptive Retrieval Controller
    participant P as Retrieval Planning
    participant R as Retrieval Execution
    participant F as Rank Fusion
    participant RR as Cross-Encoder Reranker
    participant OUT as Explore API Response

    UI->>API: POST /api/v1/explore
    API->>V: Validate Request
    V-->>API: Valid Request

    API->>N: Normalize Query
    N-->>API: Normalized Query

    API->>C: Execute Retrieval
    C->>C: Query Analysis
    C->>P: Retrieval Planning
    P-->>C: Retrieval Plan

    C->>R: Retrieval Execution
    R-->>C: Candidate Results

    C->>F: Reciprocal Rank Fusion
    F-->>C: Unified Ranking

    C->>RR: Cross-Encoder Reranking
    RR-->>C: Top-K Relevant Evidence

    C-->>API: Ranked Results
    API->>OUT: Format Response
    OUT-->>UI: Search Results
```

---

# 3. Explore API Layer

The Explore API provides the HTTP boundary for search and research discovery.

```mermaid
flowchart TD

    UI[Next.js Explore UI]

    HTTP[HTTPS / REST]

    API[FastAPI Explore API<br/>POST /api/v1/explore]

    V[Request Validation]

    N[Query Normalization]

    UI --> HTTP
    HTTP --> API
    API --> V
    V --> N
```

The API is responsible for:

- Receiving the Explore request.
- Validating request parameters.
- Normalizing the query.
- Invoking the Adaptive Retrieval Controller.
- Formatting the final retrieval response.
- Returning search results to the frontend.

---

# 4. Request Validation

The request validation layer ensures that the incoming Explore request satisfies the expected API contract.

```mermaid
flowchart LR

    R[Explore Request]

    V[Request Validation]

    Q[Validated Request]

    R --> V
    V --> Q
```

Validation can cover:

- Query presence.
- Query format.
- Retrieval parameters.
- Pagination or result limits.
- Metadata filters.
- Optional retrieval configuration.

---

# 5. Query Normalization

The query normalization layer prepares the user's query for retrieval.

```mermaid
flowchart LR

    Q[Raw Query]

    N[Query Normalization]

    RQ[Normalized Query]

    Q --> N
    N --> RQ
```

Normalization creates a consistent representation before query analysis and retrieval planning.

The normalized query is then passed to the Adaptive Retrieval Controller.

---

# 6. Adaptive Retrieval Controller

The **Adaptive Retrieval Controller** is the central orchestration boundary of the Explore retrieval pipeline.

```mermaid
flowchart TD

    Q[Normalized Query]

    C[Adaptive Retrieval Controller]

    A[Query Analysis]

    P[Retrieval Planning]

    E[Retrieval Execution]

    F[Rank Fusion]

    RR[Reranking]

    TOP[Top-K Evidence]

    Q --> C
    C --> A
    A --> P
    P --> E
    E --> F
    F --> RR
    RR --> TOP
```

The controller coordinates:

1. Query analysis.
2. Retrieval planning.
3. Retrieval execution.
4. Candidate fusion.
5. Candidate ranking.
6. Cross-encoder reranking.
7. Top-K evidence selection.

---

# 7. Query Analysis

Query analysis determines the characteristics of the incoming research query.

```mermaid
flowchart TD

    Q[Normalized Query]

    A[Query Analysis]

    I[Query Intent]

    T[Query Terms]

    C[Query Characteristics]

    Q --> A

    A --> I
    A --> T
    A --> C
```

Query analysis can help identify:

- Semantic research intent.
- Exact terminology.
- Important keywords.
- Technical phrases.
- Potential metadata constraints.
- Retrieval requirements.

---

# 8. Retrieval Planning

The retrieval planner determines which retrieval mechanisms should participate in the search.

```mermaid
flowchart TD

    A[Query Analysis]

    P[Retrieval Planning]

    D[Dense Retrieval]

    B[BM25 / Keyword Retrieval]

    M[Metadata Filtering]

    P --> D
    P --> B
    P --> M

    A --> P
```

The retrieval plan can combine multiple retrieval signals.

For example:

```text
Research Query
      |
      v
Query Analysis
      |
      v
Retrieval Planning
      |
      +---- Dense Retrieval
      |
      +---- BM25 Retrieval
      |
      +---- Metadata Filtering
```

---

# 9. Retrieval Execution

The Retrieval Execution layer runs the retrieval mechanisms selected by the planner.

```mermaid
flowchart TD

    P[Retrieval Planning]

    E[Retrieval Execution]

    D[Dense Retrieval]

    B[BM25 / Keyword Retrieval]

    M[Metadata Filtering]

    P --> E

    E --> D
    E --> B
    E --> M
```

The retrieval execution layer produces candidate result sets that are later combined.

---

# 10. Research Source Ingestion

The Explore retrieval system depends on an indexed research corpus.

```mermaid
flowchart TD

    S[Research Sources]

    P[Papers]
    AX[arXiv]
    PDF[PDFs]
    GH[GitHub]

    I[Document Ingestion]

    T[Text Extraction]

    C[Chunking]

    EG[Embedding Generation]

    FI[FAISS Vector Index]

    MS[Metadata Storage]

    S --> P
    S --> AX
    S --> PDF
    S --> GH

    P --> I
    AX --> I
    PDF --> I
    GH --> I

    I --> T
    T --> C

    C --> EG
    C --> MS
```

The ingestion pipeline transforms research sources into searchable representations.

---

# 11. Document Ingestion

Research sources enter the system through the document ingestion pipeline.

```mermaid
flowchart TD

    S[Research Sources]

    I[Document Ingestion]

    T[Text Extraction]

    C[Chunking]

    S --> I
    I --> T
    T --> C
```

Supported research sources can include:

- Papers.
- arXiv content.
- PDF documents.
- GitHub research repositories.

---

# 12. Text Extraction

Text extraction converts source documents into machine-processable text.

```mermaid
flowchart LR

    D[Research Document]

    T[Text Extraction]

    TXT[Extracted Text]

    D --> T
    T --> TXT
```

The extracted text becomes the input for chunking.

---

# 13. Chunking

Chunking divides extracted research text into smaller searchable units.

```mermaid
flowchart LR

    T[Extracted Text]

    C[Chunking]

    CH[Research Chunks]

    T --> C
    C --> CH
```

Chunks provide the retrieval unit for semantic and lexical search.

---

# 14. Embedding Generation

The embedding pipeline converts research chunks into vector representations.

```mermaid
flowchart TD

    C[Research Chunks]

    E[Embedding Generation]

    M[BGE-small]

    V[384D Vector]

    C --> E
    E --> M
    M --> V
```

The Explore architecture uses BGE-small embeddings to represent research chunks in vector space.

The resulting vectors are used for dense semantic retrieval.

---

# 15. FAISS Vector Index

The generated vectors are stored in a FAISS vector index.

```mermaid
flowchart TD

    V[384D Embeddings]

    F[FAISS Vector Index]

    C[Semantic Candidates]

    V --> F
    F --> C
```

Dense retrieval therefore follows:

```text
Query
  |
  v
Query Embedding
  |
  v
FAISS Vector Index
  |
  v
Semantic Candidates
```

---

# 16. Dense Retrieval

Dense retrieval performs semantic similarity search over the FAISS vector index.

```mermaid
flowchart TD

    Q[Research Query]

    E[BGE-small Embedding]

    V[384D Query Vector]

    F[FAISS Vector Index]

    C[Semantic Candidates]

    Q --> E
    E --> V
    V --> F
    F --> C
```

Dense retrieval is useful for:

- Semantic similarity.
- Paraphrased concepts.
- Conceptual research questions.
- Related terminology.
- Research ideas expressed with different wording.

---

# 17. BM25 / Keyword Retrieval

BM25 provides lexical retrieval over indexed research content.

```mermaid
flowchart TD

    Q[Research Query]

    T[Query Tokenization]

    B[BM25 Search]

    C[Keyword Candidates]

    Q --> T
    T --> B
    B --> C
```

BM25 is particularly useful for:

- Exact terminology.
- Technical terms.
- Paper names.
- Author names.
- Acronyms.
- Named methods.
- Identifiers.

---

# 18. Metadata Storage

Research metadata is maintained separately from the semantic retrieval index.

```mermaid
flowchart TD

    C[Research Chunks]

    M[Metadata Storage]

    P[PostgreSQL]

    D[Research Metadata]

    C --> M
    M --> P
    P --> D
```

Metadata can include information associated with:

- Papers.
- Chunks.
- Documents.
- Authors.
- Topics.
- Research attributes.

---

# 19. Metadata Filtering

Metadata filtering narrows the candidate set using structured research attributes.

```mermaid
flowchart TD

    Q[Query]

    MF[Metadata Filtering]

    PG[PostgreSQL Metadata]

    FC[Filtered Candidates]

    Q --> MF
    PG --> MF
    MF --> FC
```

Metadata filtering can be used alongside semantic and lexical retrieval.

Conceptually:

```text
Semantic Retrieval
        +
Keyword Retrieval
        +
Metadata Filtering
        =
Broader but constrained Candidate Set
```

---

# 20. PostgreSQL Research Metadata

PostgreSQL stores structured research information used during filtering and retrieval.

```mermaid
flowchart TD

    PG[PostgreSQL]

    P[Papers]

    C[Chunks]

    M[Metadata]

    PG --> P
    PG --> C
    PG --> M
```

The metadata store complements the vector and lexical indexes.

---

# 21. Retrieval Candidate Generation

The retrieval layer produces multiple candidate sets.

```mermaid
flowchart TD

    D[Dense Retrieval]

    B[BM25 / Keyword Retrieval]

    M[Metadata Filtering]

    SC[Semantic Candidates]

    KC[Keyword Candidates]

    FC[Filtered Candidates]

    D --> SC
    B --> KC
    M --> FC
```

The three candidate streams are then passed into rank fusion.

---

# 22. Reciprocal Rank Fusion

Reciprocal Rank Fusion combines candidate lists produced by multiple retrieval mechanisms.

```mermaid
flowchart TD

    SC[Semantic Candidates]

    KC[Keyword Candidates]

    FC[Filtered Candidates]

    RRF[Reciprocal Rank Fusion]

    SC --> RRF
    KC --> RRF
    FC --> RRF

    RRF --> UR[Unified Candidate Ranking]
```

RRF provides a mechanism for combining different ranking signals into a unified candidate list.

Conceptually:

```text
Dense Ranking
      +
BM25 Ranking
      +
Metadata Filtering
      |
      v
Reciprocal Rank Fusion
      |
      v
Unified Candidate Ranking
```

---

# 23. Unified Candidate Ranking

After reciprocal rank fusion, the system produces a unified candidate ranking.

```mermaid
flowchart LR

    RRF[Reciprocal Rank Fusion]

    U[Unified Candidate Ranking]

    RRF --> U
```

The unified candidate list becomes the input to the cross-encoder reranker.

---

# 24. Cross-Encoder Reranking

The cross-encoder reranker evaluates the unified candidates against the research query.

```mermaid
flowchart TD

    U[Unified Candidate Ranking]

    R[Cross-Encoder Reranker]

    TOP[Top-K Relevant Evidence]

    U --> R
    R --> TOP
```

The reranking stage improves precision after the broader candidate-generation stages.

The pipeline therefore follows:

```text
High Recall Retrieval
        |
        v
Candidate Fusion
        |
        v
Unified Ranking
        |
        v
Cross-Encoder Reranking
        |
        v
High Precision Evidence
```

---

# 25. Top-K Relevant Evidence

The final retrieval stage selects the most relevant evidence.

```mermaid
flowchart LR

    R[Cross-Encoder Reranker]

    TOP[Top-K Relevant Evidence]

    R --> TOP
```

The Top-K result set is the final retrieval output consumed by the Explore API.

---

# 26. Result Formatting

The result formatting layer converts internal retrieval results into the public API response format.

```mermaid
flowchart LR

    E[Top-K Relevant Evidence]

    F[Result Formatting]

    R[Explore API Response]

    E --> F
    F --> R
```

Formatting can include:

- Paper information.
- Chunk information.
- Relevance scores.
- Metadata.
- Search highlights.
- Source information.
- Result identifiers.

---

# 27. Explore API Response

The FastAPI endpoint returns the formatted results to the frontend.

```mermaid
flowchart TD

    R[Top-K Relevant Evidence]

    F[Result Formatting]

    API[Explore API Response]

    UI[Next.js Search Results]

    R --> F
    F --> API
    API --> UI
```

The frontend receives a structured response that can be rendered by the Explore interface.

---

# 28. End-to-End Explore Retrieval

The complete retrieval architecture is:

```mermaid
flowchart TD

    UI[Next.js Explore UI]

    API[FastAPI Explore API<br/>POST /api/v1/explore]

    V[Request Validation]

    N[Query Normalization]

    C[Adaptive Retrieval Controller]

    QA[Query Analysis]

    RP[Retrieval Planning]

    RE[Retrieval Execution]

    D[Dense Retrieval]

    DE[BGE-small Embedding]

    QV[384D Query Vector]

    FI[FAISS Vector Index]

    SC[Semantic Candidates]

    B[BM25 / Keyword Retrieval]

    QT[Query Tokenization]

    BS[BM25 Search]

    KC[Keyword Candidates]

    MF[Metadata Filtering]

    PG[PostgreSQL Metadata]

    FC[Filtered Candidates]

    RRF[Reciprocal Rank Fusion]

    UR[Unified Candidate Ranking]

    RR[Cross-Encoder Reranker]

    TOP[Top-K Relevant Evidence]

    RF[Result Formatting]

    RESP[Explore API Response]

    RESULTS[Next.js Search Results]


    UI --> API
    API --> V
    V --> N
    N --> C
    C --> QA
    QA --> RP
    RP --> RE

    RE --> D
    D --> DE
    DE --> QV
    QV --> FI
    FI --> SC

    RE --> B
    B --> QT
    QT --> BS
    BS --> KC

    RE --> MF
    MF --> PG
    PG --> FC

    SC --> RRF
    KC --> RRF
    FC --> RRF

    RRF --> UR
    UR --> RR
    RR --> TOP
    TOP --> RF
    RF --> RESP
    RESP --> RESULTS
```

---

# 29. Research Data Ingestion Architecture

The research corpus supporting Explore is created through an ingestion pipeline.

```mermaid
flowchart LR

    S[Research Sources]

    I[Document Ingestion]

    T[Text Extraction]

    C[Chunking]

    E[Embedding Generation]

    V[FAISS Vector Index]

    M[Metadata Storage]

    PG[PostgreSQL]

    S --> I
    I --> T
    T --> C

    C --> E
    E --> V

    C --> M
    M --> PG
```

This creates two complementary retrieval representations:

```text
Research Documents
        |
        v
      Chunks
      /   \
     /     \
    v       v
Embeddings Metadata
    |         |
    v         v
 FAISS   PostgreSQL
    |         |
    v         v
Dense      Filters
Retrieval
```

---

# 30. Retrieval Architecture

The retrieval architecture combines three primary candidate-generation mechanisms.

```mermaid
flowchart TD

    Q[Research Query]

    D[Dense Retrieval]

    B[BM25 / Keyword Retrieval]

    M[Metadata Filtering]

    SC[Semantic Candidates]

    KC[Keyword Candidates]

    FC[Filtered Candidates]

    RRF[Reciprocal Rank Fusion]

    Q --> D
    Q --> B
    Q --> M

    D --> SC
    B --> KC
    M --> FC

    SC --> RRF
    KC --> RRF
    FC --> RRF

    RRF --> R[Unified Candidates]
```

---

# 31. Ranking Architecture

The ranking pipeline progressively improves candidate quality.

```mermaid
flowchart LR

    C[Candidate Results]

    RRF[Reciprocal Rank Fusion]

    U[Unified Candidate Ranking]

    CE[Cross-Encoder Reranker]

    TOP[Top-K Relevant Evidence]

    C --> RRF
    RRF --> U
    U --> CE
    CE --> TOP
```

The architecture separates:

- Candidate generation.
- Candidate fusion.
- Ranking.
- High-precision reranking.

---

# 32. Explore System Boundaries

| Component | Responsibility |
|---|---|
| Next.js Explore UI | User-facing research discovery interface |
| FastAPI Explore API | HTTP API boundary |
| Request Validation | Validate incoming search requests |
| Query Normalization | Normalize research queries |
| Adaptive Retrieval Controller | Orchestrate retrieval |
| Query Analysis | Analyze query characteristics |
| Retrieval Planning | Determine retrieval strategy |
| Retrieval Execution | Execute selected retrieval mechanisms |
| Dense Retrieval | Semantic retrieval |
| BGE-small Embedding | Query and document vector representation |
| FAISS Vector Index | Vector similarity search |
| BM25 / Keyword Retrieval | Lexical retrieval |
| Query Tokenization | Prepare query for lexical search |
| BM25 Search | Keyword candidate retrieval |
| Metadata Filtering | Structured candidate filtering |
| PostgreSQL Metadata | Store structured research metadata |
| Reciprocal Rank Fusion | Combine candidate rankings |
| Unified Candidate Ranking | Produce unified candidate order |
| Cross-Encoder Reranker | High-precision relevance scoring |
| Top-K Relevant Evidence | Final evidence selection |
| Result Formatting | Convert internal results to API format |
| Explore API Response | Return structured results |
| Next.js Search Results | Render final search results |

---

# 33. Design Principles

## 33.1 Multi-Signal Retrieval

Explore does not depend on a single retrieval mechanism.

It combines:

```text
Dense Retrieval
       +
BM25 Retrieval
       +
Metadata Filtering
       |
       v
Candidate Fusion
```

This allows different retrieval signals to contribute to the final result set.

---

## 33.2 Semantic + Lexical Retrieval

Dense retrieval handles semantic similarity.

BM25 handles lexical relevance.

```mermaid
flowchart LR

    Q[Query]

    D[Semantic Search]

    B[Lexical Search]

    F[Fusion]

    Q --> D
    Q --> B

    D --> F
    B --> F
```

---

## 33.3 Retrieval Before Reranking

The cross-encoder does not search the entire corpus.

Instead:

```text
Corpus
  |
  v
Candidate Retrieval
  |
  v
Candidate Fusion
  |
  v
Cross-Encoder
  |
  v
Top-K Evidence
```

This separates broad candidate generation from precision ranking.

---

## 33.4 Metadata-Aware Retrieval

Structured metadata can constrain retrieval results.

```text
Query
  |
  +--> Dense Retrieval
  |
  +--> BM25
  |
  +--> Metadata Filtering
  |
  v
Unified Candidates
```

This enables research discovery to combine semantic, lexical, and structured signals.

---

## 33.5 Adaptive Retrieval Orchestration

The Adaptive Retrieval Controller determines how retrieval should be executed.

```mermaid
flowchart TD

    Q[Query]

    C[Adaptive Retrieval Controller]

    A[Query Analysis]

    P[Retrieval Planning]

    E[Retrieval Execution]

    Q --> C
    C --> A
    A --> P
    P --> E
```

---

# 34. Complete Explore Architecture

```mermaid
flowchart TD

    UI[Next.js Explore UI]

    API[FastAPI Explore API]

    V[Request Validation]

    N[Query Normalization]

    C[Adaptive Retrieval Controller]

    QA[Query Analysis]

    RP[Retrieval Planning]

    RE[Retrieval Execution]


    subgraph SEMANTIC["Dense Retrieval"]

        D[BGE-small Embedding]

        QV[384D Query Vector]

        FAISS[FAISS Vector Index]

        SC[Semantic Candidates]

        D --> QV
        QV --> FAISS
        FAISS --> SC

    end


    subgraph LEXICAL["BM25 / Keyword Retrieval"]

        QT[Query Tokenization]

        BM[BM25 Search]

        KC[Keyword Candidates]

        QT --> BM
        BM --> KC

    end


    subgraph METADATA["Metadata Filtering"]

        PG[PostgreSQL Metadata]

        FC[Filtered Candidates]

        PG --> FC

    end


    RRF[Reciprocal Rank Fusion]

    UR[Unified Candidate Ranking]

    CE[Cross-Encoder Reranker]

    TOP[Top-K Relevant Evidence]

    RF[Result Formatting]

    RESP[Explore API Response]

    RESULTS[Next.js Search Results]


    UI --> API
    API --> V
    V --> N
    N --> C

    C --> QA
    QA --> RP
    RP --> RE

    RE --> SEMANTIC
    RE --> LEXICAL
    RE --> METADATA

    SC --> RRF
    KC --> RRF
    FC --> RRF

    RRF --> UR
    UR --> CE
    CE --> TOP
    TOP --> RF
    RF --> RESP
    RESP --> RESULTS
```

---

# 35. Explore Data Flow Summary

```text
Research Sources
      |
      v
Document Ingestion
      |
      v
Text Extraction
      |
      v
Chunking
      |
      +----------------------+
      |                      |
      v                      v
Embedding Generation    Metadata Storage
      |                      |
      v                      v
FAISS Vector Index      PostgreSQL
      |                      |
      +----------+-----------+
                 |
                 v
          Explore Query
                 |
                 v
       Request Validation
                 |
                 v
        Query Normalization
                 |
                 v
    Adaptive Retrieval Controller
                 |
                 v
          Query Analysis
                 |
                 v
        Retrieval Planning
                 |
                 v
        Retrieval Execution
                 |
       +---------+---------+
       |         |         |
       v         v         v
     Dense     BM25    Metadata
       |         |      Filtering
       v         v         v
   Semantic   Keyword   Filtered
 Candidates  Candidates Candidates
       \         |         /
        \        |        /
         +-------+-------+
                 |
                 v
      Reciprocal Rank Fusion
                 |
                 v
      Unified Candidate Ranking
                 |
                 v
       Cross-Encoder Reranker
                 |
                 v
        Top-K Relevant Evidence
                 |
                 v
          Result Formatting
                 |
                 v
        Explore API Response
                 |
                 v
       Next.js Search Results
```

---

# 36. Core Explore Principle

The Explore module follows:

```text
Research Query
      ↓
Query Understanding
      ↓
Retrieval Planning
      ↓
Multi-Signal Retrieval
      ↓
Candidate Fusion
      ↓
Unified Ranking
      ↓
Cross-Encoder Reranking
      ↓
Top-K Relevant Evidence
      ↓
Structured API Response
      ↓
Research Discovery UI
```

The core principle is:

> **Explore combines semantic retrieval, lexical retrieval, and metadata filtering before applying increasingly precise ranking and reranking stages to produce high-quality research evidence.**


# Explore

![Explore Architecture](img/explore.png)

![Explore Architecture 2](img/explore%20(2).png)

![Explore Adaptive Retrieval Architecture](img/Explore%20Adaptive%20Retrieval%20Architecture.png)