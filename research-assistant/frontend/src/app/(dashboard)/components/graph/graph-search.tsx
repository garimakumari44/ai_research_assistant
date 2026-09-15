"use client";

import { Search, X } from "lucide-react";

import { useState } from "react";

interface GraphSearchProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

export function GraphSearch({
  onSearch,
  placeholder = "Search graph...",
}: GraphSearchProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSearch(query.trim());
  };

  const clear = () => {
    setQuery("");
    onSearch("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center rounded-lg border border-white/10 bg-zinc-950"
    >
      <Search className="ml-3 h-4 w-4 shrink-0 text-zinc-600" />

      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
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