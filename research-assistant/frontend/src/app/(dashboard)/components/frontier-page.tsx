'use client';

import { useState } from 'react';
import { projects, opportunities } from './lib/mock-data';
import { SectionLabel, Divider, MetricLabel, ScoreBar, ConfidenceMeter, TrustTag } from '../components/primitives';
import { cn } from './lib/utils';

export function FrontierPage() {
  const allFrontier = projects.flatMap((p) => p.frontier.map((f) => ({ ...f, project: p.title })));
  const [active, setActive] = useState(0);
  const f = allFrontier[active];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 md:px-10">
      <h1 className="text-xl font-medium tracking-tight text-foreground mb-2">Research Frontier</h1>
      <p className="text-[13px] text-muted-foreground mb-8">A scientific horizon map of emerging directions.</p>

      {/* Horizon timeline */}
      <div className="rounded-lg border border-border bg-surface p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">Past</span>
          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-primary-soft">Current</span>
          <span className="font-mono-tech text-[10px] uppercase tracking-wider text-warning">Future</span>
        </div>
        <div className="relative h-px bg-border mb-6">
          <div className="absolute left-0 top-0 h-px w-1/3 bg-muted-foreground" />
          <div className="absolute left-1/3 top-0 h-px w-1/3 bg-primary" />
          <div className="absolute left-2/3 top-0 h-px w-1/3 border-t border-dashed border-warning" />
        </div>
        <div className="space-y-2">
          {[
            { label: 'RAG', level: 'past' },
            { label: 'Adaptive Retrieval', level: 'current' },
            { label: 'Agentic Retrieval', level: 'current' },
            { label: 'Self-Evolving Retrieval', level: 'future' },
            { label: 'Persistent Multimodal Memory', level: 'future' },
            { label: 'Autonomous Evidence Verification', level: 'future' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-3">
              <div className={cn(
                'h-1.5 w-1.5 rounded-full',
                item.level === 'past' ? 'bg-faint' : item.level === 'current' ? 'bg-primary' : 'bg-warning'
              )} />
              <span className={cn(
                'text-[12px]',
                item.level === 'past' ? 'text-faint' : item.level === 'current' ? 'text-foreground' : 'text-warning'
              )}>
                {item.label}
              </span>
              {item.level === 'future' && (
                <span className="font-mono-tech text-[10px] text-warning">┄┄┄→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <Divider className="mb-8" />

      {/* Frontier topics */}
      <div className="flex flex-col gap-1 mb-6">
        {allFrontier.map((ft, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={cn(
              'text-left rounded-md border px-4 py-3 transition-colors',
              active === i
                ? 'border-primary/40 bg-primary/5'
                : 'border-border bg-surface hover:border-strong-border'
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={cn('text-[13px] font-medium', active === i ? 'text-foreground' : 'text-muted-foreground')}>
                  {ft.name}
                </span>
                <span className="font-mono-tech text-[10px] text-faint">{ft.project}</span>
              </div>
              <span className="font-mono-tech text-[11px] text-faint">
                Momentum <span className="text-secondary-foreground tabular-nums">{ft.momentum}</span>
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Detail */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-[16px] font-medium text-foreground">{f.name}</h3>
          <div className="flex items-center gap-3">
            <TrustTag category="forecast" />
            <ConfidenceMeter value={f.confidence} label="Confidence" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-6">
          <div>
            <MetricLabel>Observed momentum</MetricLabel>
            <ScoreBar value={f.momentum} className="mt-2" />
            <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-1 block">{f.momentum}</span>
          </div>
          <div>
            <MetricLabel>Cross-topic convergence</MetricLabel>
            <ScoreBar value={f.convergence} color="bg-primary-soft" className="mt-2" />
            <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-1 block">{f.convergence}</span>
          </div>
          <div>
            <MetricLabel>Novelty</MetricLabel>
            <ScoreBar value={f.novelty} color="bg-success" className="mt-2" />
            <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-1 block">{f.novelty}</span>
          </div>
        </div>

        <Divider className="mb-6" />

        <SectionLabel>Why?</SectionLabel>
        <div className="space-y-1 mb-6">
          {f.reasons.map((r, i) => (
            <div key={i} className="flex items-center gap-3 py-2 border-b border-border/50">
              <span className="font-mono-tech text-[11px] text-faint tabular-nums">{String(i + 1).padStart(2, '0')}</span>
              <span className="text-[13px] text-secondary-foreground">{r}</span>
            </div>
          ))}
        </div>

        <Divider className="mb-6" />

        <div className="grid grid-cols-3 gap-4">
          <div>
            <MetricLabel>Supporting evidence</MetricLabel>
            <p className="font-mono-tech text-lg text-success tabular-nums mt-1">{f.supportingEvidence}</p>
          </div>
          <div>
            <MetricLabel>Counter-signals</MetricLabel>
            <p className="font-mono-tech text-lg text-warning tabular-nums mt-1">{f.counterSignals}</p>
          </div>
          <div>
            <MetricLabel>Relevant papers</MetricLabel>
            <p className="font-mono-tech text-lg text-secondary-foreground tabular-nums mt-1">{f.relevantPapers}</p>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-[12px] text-faint italic">
            Forecast: <span className="text-warning capitalize">{f.forecast}</span> · This is a model-generated projection. Treat as a directional signal, not a certainty.
          </p>
        </div>
      </div>

      <Divider className="my-8" />

      {/* Opportunities */}
      <section>
        <SectionLabel>Research Opportunities</SectionLabel>
        <div className="space-y-1">
          {opportunities.map((o) => (
            <div key={o.id} className="flex items-start gap-4 py-4 border-b border-border/50">
              <div className="flex-1 min-w-0">
                <h4 className="text-[14px] font-medium text-foreground mb-1">{o.title}</h4>
                <p className="text-[12px] text-muted-foreground mb-3">{o.subtitle}</p>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <MetricLabel>Novelty</MetricLabel>
                    <ScoreBar value={o.novelty} className="mt-1" />
                    <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-0.5 block">{o.novelty}</span>
                  </div>
                  <div>
                    <MetricLabel>Momentum</MetricLabel>
                    <ScoreBar value={o.momentum} color="bg-primary-soft" className="mt-1" />
                    <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-0.5 block">{o.momentum}</span>
                  </div>
                  <div>
                    <MetricLabel>Competition</MetricLabel>
                    <ScoreBar value={o.competition} color="bg-warning" className="mt-1" />
                    <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-0.5 block">{o.competition}</span>
                  </div>
                  <div>
                    <MetricLabel>Difficulty</MetricLabel>
                    <ScoreBar value={o.difficulty} color="bg-danger" className="mt-1" />
                    <span className="font-mono-tech text-[11px] text-secondary-foreground tabular-nums mt-0.5 block">{o.difficulty}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
