'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  ArrowRight,
  AlertTriangle,
  Lightbulb,
  Network,
  Activity,
  Zap,
} from 'lucide-react';

import { projects } from './lib/mock-data';
import {
  SectionLabel,
  Divider,
  TrendArrow,
  StatusDot,
  MetricLabel,
  Sparkline,
  RadialScore,
  PulseWave,
  ResearchTrail,
} from './primitives';

import { cn } from './lib/utils';

const sparklineData = [8, 14, 12, 22, 28, 35, 42, 47];

export function Dashboard() {
 
  const project = projects[0];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 md:px-10 md:py-14">


      {/* Greeting */}
      <div className="mb-12 animate-fade-in-up">
        <div className="mb-3 flex items-center gap-3">
          <PulseWave bars={4} />

          <span className="font-mono-tech text-[10px] uppercase tracking-[0.15em] text-faint">
            Research Observatory
          </span>
        </div>

        <p className="mb-2 text-sm text-muted-foreground">
          Good morning.
        </p>

        <h1 className="mb-5 text-2xl font-medium tracking-tight text-foreground md:text-[28px]">
          What are you investigating?
        </h1>

        <Link
          href={`/projects/${project.id}`}
          className="group inline-flex max-w-2xl items-baseline gap-2 text-[15px] text-muted-foreground transition-colors hover:text-foreground"
        >
          <span className="border-b border-border pb-1 transition-colors group-hover:border-primary/40">
            {project.question}
          </span>

          <ArrowRight className="h-3.5 w-3.5 text-faint transition-all group-hover:translate-x-0.5 group-hover:text-primary" />
        </Link>

        {/* Research trail */}
        <div className="mt-6">
          <ResearchTrail
            steps={[
              { label: 'Question' },
              { label: 'Papers', active: true },
              { label: 'Evidence' },
              { label: 'Map' },
              { label: 'Gaps' },
              { label: 'Frontier' },
            ]}
          />
        </div>
      </div>

      <Divider className="mb-10" />

      {/* Active Research */}
      <section className="mb-12">
        <SectionLabel>Active Research</SectionLabel>

        <div className="space-y-1">
          {projects.map((p, i) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className={cn(
                'group block rounded-lg border border-transparent',
                'transition-all hover:border-border hover:bg-surface',
                'animate-fade-in-up stagger-' + (i + 1)
              )}
            >
              <div className="flex items-start justify-between px-4 py-4">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-2.5">
                    <StatusDot status={p.status} />

                    <h3 className="truncate text-[15px] font-medium text-foreground">
                      {p.title}
                    </h3>
                  </div>

                  <p className="mb-2 truncate text-[13px] text-muted-foreground">
                    {p.question}
                  </p>

                  <div className="flex items-center gap-4 font-mono-tech text-[11px] text-faint">
                    <span className="tabular-nums">
                      {p.paperCount} papers
                    </span>

                    <span className="text-border">·</span>

                    <span className="tabular-nums">
                      {p.evidenceCount} evidence units
                    </span>

                    <span className="text-border">·</span>

                    <span>
                      Last activity {p.updatedAt}
                    </span>
                  </div>
                </div>

                <div className="mt-1 flex shrink-0 items-center gap-3">
                  <Sparkline
                    data={sparklineData.slice(0, 5 + i)}
                    width={50}
                    height={18}
                  />

                  <ArrowRight className="h-4 w-4 text-faint transition-all group-hover:translate-x-0.5 group-hover:text-primary" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <Divider className="mb-10" />

      {/* Signals */}
      <section className="mb-12">
        <SectionLabel>Signals</SectionLabel>

        <div className="grid grid-cols-2 gap-x-8 gap-y-0 md:grid-cols-3">
          {project.signals.map((s, i) => (
            <div
              key={s.label}
              className={cn(
                'group -mx-2 flex items-center justify-between rounded px-2 py-2',
                'border-b border-border/50 transition-colors hover:bg-surface/30',
                'animate-fade-in-up stagger-' + ((i % 6) + 1)
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-[13px] text-secondary-foreground">
                  {s.label}
                </span>

                {s.direction === 'up' && s.change > 40 && (
                  <Zap className="h-3 w-3 text-success/60" />
                )}
              </div>

              <div className="flex items-center gap-2">
                <Sparkline
                  data={
                    s.direction === 'up'
                      ? [2, 5, 8, 12, 18, s.change]
                      : [18, 15, 12, 10, 8, s.change]
                  }
                  width={36}
                  height={14}
                  color={
                    s.direction === 'up'
                      ? 'hsl(var(--success))'
                      : 'hsl(var(--danger))'
                  }
                />

                <TrendArrow
                  direction={s.direction}
                  value={s.change}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <Divider className="mb-10" />

      {/* Recent Discoveries */}
      <section className="mb-12">
        <SectionLabel>Recent Discoveries</SectionLabel>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {project.recentDiscoveries.map((d, i) => {
            const Icon =
              d.type === 'connection'
                ? Network
                : d.type === 'contradiction'
                  ? AlertTriangle
                  : Lightbulb;

            const color =
              d.type === 'connection'
                ? 'text-primary-soft'
                : d.type === 'contradiction'
                  ? 'text-warning'
                  : 'text-success';

            const bgGlow =
              d.type === 'connection'
                ? 'hover:shadow-[0_0_20px_-5px_hsl(var(--primary)/0.2)]'
                : d.type === 'contradiction'
                  ? 'hover:shadow-[0_0_20px_-5px_hsl(var(--warning)/0.2)]'
                  : 'hover:shadow-[0_0_20px_-5px_hsl(var(--success)/0.2)]';

            return (
              <Link
                key={i}
                href={`/projects/${project.id}`}
                className={cn(
                  'group rounded-lg border border-border bg-surface p-4',
                  'transition-all hover:border-strong-border',
                  bgGlow,
                  'animate-fade-in-up stagger-' + (i + 1)
                )}
              >
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon
                      className={cn(
                        'h-3.5 w-3.5 transition-transform group-hover:scale-110',
                        color
                      )}
                    />

                    <span className="font-mono-tech text-[11px] uppercase tracking-wider text-faint">
                      {d.type === 'connection'
                        ? 'Connections'
                        : d.type === 'contradiction'
                          ? 'Contradictions'
                          : 'Opportunities'}
                    </span>
                  </div>

                  <RadialScore
                    value={d.count * 20}
                    size={36}
                    stroke={2}
                    color={
                      d.type === 'connection'
                        ? 'hsl(var(--primary))'
                        : d.type === 'contradiction'
                          ? 'hsl(var(--warning))'
                          : 'hsl(var(--success))'
                    }
                  />
                </div>

                <p className="mb-1 font-mono-tech text-2xl tabular-nums text-foreground">
                  {d.count}
                </p>

                <p className="text-[12px] leading-relaxed text-muted-foreground">
                  {d.description}
                </p>
              </Link>
            );
          })}
        </div>
      </section>

      <Divider className="mb-10" />

      {/* Frontier Preview */}
      <section className="mb-12">
        <SectionLabel>Frontier</SectionLabel>

        <div className="space-y-1">
          {project.frontier.map((f, i) => (
            <Link
              key={f.name}
              href="/frontier"
              className={cn(
                'group flex items-center justify-between rounded-lg',
                'border border-transparent px-4 py-3.5',
                'transition-all hover:border-border hover:bg-surface',
                'animate-fade-in-up stagger-' + (i + 1)
              )}
            >
              <div className="min-w-0 flex-1">
                <h4 className="mb-1 text-[14px] font-medium text-foreground">
                  {f.name}
                </h4>

                <div className="flex items-center gap-3 font-mono-tech text-[11px] text-faint">
                  <span>
                    Momentum{' '}
                    <span className="tabular-nums text-secondary-foreground">
                      {f.momentum}
                    </span>
                  </span>

                  <span>·</span>

                  <span>
                    Convergence{' '}
                    <span className="tabular-nums text-secondary-foreground">
                      {f.convergence}
                    </span>
                  </span>

                  <span>·</span>

                  <span
                    className={cn(
                      f.confidence === 'high'
                        ? 'text-success'
                        : f.confidence === 'medium'
                          ? 'text-warning'
                          : 'text-faint'
                    )}
                  >
                    {f.confidence} confidence
                  </span>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-3">
                <div className="hidden items-center gap-1.5 sm:flex">
                  {[1, 2, 3].map((bar) => (
                    <div
                      key={bar}
                      className={cn(
                        'w-0.5 rounded-full transition-all',
                        bar <=
                          (f.confidence === 'high'
                            ? 3
                            : f.confidence === 'medium'
                              ? 2
                              : 1)
                          ? f.confidence === 'high'
                            ? 'bg-success'
                            : 'bg-warning'
                          : 'bg-strong-border',
                        bar === 1
                          ? 'h-2'
                          : bar === 2
                            ? 'h-3'
                            : 'h-4'
                      )}
                    />
                  ))}
                </div>

                <ArrowRight className="h-3.5 w-3.5 text-faint transition-all group-hover:translate-x-0.5 group-hover:text-primary" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Footer */}
      <div className="flex items-center justify-between pt-8">
        <MetricLabel>
          Production RAG · Research Intelligence Workspace
        </MetricLabel>

        <div className="flex items-center gap-2">
          <Activity className="h-3 w-3 text-faint/40" />

          <span className="font-mono-tech text-[10px] text-faint/40">
            v0.1.0
          </span>
        </div>
      </div>
    </div>
  );
}