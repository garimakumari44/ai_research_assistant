"use client";

import {
  Bug,
  Check,
  MessageSquare,
  Minus,
  Send,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";

import { useState } from "react";

export type FeedbackRating =
  | "positive"
  | "negative"
  | "neutral";

export type FeedbackCategory =
  | "accuracy"
  | "relevance"
  | "citations"
  | "completeness"
  | "reasoning"
  | "other";

interface FeedbackPanelProps {
  initialRating?: FeedbackRating;
  initialCategory?: FeedbackCategory;
  initialComment?: string;
  submitting?: boolean;
  submitted?: boolean;
  onSubmit?: (feedback: {
    rating: FeedbackRating;
    category: FeedbackCategory;
    comment: string;
  }) => void;
}

const categories: Array<{
  value: FeedbackCategory;
  label: string;
}> = [
  {
    value: "accuracy",
    label: "Accuracy",
  },
  {
    value: "relevance",
    label: "Relevance",
  },
  {
    value: "citations",
    label: "Citations",
  },
  {
    value: "completeness",
    label: "Completeness",
  },
  {
    value: "reasoning",
    label: "Reasoning",
  },
  {
    value: "other",
    label: "Other",
  },
];

export function FeedbackPanel({
  initialRating,
  initialCategory = "accuracy",
  initialComment = "",
  submitting = false,
  submitted = false,
  onSubmit,
}: FeedbackPanelProps) {
  const [rating, setRating] = useState<
    FeedbackRating | undefined
  >(initialRating);

  const [category, setCategory] =
    useState<FeedbackCategory>(initialCategory);

  const [comment, setComment] = useState(initialComment);

  const submit = () => {
    if (!rating) return;

    onSubmit?.({
      rating,
      category,
      comment: comment.trim(),
    });
  };

  if (submitted) {
    return (
      <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/10">
            <Check className="h-4 w-4 text-emerald-400" />
          </div>

          <div>
            <h2 className="text-sm font-medium text-emerald-300">
              Feedback recorded
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Your feedback will be used by the evaluation and
              improvement pipeline.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950">
      <header className="border-b border-zinc-800 px-5 py-4">
        <div className="flex items-center gap-3">
          <MessageSquare className="h-4 w-4 text-zinc-500" />

          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Human Feedback
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Help improve future research executions.
            </p>
          </div>
        </div>
      </header>

      <div className="p-5">
        <div>
          <label className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
            Overall result
          </label>

          <div className="mt-2 grid grid-cols-3 gap-2">
            <RatingButton
              active={rating === "positive"}
              onClick={() => setRating("positive")}
              icon={ThumbsUp}
              label="Good"
              activeClass="border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            />

            <RatingButton
              active={rating === "neutral"}
              onClick={() => setRating("neutral")}
              icon={Minus}
              label="Mixed"
              activeClass="border-amber-500/30 bg-amber-500/10 text-amber-400"
            />

            <RatingButton
              active={rating === "negative"}
              onClick={() => setRating("negative")}
              icon={ThumbsDown}
              label="Poor"
              activeClass="border-red-500/30 bg-red-500/10 text-red-400"
            />
          </div>
        </div>

        <div className="mt-5">
          <label
            htmlFor="feedback-category"
            className="text-[10px] font-medium uppercase tracking-wider text-zinc-600"
          >
            Problem category
          </label>

          <select
            id="feedback-category"
            value={category}
            onChange={(event) =>
              setCategory(
                event.target.value as FeedbackCategory,
              )
            }
            className="mt-2 w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-zinc-700"
          >
            {categories.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-5">
          <label
            htmlFor="feedback-comment"
            className="text-[10px] font-medium uppercase tracking-wider text-zinc-600"
          >
            Feedback
          </label>

          <textarea
            id="feedback-comment"
            value={comment}
            onChange={(event) =>
              setComment(event.target.value)
            }
            rows={5}
            placeholder="What should the system do differently?"
            className="mt-2 w-full resize-y rounded-md border border-zinc-800 bg-zinc-950 p-3 text-xs leading-5 text-zinc-300 outline-none placeholder:text-zinc-700 focus:border-zinc-700"
          />
        </div>

        {rating === "negative" && (
          <div className="mt-3 flex gap-2 rounded-md border border-red-500/10 bg-red-500/5 p-3">
            <Bug className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-400" />

            <p className="text-[11px] leading-5 text-zinc-500">
              Negative feedback is especially useful for identifying
              retrieval, reasoning, and generation failures.
            </p>
          </div>
        )}

        <button
          type="button"
          disabled={!rating || submitting}
          onClick={submit}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-3 py-2.5 text-xs font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? (
            <>
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Recording...
            </>
          ) : (
            <>
              <Send className="h-3.5 w-3.5" />
              Submit feedback
            </>
          )}
        </button>
      </div>
    </section>
  );
}

function RatingButton({
  active,
  onClick,
  icon: Icon,
  label,
  activeClass,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof ThumbsUp;
  label: string;
  activeClass: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-center gap-2 rounded-md border px-3 py-3 text-xs transition ${
        active
          ? activeClass
          : "border-zinc-800 text-zinc-600 hover:bg-zinc-900 hover:text-zinc-400"
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}