import './dashboard.css';
import { Inter, Space_Mono } from 'next/font/google';
import { TooltipProvider } from './components/ui/tooltip';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const spaceMono = Space_Mono({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-space-mono',
  display: 'swap',
});

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      className={`${inter.variable} ${spaceMono.variable} font-sans bg-background text-foreground min-h-screen`}
    >
      <TooltipProvider delayDuration={200}>
        {children}
      </TooltipProvider>
    </div>
  );
}