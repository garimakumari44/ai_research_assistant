"use client";

import {
  FormEvent,
  KeyboardEvent,
  useState,
} from "react";

import {
  Brain,
  Send,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";

interface ResearchInputProps {
  loading?: boolean;

  onSubmit: (
    query: string,
  ) => void;

  defaultQuery?: string;
}

export function ResearchInput({
  loading = false,
  onSubmit,
  defaultQuery = "",
}: ResearchInputProps) {
  const [query, setQuery] =
    useState(defaultQuery);

  function submit(
    event?: FormEvent,
  ) {
    event?.preventDefault();

    const value = query.trim();

    if (!value || loading) {
      return;
    }

    onSubmit(value);
    setQuery("");
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      submit();
    }
  }

  return (
    <div className="border-t bg-background p-4">
      <form
        onSubmit={submit}
        className="mx-auto max-w-5xl"
      >
        <div className="rounded-2xl border bg-background shadow-sm">
          <textarea
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            onKeyDown={handleKeyDown}
            disabled={loading}
            rows={4}
            placeholder="Ask a research question..."
            className="w-full resize-none rounded-2xl bg-transparent px-4 py-4 pr-14 text-sm leading-6 outline-none"
          />

          <div className="flex items-center justify-between border-t px-3 py-2">
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Brain className="h-3.5 w-3.5" />
                Research Engine
              </span>

              <span className="flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                Adaptive RAG
              </span>

              <span className="hidden items-center gap-1.5 md:flex">
                <SlidersHorizontal className="h-3.5 w-3.5" />
                Evidence verification
              </span>
            </div>

            <button
              type="submit"
              disabled={
                loading ||
                !query.trim()
              }
              className="flex h-9 items-center gap-2 rounded-xl bg-foreground px-4 text-xs font-medium text-background transition hover:opacity-90 disabled:opacity-30"
            >
              {loading ? (
                <span>Researching...</span>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  Research
                </>
              )}
            </button>
          </div>
        </div>

        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          Enter to research · Shift + Enter for a new line
        </p>
      </form>
    </div>
  );
}