'use client';

import { useState } from 'react';

import { AuthPanel } from '@/components/AuthPanel';
import {
  LandingPanel,
  Logo,
  Constellation,
} from '@/components/LandingPanel';

import { useAuth } from '@/providers/AuthProvider';
import { Dashboard } from '@/app/(dashboard)/components/dashboard-two';
import { AppShell } from '@/app/(dashboard)/components/app-shell';

function AuroraBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#070b18] via-[#0a0f1f] to-[#0d1226]" />

      {/* Aurora blobs */}
      <div className="absolute -top-48 -left-32 w-[40rem] h-[40rem] rounded-full bg-blue-600/20 blur-[120px] animate-aurora" />

      <div
        className="absolute top-1/4 -right-32 w-[34rem] h-[34rem] rounded-full bg-indigo-600/20 blur-[120px] animate-aurora"
        style={{ animationDelay: '4s' }}
      />

      <div
        className="absolute -bottom-48 left-1/3 w-[38rem] h-[38rem] rounded-full bg-violet-600/15 blur-[120px] animate-aurora"
        style={{ animationDelay: '8s' }}
      />

      {/* Grid overlay */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      {/* Grain texture */}
      <div className="absolute inset-0 bg-grain opacity-[0.035] mix-blend-overlay" />

      {/* Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(7,11,24,0.6)_100%)]" />
    </div>
  );
}

export function LandingPage() {
  const { user } = useAuth();

  const [panelMode, setPanelMode] = useState<
    'login' | 'register'
  >('register');

  /*
   * AUTHENTICATED APPLICATION
   *
   * AppShell owns:
   * - Dashboard routing/navigation
   * - Sidebar
   * - Search / command palette
   * - Sign Out
   *
   * Dashboard only owns dashboard content.
   */
  if (user) {
    return (
      <AppShell>
        <Dashboard/>
        </AppShell>
      
    );
  }

  /*
   * PUBLIC LANDING / AUTHENTICATION
   */
  return (
    <div className="relative min-h-screen flex flex-col lg:flex-row">
      <AuroraBackground />

      {/* Left — marketing */}
      <div className="relative z-10 flex-1 flex flex-col">
        <header className="relative z-10 px-10 lg:px-16 xl:px-20 py-6">
          <Logo />
        </header>

        <div className="relative flex-1">
          <Constellation />

          <div className="relative z-10 h-full">
            <LandingPanel
              onGetStarted={() => setPanelMode('register')}
            />
          </div>
        </div>
      </div>

      {/* Right — auth */}
      <div className="relative z-10 lg:w-[480px] xl:w-[540px] flex items-center justify-center px-8 lg:px-12 py-12 border-l border-white/10 glass-strong min-h-screen lg:min-h-0">
        <div className="w-full max-w-md">
          <AuthPanel initialMode={panelMode} />
        </div>
      </div>
    </div>
  );
}