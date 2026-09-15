
"use client";

import {
  Search,
  X,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

interface GraphSearchProps {
  value?: string;
  onChange?: (value: string) => void;
  onClear?: () => void;

  /**
   * Kept for compatibility with callers
   * that use submit-based graph searching.
   */
  onSearch?: (query: string) => void;

  placeholder?: string;
}

export function GraphSearch({
  value,
  onChange,
  onClear,
  onSearch,
  placeholder = "Search graph...",
}: GraphSearchProps) {
  const isControlled =
    value !== undefined;

  const [internalQuery, setInternalQuery] =
    useState("");

  const query = isControlled
    ? value
    : internalQuery;

  useEffect(() => {
    if (isControlled) {
      return;
    }

    setInternalQuery(value ?? "");
  }, [value, isControlled]);

  const updateQuery = (
    nextValue: string,
  ) => {
    if (!isControlled) {
      setInternalQuery(nextValue);
    }

    onChange?.(nextValue);
  };

  const handleSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const normalizedQuery =
      query.trim();

    onSearch?.(normalizedQuery);
    onChange?.(normalizedQuery);
  };

  const clear = () => {
    if (!isControlled) {
      setInternalQuery("");
    }

    onChange?.("");
    onClear?.();
    onSearch?.("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center rounded-lg border border-white/10 bg-zinc-950"
    >
      <Search className="ml-3 h-4 w-4 shrink-0 text-zinc-600" />

      <input
        value={query}
        onChange={(event) =>
          updateQuery(
            event.target.value,
          )
        }
        placeholder={placeholder}
        className="h-10 min-w-0 flex-1 bg-transparent px-2 text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
      />

      {query && (
        <button
          type="button"
          onClick={clear}
          aria-label="Clear search"
          className="mr-1 flex h-8 w-8 items-center justify-center rounded-md text-zinc-500 hover:bg-white/5 hover:text-zinc-300"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </form>
  );
}

