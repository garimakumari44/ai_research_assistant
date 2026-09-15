
"use client";

import {
  Maximize2,
  Minus,
  Plus,
  RotateCcw,
} from "lucide-react";

import { useReactFlow } from "@xyflow/react";

interface GraphControlsProps {
  depth?: number;
  onDepthChange?: (depth: number) => void;
}

export function GraphControls({
  depth,
  onDepthChange,
}: GraphControlsProps) {
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

  const decreaseDepth = () => {
    if (
      depth === undefined ||
      !onDepthChange
    ) {
      return;
    }

    onDepthChange(
      Math.max(1, depth - 1),
    );
  };

  const increaseDepth = () => {
    if (
      depth === undefined ||
      !onDepthChange
    ) {
      return;
    }

    onDepthChange(
      Math.min(5, depth + 1),
    );
  };

  return (
    <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1 rounded-lg border border-white/10 bg-black/80 p-1 backdrop-blur">
      {/* Zoom Out */}
      <button
        type="button"
        onClick={() => zoomOut()}
        aria-label="Zoom out"
        title="Zoom out"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <Minus className="h-4 w-4" />
      </button>

      {/* Zoom In */}
      <button
        type="button"
        onClick={() => zoomIn()}
        aria-label="Zoom in"
        title="Zoom in"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <Plus className="h-4 w-4" />
      </button>

      <div className="mx-1 h-5 w-px bg-white/10" />

      {/* Fit Graph */}
      <button
        type="button"
        onClick={() =>
          fitView({
            padding: 0.2,
          })
        }
        aria-label="Fit graph"
        title="Fit graph"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <Maximize2 className="h-4 w-4" />
      </button>

      {/* Reset View */}
      <button
        type="button"
        onClick={resetView}
        aria-label="Reset view"
        title="Reset view"
        className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white"
      >
        <RotateCcw className="h-4 w-4" />
      </button>

      {/* Graph Depth Controls */}
      {depth !== undefined &&
        onDepthChange && (
          <>
            <div className="mx-1 h-5 w-px bg-white/10" />

            {/* Decrease Depth */}
            <button
              type="button"
              onClick={decreaseDepth}
              disabled={depth <= 1}
              aria-label="Decrease graph depth"
              title="Decrease graph depth"
              className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
            >
              <Minus className="h-4 w-4" />
            </button>

            {/* Current Depth */}
            <div
              className="flex h-8 min-w-8 items-center justify-center px-1 text-xs font-medium text-zinc-300"
              aria-label={`Graph depth ${depth}`}
              title={`Graph depth: ${depth}`}
            >
              {depth}
            </div>

            {/* Increase Depth */}
            <button
              type="button"
              onClick={increaseDepth}
              disabled={depth >= 5}
              aria-label="Increase graph depth"
              title="Increase graph depth"
              className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
            >
              <Plus className="h-4 w-4" />
            </button>
          </>
        )}
    </div>
  );
}

