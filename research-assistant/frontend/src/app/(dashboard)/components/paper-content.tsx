"use client";

import { useState } from "react";
import {
  FileText,
  Loader2,
  ChevronRight,
  Database,
  Hash,
} from "lucide-react";

import { useDocuments } from "@/lib/queries/documents";
import { useSections } from "@/lib/queries/sections";
import { useChunks } from "@/lib/queries/chunks";

import type { Document } from "@/types/document";
import type { Section } from "@/types/section";
import type { Chunk } from "@/types/chunk";

import { SectionLabel, Divider } from "./primitives";

export function PaperContent({
  paperId,
}: {
  paperId: string;
}) {
  const [selectedDocumentId, setSelectedDocumentId] =
    useState<string | null>(null);

  const [selectedSectionId, setSelectedSectionId] =
    useState<string | null>(null);

  const {
    data: documents,
    isLoading: documentsLoading,
    isError: documentsIsError,
    error: documentsError,
  } = useDocuments(paperId);

  const {
    data: sections,
    isLoading: sectionsLoading,
    isError: sectionsIsError,
  } = useSections(selectedDocumentId);

  const {
    data: chunks,
    isLoading: chunksLoading,
    isError: chunksIsError,
  } = useChunks(selectedSectionId);

  /* ----------------------------------------------------------------------- */
  /* Documents                                                               */
  /* ----------------------------------------------------------------------- */

  if (documentsLoading) {
    return (
      <LoadingState message="Loading document content..." />
    );
  }

  if (documentsIsError) {
    return (
      <ErrorState
        title="Unable to load documents"
        message={
          documentsError instanceof Error
            ? documentsError.message
            : "Unable to load documents for this paper."
        }
      />
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <EmptyState
        title="No document available"
        description="This paper has not been ingested into the document pipeline yet."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* Documents                                                          */}
      {/* ------------------------------------------------------------------ */}

      <section>
        <div className="flex items-center justify-between">
          <SectionLabel>Documents</SectionLabel>

          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
            {documents.length}{" "}
            {documents.length === 1 ? "document" : "documents"}
          </span>
        </div>

        <div className="mt-3 space-y-2">
          {documents.map((document) => {
            const documentId = String(document.id);
            const selected = selectedDocumentId === documentId;

            return (
              <button
                key={documentId}
                type="button"
                onClick={() => {
                  setSelectedDocumentId(documentId);
                  setSelectedSectionId(null);
                }}
                className={[
                  "w-full rounded-md border p-4 text-left transition-colors",
                  selected
                    ? "border-primary bg-primary/5"
                    : "border-border bg-surface hover:border-strong-border",
                ].join(" ")}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={[
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-md border",
                      selected
                        ? "border-primary/30 bg-primary/10"
                        : "border-border bg-background",
                    ].join(" ")}
                  >
                    <FileText
                      className={[
                        "h-4 w-4",
                        selected
                          ? "text-primary"
                          : "text-faint",
                      ].join(" ")}
                    />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] text-foreground">
                      {getDocumentTitle(document)}
                    </p>

                    <div className="mt-1 flex items-center gap-2">
                      <span className="text-[10px] text-faint">
                        {getDocumentType(document)}
                      </span>

                      <span className="text-faint">·</span>

                      <span className="font-mono-tech text-[9px] uppercase tracking-wider text-faint">
                        {documentId}
                      </span>
                    </div>
                  </div>

                  <ChevronRight
                    className={[
                      "h-4 w-4 shrink-0 transition-transform",
                      selected
                        ? "rotate-90 text-primary"
                        : "text-faint",
                    ].join(" ")}
                  />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Sections                                                           */}
      {/* ------------------------------------------------------------------ */}

      {selectedDocumentId && (
        <>
          <Divider />

          <section>
            <div className="flex items-center justify-between">
              <SectionLabel>Sections</SectionLabel>

              {sections && (
                <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                  {sections.items.length}{" "}
                  {sections.items.length === 1
                    ? "section"
                    : "sections"}
                </span>
              )}
            </div>

            {sectionsLoading ? (
              <LoadingInline message="Loading sections..." />
            ) : sectionsIsError ? (
              <ErrorInline message="Unable to load sections for this document." />
            ) : !sections || sections.items.length === 0 ? (
              <EmptyInline message="No sections have been extracted for this document yet." />
            ) : (
              <div className="mt-3 space-y-2">
                {sections.items.map((section) => {
                  const sectionId = String(section.id);
                  const selected =
                    selectedSectionId === sectionId;

                  return (
                    <button
                      key={sectionId}
                      type="button"
                      onClick={() =>
                        setSelectedSectionId(sectionId)
                      }
                      className={[
                        "w-full rounded-md border p-3 text-left transition-colors",
                        selected
                          ? "border-primary bg-primary/5"
                          : "border-border bg-surface hover:border-strong-border",
                      ].join(" ")}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <Hash className="h-3 w-3 shrink-0 text-faint" />

                            <p className="truncate text-[13px] text-foreground">
                              {getSectionTitle(section)}
                            </p>
                          </div>

                          {getSectionNumber(section) && (
                            <p className="mt-1 pl-5 font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                              Section {getSectionNumber(section)}
                            </p>
                          )}
                        </div>

                        <ChevronRight
                          className={[
                            "h-4 w-4 shrink-0 transition-transform",
                            selected
                              ? "rotate-90 text-primary"
                              : "text-faint",
                          ].join(" ")}
                        />
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Chunks                                                             */}
      {/* ------------------------------------------------------------------ */}

      {selectedSectionId && (
        <>
          <Divider />

          <section>
            <div className="flex items-center justify-between">
              <SectionLabel>Section Content</SectionLabel>

              {chunks && (
                <div className="flex items-center gap-1.5">
                  <Database className="h-3 w-3 text-faint" />

                  <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                    {chunks.items.length}{" "}
                    {chunks.items.length === 1
                      ? "chunk"
                      : "chunks"}
                  </span>
                </div>
              )}
            </div>

            {chunksLoading ? (
              <LoadingInline message="Loading section content..." />
            ) : chunksIsError ? (
              <ErrorInline message="Unable to load section content." />
            ) : !chunks || chunks.items.length === 0 ? (
              <EmptyInline message="No content chunks are available for this section yet." />
            ) : (
              <div className="mt-3 space-y-3">
                {chunks.items.map((chunk, index) => {
                  const chunkId = String(
                    chunk.id ?? index,
                  );

                  const content =
                    getChunkContent(chunk);

                  return (
                    <article
                      key={chunkId}
                      className="rounded-md border border-border bg-surface p-4 transition-colors hover:border-strong-border"
                    >
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <Database className="h-3 w-3 text-primary-soft" />

                          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                            Chunk{" "}
                            {String(index + 1).padStart(
                              3,
                              "0",
                            )}
                          </span>
                        </div>

                        <span className="font-mono-tech text-[9px] text-faint">
                          {chunkId}
                        </span>
                      </div>

                      <p className="whitespace-pre-wrap text-[13px] leading-7 text-secondary-foreground">
                        {content}
                      </p>

                      <div className="mt-4 flex items-center gap-3 border-t border-border/60 pt-3">
                        <span className="font-mono-tech text-[9px] uppercase tracking-wider text-faint">
                          Retrieval unit
                        </span>

                        {getChunkMetadata(chunk) && (
                          <span className="text-[10px] text-faint">
                            {getChunkMetadata(chunk)}
                          </span>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

/* ========================================================================== */
/* Helpers                                                                    */
/* ========================================================================== */

function getDocumentTitle(
  document: Document,
): string {
  return document.filename || "Untitled document";
}

function getDocumentType(
  document: Document,
): string {
  return document.document_type || "Document";
}

function getSectionTitle(
  section: Section,
): string {
  return section.title || "Untitled section";
}

function getSectionNumber(
  section: Section,
): string | null {
  return section.section_number || null;
}

function getChunkContent(
  chunk: Chunk,
): string {
  return chunk.text || "No content available.";
}

function getChunkMetadata(
  chunk: Chunk,
): string | null {
  if (chunk.token_count !== null) {
    return `${chunk.token_count} tokens`;
  }

  if (chunk.position !== undefined) {
    return `position ${chunk.position}`;
  }

  if (
    chunk.metadata &&
    Object.keys(chunk.metadata).length > 0
  ) {
    return "metadata available";
  }

  return null;
}

/* ========================================================================== */
/* Loading / Error / Empty States                                             */
/* ========================================================================== */

function LoadingState({
  message,
}: {
  message: string;
}) {
  return (
    <div className="py-16 text-center">
      <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-faint" />

      <p className="text-[13px] text-muted-foreground">
        {message}
      </p>
    </div>
  );
}

function LoadingInline({
  message,
}: {
  message: string;
}) {
  return (
    <div className="flex items-center gap-2 py-6">
      <Loader2 className="h-4 w-4 animate-spin text-faint" />

      <span className="text-[12px] text-muted-foreground">
        {message}
      </span>
    </div>
  );
}

function EmptyInline({
  message,
}: {
  message: string;
}) {
  return (
    <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
      {message}
    </p>
  );
}

function ErrorInline({
  message,
}: {
  message: string;
}) {
  return (
    <div className="mt-3 rounded-md border border-border bg-surface px-4 py-3">
      <p className="text-[12px] text-muted-foreground">
        {message}
      </p>
    </div>
  );
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <FileText className="mb-3 h-5 w-5 text-faint" />

      <SectionLabel>{title}</SectionLabel>

      <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

function ErrorState({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <SectionLabel>{title}</SectionLabel>

      <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
        {message}
      </p>
    </div>
  );
}