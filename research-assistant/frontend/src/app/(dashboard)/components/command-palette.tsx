'use client';

import { Command } from 'cmdk';
import { useRouter } from 'next/navigation';
import {
  Search,
  FileText,
  GitCompare,
  Microscope,
  Network,
  AlertTriangle,
  Lightbulb,
  Telescope,
  FlaskConical,
  Map,
  FileBarChart,
  CornerDownLeft,
  Database,
} from 'lucide-react';

const commands = [
  {
    label: 'Search papers',
    hint: 'Find literature by title, author, method',
    icon: Search,
    action: '/papers',
  },
  {
    label: 'Explore research',
    hint: 'Search and retrieve knowledge from your papers',
    icon: Telescope,
    action: '/explore',
  },
  {
    label: 'Open project',
    hint: 'Future of Agentic RAG',
    icon: Microscope,
    action: '/projects/agentic-rag',
  },
  {
    label: 'Compare papers',
    hint: 'Side-by-side analysis',
    icon: GitCompare,
    action: '/papers',
  },
  {
    label: 'Analyze paper',
    hint: 'Deep document intelligence',
    icon: FileText,
    action: '/papers/p-001',
  },
  {
    label: 'Find evidence',
    hint: 'Trace claims to sources',
    icon: Database,
    action: '/explore',
  },
  {
    label: 'Explore citations',
    hint: 'Citation graph and relationships',
    icon: Network,
    action: '/graph',
  },
  {
    label: 'Find contradictions',
    hint: 'Disagreements in the literature',
    icon: AlertTriangle,
    action: '/explore',
  },
  {
    label: 'Find research gaps',
    hint: 'Underexplored intersections',
    icon: Map,
    action: '/explore',
  },
  {
    label: 'Explore frontier',
    hint: 'Emerging research directions',
    icon: Telescope,
    action: '/frontier',
  },
  {
    label: 'Generate hypothesis',
    hint: 'Derive research ideas',
    icon: Lightbulb,
    action: '/explore',
  },
  {
    label: 'Generate roadmap',
    hint: 'Turn research insight into a plan',
    icon: FlaskConical,
    action: '/explore',
  },
  {
    label: 'Generate report',
    hint: 'Academic document synthesis',
    icon: FileBarChart,
    action: '/reports',
  },
];

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const router = useRouter();

  if (!open) return null;

  const handleSelect = (action: string) => {
    router.push(action);
    onOpenChange(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[15vh]">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-md"
        onClick={() => onOpenChange(false)}
        aria-hidden="true"
      />

      {/* Command dialog */}
      <div className="relative w-full max-w-xl overflow-hidden rounded-lg border border-strong-border bg-popover shadow-2xl animate-fade-in-up">
        {/* Top accent line */}
        <div className="h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />

        <Command
          className="flex flex-col"
          loop
          shouldFilter
        >
          {/* Search input */}
          <div className="flex items-center gap-2.5 border-b border-border px-4 py-3">
            <Search className="h-4 w-4 shrink-0 text-faint" />

            <Command.Input
              autoFocus
              placeholder="Search papers, topics, authors, questions..."
              className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-faint"
            />

            <kbd
              className="cursor-pointer rounded border border-border bg-background px-1.5 py-0.5 font-mono-tech text-[10px] text-faint transition-colors hover:text-muted-foreground"
              onClick={() => onOpenChange(false)}
            >
              ESC
            </kbd>
          </div>

          {/* Commands */}
          <Command.List className="max-h-[400px] overflow-y-auto p-2">
            <Command.Empty className="py-8 text-center text-sm text-faint">
              No results found.
            </Command.Empty>

            <Command.Group
              heading="Commands"
              className="text-faint [&_[cmdk-group-heading]]:px-2.5 [&_[cmdk-group-heading]]:pb-2 [&_[cmdk-group-heading]]:pt-1 [&_[cmdk-group-heading]]:font-mono-tech [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
            >
              {commands.map((cmd) => {
                const Icon = cmd.icon;

                return (
                  <Command.Item
                    key={cmd.label}
                    value={`${cmd.label} ${cmd.hint}`}
                    onSelect={() => handleSelect(cmd.action)}
                    className="group flex cursor-pointer items-center gap-3 rounded-md px-2.5 py-2 text-sm text-muted-foreground outline-none transition-colors data-[selected=true]:bg-elevated data-[selected=true]:text-foreground"
                  >
                    {/* Icon */}
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-transparent transition-colors group-data-[selected=true]:border-border group-data-[selected=true]:bg-background">
                      <Icon className="h-3.5 w-3.5 text-faint transition-colors group-data-[selected=true]:text-primary" />
                    </div>

                    {/* Command information */}
                    <div className="flex min-w-0 flex-1 flex-col">
                      <span className="truncate text-foreground">
                        {cmd.label}
                      </span>

                      <span className="truncate text-[11px] text-faint">
                        {cmd.hint}
                      </span>
                    </div>

                    {/* Enter indicator */}
                    <CornerDownLeft className="h-3 w-3 shrink-0 text-faint opacity-0 transition-opacity group-data-[selected=true]:opacity-100" />
                  </Command.Item>
                );
              })}
            </Command.Group>
          </Command.List>
        </Command>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border px-4 py-2">
          <div className="flex items-center gap-3">
            <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
              {commands.length} commands
            </span>
          </div>

          <div className="flex items-center gap-2 font-mono-tech text-[10px] text-faint">
            <kbd className="rounded border border-border bg-background px-1 py-0.5">
              ↑↓
            </kbd>
            <span>navigate</span>

            <kbd className="rounded border border-border bg-background px-1 py-0.5">
              ↵
            </kbd>
            <span>select</span>

            <kbd className="rounded border border-border bg-background px-1 py-0.5">
              ESC
            </kbd>
            <span>close</span>
          </div>
        </div>
      </div>
    </div>
  );
}