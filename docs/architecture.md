AI Research Assistant --- Technical Architecture

Detailed component and data-flow architecture for the AI Research
Assistant research-intelligence platform.

1. Architecture Overview

The AI Research Assistant is a layered research-intelligence platform
that combines:

A Next.js frontend for exploration, research, reports, and
knowledge-graph workflows.

A FastAPI /api/v1 application layer for authentication and API
orchestration.

A Research Intelligence layer responsible for planning,
retrieval, evidence assembly, LLM generation, and report creation.

A Retrieval / AI infrastructure layer containing dense vector
search, sparse keyword search, hybrid retrieval, reranking, and
external LLM access.

A PostgreSQL data layer for persistent application, document,
research, and knowledge-graph data.

The architecture separates persistent relational data from vector-search
infrastructure. PostgreSQL stores application/document metadata and
research state, while FAISS stores and searches normalized embedding
vectors.

2. High-Level Architecture

┌─────────────────────────────────────────────────────────────────────┐
│                         USER / RESEARCHER                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION                                │
│                                                                     │
│  Next.js Frontend                                                  │
│  ┌────────────┐ ┌──────────────────┐ ┌────────────┐ ┌────────────┐ │
│  │ Explore UI │ │ Research /       │ │ Reports UI │ │ Knowledge  │ │
│  │            │ │ Assistant UI     │ │            │ │ Graph UI   │ │
│  └────────────┘ └──────────────────┘ └────────────┘ └────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS / API
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API / APPLICATION                           │
│                                                                     │
│                    FastAPI — /api/v1                                │
│                 Authentication + API Services                       │
│                                                                     │
│       ┌─────────┬──────────┬─────────┬────────────────┐             │
│       │ Explore │ Research │ Reports │ Knowledge Graph│             │
│       └────┬────┴─────┬────┴────┬────┴───────┬────────┘             │
└────────────┼──────────┼──────────┼────────────┼─────────────────────┘
             │          │          │            │
             ▼          ▼          ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RESEARCH INTELLIGENCE                          │
│                                                                     │
│  Explore Track                  Research Pipeline                   │
│  ┌────────────────┐             ┌──────────────────────────────┐    │
│  │ Explore Service│             │ Query Planner                │    │
│  └───────┬────────┘             └──────────────┬───────────────┘    │
│          ▼                                     ▼                    │
│  ┌────────────────┐             ┌──────────────────────────────┐    │
│  │ Ranked Sources │────────────▶│ Retrieval Adapter            │    │
│  └───────┬────────┘             └──────────────┬───────────────┘    │
│          ▼                                     ▼                    │
│  ┌────────────────┐             ┌──────────────────────────────┐    │
│  │ Interactive    │             │ Retrieval Pipeline           │    │
│  │ Exploration    │             │ Dense + BM25 + Filters       │    │
│  └────────────────┘             └──────────────┬───────────────┘    │
│                                                ▼                    │
│                                      Hybrid Retrieval               │
│                                                ▼                    │
│                                      Reciprocal Rank Fusion         │
│                                                ▼                    │
│                                      Cross-Encoder Reranker         │
│                                                ▼                    │
│                                      Evidence Assembly              │
│                                                ▼                    │
│                                        LLM Pipeline                 │
│                                                ▼                    │
│                                      Research Result                │
│                                                ▼                    │
│                                      Research Report                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL / AI INFRASTRUCTURE                    │
│                                                                     │
│  BGE-small Embeddings → Normalized Vectors → FAISS IndexFlatIP     │
│                                      │                              │
│                                      ▼                              │
│                              Shared IndexRegistry                  │
│                                      │                              │
│                                      ▼                              │
│                           Document / Chunk IDs                      │
│                                                                     │
│  BM25 / Keyword Index ────────▶ Sparse Retrieval                    │
│  Cross-Encoder Model ─────────▶ Pairwise Relevance Reranking        │
│  OpenRouter ──────────────────▶ External LLM Gateway / Provider     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              DATA                                   │
│                                                                     │
│                           PostgreSQL                                │
│                                                                     │
│ Users & Authentication     Papers / Documents                       │
│ Document Chunks            Metadata                                 │
│ Research Projects          Research Executions & Results            │
│ Knowledge Graph Entities   Knowledge Graph Relations                │
│ Index Metadata                                                        │
└─────────────────────────────────────────────────────────────────────┘

3. Architectural Layers

3.1 Presentation Layer

The presentation layer is implemented with Next.js and provides the
researcher-facing application.

Explore UI

The Explore interface supports fast document and knowledge-base
discovery. It is primarily retrieval-oriented and can operate without an
LLM for basic browsing and source discovery.

Typical flow:

User Query
   ↓
Explore API
   ↓
Explore Service
   ↓
Retrieval
   ↓
Ranked Sources
   ↓
Interactive Exploration

Research / Assistant UI

The Research / Assistant interface provides the primary research
workflow.

It submits a research question to the backend, where the question can be
planned, decomposed, retrieved against the knowledge base, grounded in
evidence, and synthesized by the LLM pipeline.

Research Question
       ↓
Query Planner
       ↓
Retrieval Adapter
       ↓
Retrieval Pipeline
       ↓
Evidence Assembly
       ↓
LLM Pipeline
       ↓
Research Result

Reports UI

The Reports interface presents persisted research outputs as exportable
research reports.

Reports are downstream of the research execution and use the assembled
evidence and generated research result.

Knowledge Graph UI

The Knowledge Graph interface exposes relationships between research
entities such as:

Papers

Authors

Topics

Citations

Research entities

4. API / Application Layer

The backend exposes the application through FastAPI under /api/v1.

Responsibilities

Authentication and authorization

Request validation

API routing

Research orchestration

Explore orchestration

Report access and generation

Knowledge-graph access

Persistence coordination

Integration with retrieval and LLM services

The application layer should remain separate from low-level retrieval
implementations so that API routes do not directly manage FAISS, BM25,
reranking, or LLM provider details.

5. Research Intelligence Layer

The Research Intelligence layer contains the core research workflow.

5.1 Explore Service

The Explore Service provides retrieval-first discovery.

Responsibilities include:

Accepting exploration queries

Executing retrieval

Applying ranking

Returning relevant sources

Supporting interactive source exploration

The Explore path is intentionally lighter than full research synthesis.

Explore Request
      ↓
Explore Service
      ↓
Ranked Sources
      ↓
Interactive Exploration

5.2 Research Pipeline

The Research Pipeline is the main orchestration layer for research
generation.

Conceptually:

Question
   ↓
Plan
   ↓
Retrieve
   ↓
Rerank
   ↓
Evidence Assembly
   ↓
Synthesize
   ↓
Research Result
   ↓
Research Report

Its major components are:

Query Planner

Retrieval Adapter

Retrieval Pipeline

Evidence Assembly

LLM Pipeline

Research Result

Research Report

5.3 Query Planner

The Query Planner converts a research question into a retrieval plan.

A complex research question may be decomposed into multiple sub-queries.

Research Question
       ↓
Query Analysis
       ↓
Sub-query / Retrieval Plan
       ↓
Retrieval Adapter

The planner should remain independent of the underlying retrieval
implementation.

5.4 Retrieval Adapter

The Retrieval Adapter provides a uniform interface between the research
pipeline and retrieval infrastructure.

This abstraction allows the research pipeline to request evidence
without depending directly on FAISS, BM25, metadata filters, or
individual retrieval implementations.

Conceptually:

Research Pipeline
       ↓
Retrieval Adapter
       ↓
Retrieval Pipeline
       ├── Dense Retrieval
       ├── BM25 / Keyword Retrieval
       └── Metadata Filtering

5.5 Evidence Assembly

Evidence Assembly converts ranked retrieval results into structured
context for generation.

Responsibilities include:

Selecting high-quality evidence

Preserving document/chunk identity

Maintaining source metadata

Constructing grounded context

Preserving citation information

Preparing context for the LLM pipeline

The key invariant is:

Generated research should be grounded in retrieved evidence rather
than relying solely on the model's prior knowledge.

5.6 LLM Pipeline

The LLM Pipeline is responsible for grounded generation.

It receives:

Research question

Retrieval plan

Retrieved evidence

Source metadata

Relevant citations

and produces the research result.

The external model gateway shown in the architecture is OpenRouter,
which provides access to configured LLM providers/models.

Evidence
   ↓
Prompt Construction
   ↓
LLM Gateway
   ↓
Generated Research Result

5.7 Research Result

A Research Result represents the grounded answer produced by the
research pipeline.

It should retain enough information to connect the generated answer back
to the evidence used to produce it.

Typical conceptual fields include:

Research question

Generated answer

Sources

Citations

Research execution metadata

Timestamps

Status

5.8 Research Report

A Research Report is the presentation/export layer for a completed
research result.

Research Result
      ↓
Report Generation
      ↓
Research Report

Reports should preserve evidence provenance and citations so that a
researcher can inspect the basis of the generated findings.

6. Retrieval / AI Infrastructure

The retrieval subsystem is designed as a multi-stage retrieval
architecture.

6.1 Embedding Model

The architecture uses BGE-small embeddings for document chunks and
queries.

Document Chunk
      ↓
BGE-small Encoder
      ↓
Embedding Vector
      ↓
Normalization

Query embeddings are generated using the same embedding space.

6.2 Normalized Vectors

Vectors are normalized before similarity search.

This allows inner-product search to behave as cosine-similarity search
when vectors are unit normalized.

Embedding
   ↓
L2 Normalization
   ↓
Normalized Vector

6.3 FAISS Index

The dense vector store is represented by a FAISS IndexFlatIP
index.

Normalized Vectors
        ↓
FAISS IndexFlatIP
        ↓
Dense Candidate Retrieval

IndexFlatIP performs exact inner-product similarity search over the
indexed vectors.

6.4 Shared IndexRegistry

The Shared IndexRegistry provides the common lifecycle and lookup layer
for retrieval indexes.

It acts as the shared source of truth for:

Dense vector index access

Vector IDs

Index metadata

Index lifecycle

Lookup between vector IDs and document/chunk records

The registry prevents separate retrieval paths from accidentally
creating independent or inconsistent indexes.

                ┌────────────────────┐
                │  Shared            │
                │  IndexRegistry     │
                └─────────┬──────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      Dense Vector Index        Index Metadata
             │
             ▼
      Document / Chunk IDs

6.5 Document / Chunk IDs

Vector indexes should resolve retrieved vector identifiers back to
document and chunk records.

The mapping is conceptually:

Vector ID
   ↓
Document / Chunk ID
   ↓
Document Chunk
   ↓
Metadata + Source

This mapping is critical for citation generation and evidence
provenance.

6.6 BM25 / Keyword Retrieval

The sparse retrieval path provides lexical matching.

Query
 ↓
BM25 / Keyword Index
 ↓
Sparse Candidate Results

This complements dense retrieval because exact terminology, identifiers,
names, and domain-specific phrases may not always be captured optimally
by semantic embeddings.

6.7 Metadata Filtering

Metadata filtering restricts retrieval using structured document
attributes.

Possible filtering dimensions include:

Paper/document identity

Source metadata

Topics

Authors

Other indexed metadata

The metadata filter is applied as part of the retrieval pipeline rather
than being implemented independently by each API route.

7. Hybrid Retrieval

The retrieval pipeline combines dense and sparse retrieval.

                    Query
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Dense Retrieval         BM25 / Keyword
          │                       │
          └───────────┬───────────┘
                      ▼
              Hybrid Retrieval
                      ↓
          Reciprocal Rank Fusion
                      ↓
            Cross-Encoder Reranker
                      ↓
             Ranked Evidence

Dense Retrieval

Finds semantically similar document chunks using normalized embedding
vectors.

Sparse Retrieval

Finds lexical matches using BM25 / keyword search.

Hybrid Retrieval

Combines candidate sets from both retrieval strategies.

Reciprocal Rank Fusion

RRF combines ranked lists into a unified ranking without requiring the
raw scores from different retrieval systems to be directly comparable.

Cross-Encoder Reranking

The Cross-Encoder performs pairwise relevance evaluation between a query
and candidate text.

Query + Candidate Chunk
          ↓
    Cross-Encoder
          ↓
   Relevance Score
          ↓
   Final Top-K Ranking

This creates a multi-stage retrieval architecture:

Candidate Generation
        ↓
Dense + Sparse
        ↓
Rank Fusion
        ↓
Precision Reranking
        ↓
Evidence Selection

8. Knowledge Graph Architecture

The Knowledge Graph provides structured relationships between research
entities.

Core entity types

Paper
 ├── Author
 ├── Topic
 ├── Citation
 └── Research Entity

The graph can represent relationships such as:

Paper → written by → Author

Paper → belongs to → Topic

Paper → cites → Paper

Paper → associated with → Research Entity

Graph data is persisted in PostgreSQL.

The Knowledge Graph UI accesses the graph through the FastAPI
application layer rather than directly connecting to the database.

9. Data Layer

PostgreSQL

PostgreSQL is the primary persistent relational data store.

It stores application state and structured research data rather than
acting as the primary dense vector-search engine in this architecture.

The main logical data domains are:

Domain                              Purpose

Users & Authentication              User accounts, credentials, and
authentication state

Papers / Documents                  Research documents and source
metadata

Document Chunks                     Chunked document content used for
retrieval

Metadata                            Structured document/source metadata

Research Projects                   Persistent research
workspace/project state

Research Executions & Results       Execution state, generated answers,
and research outputs

Knowledge Graph Entities            Papers, authors, topics, citations,
and research entities

Knowledge Graph Relations           Relationships between graph
entities

10. Vector Data vs Relational Data

A key architectural separation is:

                 DATA STORAGE
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     PostgreSQL                  FAISS
          │                       │
          │                       ├── Embedding vectors
          │                       ├── Vector IDs
          │                       └── Dense similarity search
          │
          ├── Users
          ├── Documents
          ├── Chunks
          ├── Metadata
          ├── Research Projects
          ├── Executions / Results
          └── Knowledge Graph

This separation allows relational persistence and dense retrieval to
evolve independently.

11. End-to-End Research Data Flow

A complete research request follows this conceptual flow:

1. User
   │
   ▼
2. Research / Assistant UI
   │
   ▼
3. FastAPI /api/v1
   │
   ▼
4. Research Pipeline
   │
   ▼
5. Query Planner
   │
   ▼
6. Retrieval Adapter
   │
   ▼
7. Retrieval Pipeline
   │
   ├── Dense Retrieval
   │      └── BGE-small → FAISS IndexFlatIP
   │
   ├── BM25 / Keyword Retrieval
   │
   └── Metadata Filtering
   │
   ▼
8. Hybrid Retrieval
   │
   ▼
9. Reciprocal Rank Fusion
   │
   ▼
10. Cross-Encoder Reranking
    │
    ▼
11. Evidence Assembly
    │
    ▼
12. LLM Pipeline
    │
    └── OpenRouter / configured model provider
    │
    ▼
13. Research Result
    │
    ▼
14. Research Report
    │
    ▼
15. PostgreSQL persistence

12. Explore Data Flow

Explore is optimized for source discovery rather than full synthesis.

User
 ↓
Explore UI
 ↓
FastAPI
 ↓
Explore Service
 ↓
Retrieval
 ↓
Ranked Sources
 ↓
Interactive Exploration

The Explore path can therefore provide useful retrieval results even
when an LLM generation step is unnecessary.

13. Research / Assistant Data Flow

The Assistant workflow is more comprehensive:

User Question
     ↓
Research / Assistant UI
     ↓
FastAPI
     ↓
Research Pipeline
     ↓
Query Planner
     ↓
Retrieval Adapter
     ↓
Retrieval Pipeline
     ↓
Dense + BM25 + Metadata Filters
     ↓
Hybrid Retrieval
     ↓
RRF
     ↓
Cross-Encoder Reranking
     ↓
Evidence Assembly
     ↓
LLM Pipeline
     ↓
Grounded Research Result
     ↓
Research UI / Reports

14. Report Data Flow

Reports consume completed research outputs.

Research Execution
       ↓
Research Result
       ↓
Evidence / Citations
       ↓
Report Generation
       ↓
Research Report
       ↓
Reports UI

The report layer should not independently invent research evidence. Its
source of truth is the completed research result and its associated
evidence.

15. Authentication and Security

Authentication sits at the application boundary.

User
 ↓
Next.js
 ↓
Authentication API
 ↓
FastAPI
 ↓
Authenticated Request
 ↓
Protected Research / Data APIs

The backend should enforce authorization independently of frontend route
protection.

Security responsibilities include:

Credential validation

Token/session validation

Protected API endpoints

User-scoped research projects

User-scoped research executions/results

Secure handling of external LLM credentials

Environment-based configuration

No secrets committed to source control

16. Component Responsibilities

Component              Responsibility

Next.js Frontend       User interaction and presentation
Explore Service        Retrieval-first exploration
Research Pipeline      End-to-end research orchestration
Query Planner          Query analysis and decomposition
Retrieval Adapter      Uniform retrieval interface
Retrieval Pipeline     Multi-stage retrieval execution
Dense Retrieval        Semantic candidate generation
BM25 / Keyword         Lexical candidate generation
Metadata Filter        Structured retrieval constraints
Hybrid Retrieval       Dense/sparse candidate combination
RRF                    Rank-list fusion
Cross-Encoder          Precision reranking
Evidence Assembly      Grounded context construction
LLM Pipeline           Evidence-grounded synthesis
OpenRouter             External LLM gateway/provider access
Shared IndexRegistry   Shared retrieval index lifecycle/lookup
PostgreSQL             Persistent relational application/research data
FAISS                  Dense vector similarity search
Knowledge Graph        Structured research relationships
Reports                Exportable/presentable research outputs

17. Architectural Principles

Separation of Concerns

Frontend, API, research orchestration, retrieval, AI inference, and
persistence should remain independently testable.

Shared Retrieval Infrastructure

All research retrieval paths should use the shared retrieval
infrastructure and IndexRegistry rather than creating ad-hoc indexes.

Evidence-First Generation

LLM synthesis should operate on explicitly assembled evidence.

Provenance Preservation

Every retrieved chunk should remain traceable to its document/source
metadata so that generated answers can provide citations.

Multi-Stage Retrieval

Retrieval should progressively improve precision:

Broad Candidate Generation
        ↓
Dense + Sparse
        ↓
Fusion
        ↓
Reranking
        ↓
Evidence Selection

API Boundary

Frontend code should communicate through the FastAPI API rather than
directly accessing PostgreSQL, FAISS, or external model providers.

Persistent Research State

Research projects, executions, results, and graph entities should remain
persistent in PostgreSQL so workflows can be revisited and reported
later.

18. Reliability and Consistency Requirements

The architecture depends on several important invariants.

Retrieval Index Consistency

Vector IDs must resolve correctly to document/chunk records.

FAISS Vector ID
      ↓
IndexRegistry
      ↓
Document / Chunk ID
      ↓
PostgreSQL Document Chunk

Filter Consistency

Document and paper filters must use the identifier type expected by the
underlying retrieval and persistence layers.

Shared Pipeline Consistency

Explore and Research should not silently maintain separate retrieval
indexes when they are intended to operate over the same knowledge base.

Citation Consistency

Evidence selected for generation must retain its source identity
through:

Retrieval
   ↓
Reranking
   ↓
Evidence Assembly
   ↓
LLM Prompt
   ↓
Research Result
   ↓
Report

19. Deployment View

The logical production deployment can be represented as:

                         Internet
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
      Next.js Frontend              FastAPI Backend
             │                             │
             │ HTTPS                       │
             └─────────────────────────────┘
                                           │
                          ┌────────────────┼────────────────┐
                          ▼                ▼                ▼
                     PostgreSQL       FAISS / Index     OpenRouter
                     Persistent       Retrieval         External LLM
                     Data             Infrastructure    Gateway

The frontend should contain only public configuration required for API
communication. Secrets and provider credentials belong on the backend.

20. Observability

The research pipeline should expose enough structured information to
diagnose failures across stages.

Recommended execution-level observability:

Request
  ↓
Authentication
  ↓
Planning
  ↓
Retrieval
  ↓
Fusion
  ↓
Reranking
  ↓
Evidence Assembly
  ↓
LLM
  ↓
Persistence

Each stage should ideally record:

Execution status

Duration

Error information

Input/output counts

Retrieved source counts

Reranked source counts

LLM invocation status

Persistence status

This makes it possible to distinguish retrieval failures from LLM,
authentication, API, or persistence failures.

21. Testing Strategy

Unit Tests

Test individual components:

Query Planner

Retrieval Adapter

Dense Retrieval

BM25 retrieval

Metadata filtering

RRF

Cross-Encoder reranking

Evidence Assembly

LLM prompt construction

Integration Tests

Test:

API
 ↓
Research Pipeline
 ↓
Retrieval Infrastructure
 ↓
PostgreSQL

End-to-End Tests

Test complete researcher workflows:

Register / Login
      ↓
Explore
      ↓
Select / inspect sources
      ↓
Ask research question
      ↓
Generate grounded result
      ↓
Open report

Retrieval Validation

Use known documents and questions to verify:

Relevant documents are retrieved.

Filters are respected.

Vector IDs resolve correctly.

Hybrid retrieval combines candidate sets correctly.

Reranking changes ordering appropriately when relevance differs.

Citations map back to the correct source chunks.

22. Scalability Considerations

The architecture can scale by separating workloads:

API Scaling

Run multiple FastAPI instances behind a load balancer.

Frontend Scaling

Deploy the Next.js application independently from the backend.

Retrieval Scaling

The retrieval layer can evolve from a local FAISS deployment toward a
dedicated vector-search service if dataset size or concurrency requires
it.

LLM Scaling

OpenRouter provides an abstraction over external model providers,
allowing the configured model/provider to change without redesigning the
research pipeline.

Database Scaling

PostgreSQL can be scaled independently for persistent application and
research state.

23. Failure Boundaries

The architecture intentionally creates clear failure boundaries.

Authentication Failure

Stops the request before protected research operations.

Retrieval Failure

Prevents or degrades evidence generation while keeping the API available
for unrelated functionality.

Reranking Failure

Can be handled as a retrieval-stage failure or degraded mode depending
on application policy.

LLM Failure

Should not erase successfully retrieved evidence. The research execution
should retain enough state to diagnose or retry generation.

Persistence Failure

Should be reported independently from successful retrieval/generation so
that transient database issues do not obscure the underlying research
execution.

24. Architecture Summary

The AI Research Assistant follows a layered, evidence-grounded
architecture:

                 USER
                   │
                   ▼
             Next.js UI
                   │
                   ▼
            FastAPI /api/v1
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   Explore Service      Research Pipeline
                              │
                         Query Planner
                              │
                       Retrieval Adapter
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             Dense          BM25       Metadata
             Search        Search        Filter
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                      Hybrid Retrieval
                              ▼
                           RRF
                              ▼
                    Cross-Encoder
                       Reranking
                              ▼
                     Evidence Assembly
                              ▼
                        LLM Pipeline
                              │
                         OpenRouter
                              ▼
                     Research Result
                              ▼
                     Research Report
                              │
                              ▼
                         PostgreSQL

The central design goal is to keep retrieval, evidence, generation,
provenance, and persistence connected through explicit interfaces.
This allows the system to provide fast exploration, structured research
workflows, grounded LLM answers, and exportable reports while
maintaining traceability from generated output back to the underlying
research sources.