"use client";

import {
  Maximize2,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";

import { useReactFlow } from "@xyflow/react";

export function GraphControls() {
  const {
    zoomIn,
    zoomOut,
    fitView,
    setViewport,
  } = useReactFlow();

  const resetView = () => {
    setViewport({
      x: 0,
      y: 0,
      zoom: 1,
    });
  };

  return (
    <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1 rounded-lg border border-white/10 bg-black/80 p-1 backdrop-blur">
      <button
        type="button"
        onClick={() => zoomOut()}
        aria-label="Zoom out"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <Minus className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={() => zoomIn()}
        aria-label="Zoom in"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <Plus className="h-4 w-4" />
      </button>

      <div className="mx-1 h-5 w-px bg-white/10" />

      <button
        type="button"
        onClick={() => fitView({ padding: 0.2 })}
        aria-label="Fit graph"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <Maximize2 className="h-4 w-4" />
      </button>

      <button
        type="button"
        onClick={resetView}
        aria-label="Reset view"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <RotateCcw className="h-4 w-4" />
      </button>
    </div>
  );
}