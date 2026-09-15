'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Microscope,
  FileText,
  Compass,
  Network,
  Telescope,
  FolderOpen,
  MessageSquareText,
  FileBarChart,
  Command as CommandIcon,
  ChevronRight,
  LogOut,
} from 'lucide-react';

import { cn } from './lib/utils';
import { CommandPalette } from './command-palette';
import { useAuth } from '@/providers/AuthProvider';

const navItems = [
  { label: 'Research', href: '/', icon: Microscope },
  { label: 'Papers', href: '/papers', icon: FileText },
  { label: 'Explore', href: '/explore', icon: Compass },
  { label: 'Graph', href: '/graph', icon: Network },
  { label: 'Frontier', href: '/frontier', icon: Telescope },
  { label: 'Collections', href: '/collections', icon: FolderOpen },
  { label: 'Assistant', href: '/assistant', icon: MessageSquareText },
  { label: 'Reports', href: '/reports', icon: FileBarChart },
];

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { signOut } = useAuth();

  const [commandOpen, setCommandOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandOpen((value) => !value);
      }
    };

    window.addEventListener('keydown', handler);

    return () => {
      window.removeEventListener('keydown', handler);
    };
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="hidden md:flex w-[224px] shrink-0 flex-col border-r border-border bg-surface">
        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;

            const active =
              pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'group relative flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] transition-all',
                  active
                    ? 'bg-elevated text-foreground border border-border glow-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-elevated/50 border border-transparent'
                )}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-0.5 rounded-full bg-primary" />
                )}

                <Icon
                  className={cn(
                    'h-3.5 w-3.5 transition-colors',
                    active
                      ? 'text-primary'
                      : 'text-faint group-hover:text-muted-foreground'
                  )}
                />

                <span>{item.label}</span>

                {active && (
                  <ChevronRight className="h-3 w-3 ml-auto text-faint" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Sign Out */}
        <div className="border-t border-border p-3">
          <button
            type="button"
            onClick={signOut}
            className="group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] text-muted-foreground transition-all hover:bg-elevated hover:text-foreground"
          >
            <LogOut className="h-3.5 w-3.5 text-faint transition-colors group-hover:text-primary" />

            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-4 md:px-6">
          <button
            type="button"
            onClick={() => setCommandOpen(true)}
            className="group flex h-9 flex-1 max-w-2xl items-center gap-2.5 rounded-md border border-border bg-elevated px-3 text-left transition-all hover:border-strong-border hover:bg-hover"
          >
            <CommandIcon className="h-3.5 w-3.5 text-faint group-hover:text-primary transition-colors" />

            <span className="text-[13px] text-faint group-hover:text-muted-foreground transition-colors">
              Search papers, topics, authors, questions...
            </span>

            <kbd className="ml-auto hidden sm:flex items-center gap-0.5 rounded border border-border bg-background px-1.5 py-0.5 font-mono-tech text-[10px] text-faint">
              ⌘K
            </kbd>
          </button>

          {/* Mobile logo */}
          <Link
            href="/"
            className="md:hidden flex h-7 w-7 items-center justify-center rounded-md border border-strong-border bg-elevated"
          >
            <div className="h-3 w-3 rounded-sm bg-primary" />
          </Link>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
      />
    </div>
  );
}