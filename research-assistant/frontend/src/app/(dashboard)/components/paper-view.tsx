"use client";

import { useState } from "react";
import {
  ArrowLeft,
  Microscope,
  GitCompare,
  MessageSquareText,
  Plus,
  ExternalLink,
  FileText,
  Loader2,
} from "lucide-react";
import Link from "next/link";

import { usePaper } from "@/lib/queries/papers";

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "./ui/tabs";

import {
  SectionLabel,
  Divider,
  MetricLabel,
} from "./primitives";

import { PaperContent } from "./paper-content";

export function PaperView({
  paperId,
}: {
  paperId: string;
}) {
  const [tab, setTab] = useState("overview");

  const {
    data: paper,
    isLoading,
    isError,
    error,
  } = usePaper(paperId);

  /*
   * -------------------------------------------------------------------------
   * Loading
   * -------------------------------------------------------------------------
   */

  if (isLoading) {
    return (
      <div className="py-20 text-center">
        <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-faint" />

        <p className="text-[13px] text-muted-foreground">
          Loading paper...
        </p>
      </div>
    );
  }

  /*
   * -------------------------------------------------------------------------
   * Error
   * -------------------------------------------------------------------------
   */

  if (isError) {
    return (
      <div className="px-6 py-8 md:px-10">
        <div className="mx-auto max-w-4xl">
          <Link
            href="/papers"
            className="mb-5 inline-flex items-center gap-1.5 text-[12px] text-faint transition-colors hover:text-muted-foreground"
          >
            <ArrowLeft className="h-3 w-3" />
            All papers
          </Link>

          <div className="rounded-md border border-border bg-surface p-5">
            <p className="text-[14px] text-muted-foreground">
              Unable to load this paper.
            </p>

            <p className="mt-1 text-[11px] text-faint">
              {error instanceof Error
                ? error.message
                : "Failed to load paper"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  /*
   * -------------------------------------------------------------------------
   * Not found
   * -------------------------------------------------------------------------
   */

  if (!paper) {
    return (
      <div className="px-6 py-8 md:px-10">
        <div className="mx-auto max-w-4xl">
          <Link
            href="/papers"
            className="mb-5 inline-flex items-center gap-1.5 text-[12px] text-faint transition-colors hover:text-muted-foreground"
          >
            <ArrowLeft className="h-3 w-3" />
            All papers
          </Link>

          <p className="text-[13px] text-muted-foreground">
            Paper not found.
          </p>
        </div>
      </div>
    );
  }

  /*
   * -------------------------------------------------------------------------
   * Derived metadata
   * -------------------------------------------------------------------------
   */

  const publicationYear = paper.publication_date
    ? new Date(
        paper.publication_date,
      ).getFullYear()
    : null;

  const authors =
    paper.authors?.length > 0
      ? paper.authors
          .map((author) => author.name)
          .join(", ")
      : "Unknown authors";

  const keywords = paper.keywords ?? [];
  const categories = paper.categories ?? [];

  const externalIds = paper.external_ids ?? {};

  /*
   * -------------------------------------------------------------------------
   * Render
   * -------------------------------------------------------------------------
   */

  return (
    <div className="px-6 py-8 md:px-10">
      <div className="mx-auto max-w-4xl">
        {/* ---------------------------------------------------------------- */}
        {/* Back                                                              */}
        {/* ---------------------------------------------------------------- */}

        <Link
          href="/papers"
          className="mb-5 inline-flex items-center gap-1.5 text-[12px] text-faint transition-colors hover:text-muted-foreground"
        >
          <ArrowLeft className="h-3 w-3" />
          All papers
        </Link>

        {/* ---------------------------------------------------------------- */}
        {/* Header                                                            */}
        {/* ---------------------------------------------------------------- */}

        <div className="mb-6">
          <h1 className="mb-2 text-xl font-medium leading-tight tracking-tight text-foreground md:text-2xl">
            {paper.title}
          </h1>

          <p className="mb-3 text-[13px] text-muted-foreground">
            {authors}

            {paper.venue && (
              <>
                {" · "}
                {paper.venue}
              </>
            )}

            {publicationYear && (
              <>
                {" · "}
                {publicationYear}
              </>
            )}
          </p>

          <div className="flex flex-wrap items-center gap-4">
            {paper.doi && (
              <span className="font-mono-tech text-[11px] text-faint">
                DOI: {paper.doi}
              </span>
            )}

            <span className="font-mono-tech text-[11px] text-faint">
              Citations{" "}
              <span className="tabular-nums text-secondary-foreground">
                {paper.citation_count ?? 0}
              </span>
            </span>

            <span className="font-mono-tech text-[11px] text-faint">
              References{" "}
              <span className="tabular-nums text-secondary-foreground">
                {paper.reference_count ?? 0}
              </span>
            </span>

            {paper.source && (
              <span className="rounded border border-border px-1.5 py-0.5 font-mono-tech text-[10px] text-muted-foreground">
                {paper.source}
              </span>
            )}
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Actions                                                           */}
        {/* ---------------------------------------------------------------- */}

        <div className="mb-8 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setTab("content")}
            className="flex items-center gap-1.5 rounded-md border border-primary bg-primary/10 px-3 py-1.5 text-[12px] text-primary-soft transition-colors hover:bg-primary/20"
          >
            <Microscope className="h-3 w-3" />
            Analyze
          </button>

          <button
            type="button"
            onClick={() => {
              // Comparison workflow will be connected later.
            }}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
          >
            <GitCompare className="h-3 w-3" />
            Compare
          </button>

          <button
            type="button"
            onClick={() => {
              // Retrieval / research Q&A workflow will be connected later.
            }}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
          >
            <MessageSquareText className="h-3 w-3" />
            Ask
          </button>

          <button
            type="button"
            onClick={() => {
              // Project association workflow will be connected later.
            }}
            className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
          >
            <Plus className="h-3 w-3" />
            Add to project
          </button>

          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
            >
              <ExternalLink className="h-3 w-3" />
              Source
            </a>
          )}

          {paper.pdf_url && (
            <a
              href={paper.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
            >
              <FileText className="h-3 w-3" />
              PDF
            </a>
          )}
        </div>

        <Divider className="mb-6" />

        {/* ---------------------------------------------------------------- */}
        {/* Tabs                                                              */}
        {/* ---------------------------------------------------------------- */}

        <Tabs
          value={tab}
          onValueChange={setTab}
        >
          <TabsList className="h-auto gap-4 rounded-none border-b border-border bg-transparent p-0">
            {[
              "Overview",
              "Content",
              "Evidence",
              "Methods",
              "Results",
              "References",
            ].map((name) => {
              const value = name.toLowerCase();

              return (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="rounded-none border-b-2 border-transparent px-0 pb-2 pt-1.5 text-[13px] text-muted-foreground transition-colors data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none"
                >
                  {name}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* ============================================================ */}
          {/* Overview                                                       */}
          {/* ============================================================ */}

          <TabsContent
            value="overview"
            className="mt-6"
          >
            <div className="space-y-6">
              {/* Abstract */}

              <section>
                <SectionLabel>
                  Abstract
                </SectionLabel>

                <p className="text-[14px] leading-relaxed text-secondary-foreground">
                  {paper.abstract ||
                    "No abstract available."}
                </p>
              </section>

              <Divider />

              {/* Metrics */}

              <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
                <div>
                  <MetricLabel>
                    Publication
                  </MetricLabel>

                  <p className="mt-1 text-[13px] text-secondary-foreground">
                    {paper.publication_date
                      ? new Date(
                          paper.publication_date,
                        ).toLocaleDateString()
                      : "Unknown"}
                  </p>
                </div>

                <div>
                  <MetricLabel>
                    Venue
                  </MetricLabel>

                  <p className="mt-1 text-[13px] text-secondary-foreground">
                    {paper.venue || "Unknown"}
                  </p>
                </div>

                <div>
                  <MetricLabel>
                    Citations
                  </MetricLabel>

                  <p className="mt-1 text-[13px] text-secondary-foreground">
                    {paper.citation_count ?? 0}
                  </p>
                </div>

                <div>
                  <MetricLabel>
                    References
                  </MetricLabel>

                  <p className="mt-1 text-[13px] text-secondary-foreground">
                    {paper.reference_count ?? 0}
                  </p>
                </div>
              </div>

              <Divider />

              {/* Authors */}

              <section>
                <SectionLabel>
                  Authors
                </SectionLabel>

                <div className="mt-3 space-y-2">
                  {paper.authors.length > 0 ? (
                    paper.authors.map(
                      (author, index) => (
                        <div
                          key={
                            author.id ??
                            `${author.name}-${index}`
                          }
                          className="text-[13px] text-secondary-foreground"
                        >
                          {author.name}

                          {author.affiliation && (
                            <span className="text-faint">
                              {" · "}
                              {author.affiliation}
                            </span>
                          )}
                        </div>
                      ),
                    )
                  ) : (
                    <span className="text-[12px] text-faint">
                      No author information
                      available.
                    </span>
                  )}
                </div>
              </section>

              <Divider />

              {/* Keywords */}

              <section>
                <SectionLabel>
                  Keywords
                </SectionLabel>

                <div className="mt-3 flex flex-wrap gap-1.5">
                  {keywords.length > 0 ? (
                    keywords.map((keyword) => (
                      <span
                        key={keyword}
                        className="rounded border border-border px-1.5 py-0.5 font-mono-tech text-[10px] text-muted-foreground"
                      >
                        {keyword}
                      </span>
                    ))
                  ) : (
                    <span className="text-[12px] text-faint">
                      No keywords available.
                    </span>
                  )}
                </div>
              </section>

              {/* Categories */}

              {categories.length > 0 && (
                <>
                  <Divider />

                  <section>
                    <SectionLabel>
                      Categories
                    </SectionLabel>

                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {categories.map(
                        (category) => (
                          <span
                            key={category}
                            className="rounded border border-border px-1.5 py-0.5 font-mono-tech text-[10px] text-muted-foreground"
                          >
                            {category}
                          </span>
                        ),
                      )}
                    </div>
                  </section>
                </>
              )}

              {/* External IDs */}

              {Object.keys(externalIds).length >
                0 && (
                <>
                  <Divider />

                  <section>
                    <SectionLabel>
                      External IDs
                    </SectionLabel>

                    <div className="mt-3 space-y-2">
                      {Object.entries(
                        externalIds,
                      ).map(
                        ([provider, value]) => (
                          <div
                            key={provider}
                            className="flex items-center justify-between gap-4 text-[12px]"
                          >
                            <span className="text-faint">
                              {provider}
                            </span>

                            <span className="break-all text-right font-mono-tech text-secondary-foreground">
                              {String(value)}
                            </span>
                          </div>
                        ),
                      )}
                    </div>
                  </section>
                </>
              )}
            </div>
          </TabsContent>

          {/* ============================================================ */}
          {/* Content                                                         */}
          {/* ============================================================ */}

          <TabsContent
            value="content"
            className="mt-6"
          >
            <PaperContent
              paperId={paperId}
            />
          </TabsContent>

          {/* ============================================================ */}
          {/* Evidence                                                        */}
          {/* ============================================================ */}

          <TabsContent
            value="evidence"
            className="mt-6"
          >
            <PhasePlaceholder
              title="Evidence extraction"
              description="Evidence extraction will be implemented with the document intelligence and retrieval pipeline."
            />
          </TabsContent>

          {/* ============================================================ */}
          {/* Methods                                                         */}
          {/* ============================================================ */}

          <TabsContent
            value="methods"
            className="mt-6"
          >
            <PhasePlaceholder
              title="Method analysis"
              description="Method and dataset extraction will be implemented after document parsing and chunk indexing are available."
            />
          </TabsContent>

          {/* ============================================================ */}
          {/* Results                                                         */}
          {/* ============================================================ */}

          <TabsContent
            value="results"
            className="mt-6"
          >
            <PhasePlaceholder
              title="Results"
              description="Results extraction will be implemented through the document intelligence pipeline."
            />
          </TabsContent>

          {/* ============================================================ */}
          {/* References                                                      */}
          {/* ============================================================ */}

          <TabsContent
            value="references"
            className="mt-6"
          >
            <PhasePlaceholder
              title="References"
              description="Reference extraction and citation relationships will be connected to the paper knowledge graph."
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

/*
 * ===========================================================================
 * Placeholder
 * ===========================================================================
 */

function PhasePlaceholder({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <SectionLabel>
        {title}
      </SectionLabel>

      <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
        {description}
      </p>
    </div>
  );
}