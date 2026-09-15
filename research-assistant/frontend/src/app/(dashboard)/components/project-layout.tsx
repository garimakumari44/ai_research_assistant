'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';

import { cn } from './lib/utils';
import { StatusDot, MetricLabel, PulseWave } from './primitives';

import { useProjectOverview } from '@/projects/hooks/use-project-overview';

const projectNav = [
  { label: 'Overview', href: '' },
  { label: 'Papers', href: '/papers' },
  { label: 'Evidence', href: '/evidence' },
  { label: 'Map', href: '/map' },
  { label: 'Trends', href: '/trends' },
  { label: 'Contradictions', href: '/contradictions' },
  { label: 'Gaps', href: '/gaps' },
  { label: 'Frontier', href: '/frontier' },
  { label: 'Hypotheses', href: '/hypotheses' },
  { label: 'Roadmap', href: '/roadmap' },
  { label: 'Reports', href: '/reports' },
];

export function ProjectLayout({
  projectId,
  children,
}: {
  projectId: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const {
    data,
    isLoading,
    isError,
  } = useProjectOverview(projectId);

  const basePath = `/projects/${projectId}`;

  if (isLoading) {
    return (
      <div className="flex flex-col">
        <div className="border-b border-border px-6 md:px-10 pt-8 pb-6">
          <div className="text-sm text-muted-foreground">
            Loading project...
          </div>
        </div>
      </div>
    );
  }

  if (isError || !data?.project) {
    return (
      <div className="flex flex-col">
        <div className="border-b border-border px-6 md:px-10 pt-8 pb-6">
          <div className="text-sm text-destructive">
            Unable to load project.
          </div>
        </div>

        <div className="px-6 md:px-10 py-8">
          {children}
        </div>
      </div>
    );
  }

  const project = data.project;

  return (
    <div className="flex flex-col">
      {/* Project header */}
      <div className="border-b border-border px-6 md:px-10 pt-8 pb-6 relative">
        {/* Subtle dot grid background */}
        <div className="absolute inset-0 dot-bg opacity-30 pointer-events-none" />

        <div className="relative">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-[12px] text-faint hover:text-muted-foreground transition-colors mb-5"
          >
            <ArrowLeft className="h-3 w-3" />
            All research
          </Link>

          <div className="flex items-start justify-between gap-6 flex-wrap">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2.5 mb-2">
                <StatusDot status={project.status} />

                <h1 className="text-xl md:text-2xl font-medium tracking-tight text-foreground">
                  {project.title}
                </h1>
              </div>

              <p className="text-[14px] text-muted-foreground max-w-2xl leading-relaxed mb-4">
                {project.question}
              </p>

              <div className="flex items-center gap-4 font-mono-tech text-[11px] text-faint">
                <span className="tabular-nums">
                  {project.paperCount} papers
                </span>

                <span className="text-border">·</span>

                <span className="tabular-nums">
                  {project.evidenceCount} evidence units
                </span>

                <span className="text-border">·</span>

                <span className="tabular-nums">
                  {project.topicCount} topics
                </span>

                <span className="text-border">·</span>

                <span>
                  Updated {project.updatedAt}
                </span>
              </div>
            </div>

            <div className="hidden md:flex items-center gap-3">
              <PulseWave bars={6} />
              <MetricLabel>live</MetricLabel>
            </div>
          </div>

          {/* Horizontal contextual nav */}
          <nav className="mt-6 -mb-px flex items-center gap-1 overflow-x-auto relative">
            {projectNav.map((item) => {
              const href = basePath + item.href;

              const active =
                item.href === ''
                  ? pathname === basePath
                  : pathname === href ||
                    pathname.startsWith(href + '/');

              return (
                <Link
                  key={item.label}
                  href={href}
                  className={cn(
                    'shrink-0 border-b-2 px-3 py-2.5 text-[13px] transition-all relative',
                    active
                      ? 'border-primary text-foreground'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  )}
                >
                  {item.label}

                  {active && (
                    <span className="absolute -bottom-px left-0 right-0 h-px bg-primary/20" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Project content */}
      <div className="px-6 md:px-10 py-8">
        {children}
      </div>
    </div>
  );
}