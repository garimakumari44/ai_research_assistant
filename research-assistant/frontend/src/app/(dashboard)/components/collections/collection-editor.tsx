"use client";

import {
  Folder,
  Save,
  X,
} from "lucide-react";

import { useEffect, useState } from "react";

import type { Collection } from "./collection-card";

interface CollectionEditorProps {
  collection?: Collection | null;
  isSaving?: boolean;
  onSave: (
    values: CollectionFormValues,
  ) => void | Promise<void>;
  onCancel?: () => void;
}

export interface CollectionFormValues {
  name: string;
  description: string;
  color: string;
}

const COLORS = [
  "#3b82f6",
  "#06b6d4",
  "#8b5cf6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
];

export function CollectionEditor({
  collection,
  isSaving = false,
  onSave,
  onCancel,
}: CollectionEditorProps) {
  const [name, setName] = useState(collection?.name ?? "");
  const [description, setDescription] = useState(
    collection?.description ?? "",
  );
  const [color, setColor] = useState(
    collection?.color ?? COLORS[0],
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(collection?.name ?? "");
    setDescription(collection?.description ?? "");
    setColor(collection?.color ?? COLORS[0]);
  }, [collection]);

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const trimmedName = name.trim();

    if (!trimmedName) {
      setError("Collection name is required.");
      return;
    }

    setError(null);

    await onSave({
      name: trimmedName,
      description: description.trim(),
      color,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-white/10 bg-zinc-950"
    >
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg"
            style={{
              backgroundColor: `${color}15`,
            }}
          >
            <Folder
              className="h-4 w-4"
              style={{
                color,
              }}
            />
          </div>

          <div>
            <h2 className="text-sm font-medium text-zinc-100">
              {collection
                ? "Edit collection"
                : "Create collection"}
            </h2>

            <p className="mt-0.5 text-[10px] text-zinc-600">
              Configure your research collection.
            </p>
          </div>
        </div>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md p-1.5 text-zinc-600 hover:bg-white/5 hover:text-zinc-300"
            aria-label="Cancel"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="space-y-5 p-5">
        <div>
          <label
            htmlFor="collection-name"
            className="mb-1.5 block text-xs font-medium text-zinc-400"
          >
            Name
          </label>

          <input
            id="collection-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Retrieval-Augmented Generation"
            maxLength={120}
            autoFocus
            className="h-10 w-full rounded-md border border-white/10 bg-black px-3 text-xs text-zinc-200 outline-none placeholder:text-zinc-700 focus:border-blue-500/50"
          />

          {error && (
            <p className="mt-1.5 text-[11px] text-red-400">
              {error}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="collection-description"
            className="mb-1.5 block text-xs font-medium text-zinc-400"
          >
            Description
          </label>

          <textarea
            id="collection-description"
            value={description}
            onChange={(event) =>
              setDescription(event.target.value)
            }
            placeholder="Describe what this collection contains..."
            rows={4}
            maxLength={500}
            className="w-full resize-none rounded-md border border-white/10 bg-black px-3 py-2.5 text-xs leading-relaxed text-zinc-200 outline-none placeholder:text-zinc-700 focus:border-blue-500/50"
          />

          <div className="mt-1 text-right text-[10px] text-zinc-700">
            {description.length}/500
          </div>
        </div>

        <div>
          <div className="mb-2 text-xs font-medium text-zinc-400">
            Collection color
          </div>

          <div className="flex items-center gap-2">
            {COLORS.map((option) => {
              const selected = color === option;

              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => setColor(option)}
                  aria-label={`Select color ${option}`}
                  className={[
                    "flex h-8 w-8 items-center justify-center rounded-full border transition",
                    selected
                      ? "border-white/50"
                      : "border-transparent",
                  ].join(" ")}
                >
                  <span
                    className="h-5 w-5 rounded-full"
                    style={{
                      backgroundColor: option,
                    }}
                  />
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 border-t border-white/10 px-5 py-3">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSaving}
            className="h-9 rounded-md px-3 text-xs text-zinc-500 transition hover:bg-white/5 hover:text-zinc-300 disabled:opacity-50"
          >
            Cancel
          </button>
        )}

        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex h-9 items-center gap-2 rounded-md bg-blue-600 px-3 text-xs font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Save className="h-3.5 w-3.5" />

          {isSaving
            ? "Saving..."
            : collection
              ? "Save changes"
              : "Create collection"}
        </button>
      </div>
    </form>
  );
}