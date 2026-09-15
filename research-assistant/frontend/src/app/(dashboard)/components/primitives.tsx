import { cn } from './lib/utils';
import type { TrustCategory, Confidence } from './lib/types';

export function TrustTag({ category, className }: { category: TrustCategory; className?: string }) {
  const labels: Record<TrustCategory, string> = {
    evidence: 'EVIDENCE',
    inference: 'INFERENCE',
    forecast: 'FORECAST',
    hypothesis: 'HYPOTHESIS',
  };
  const colors: Record<TrustCategory, string> = {
    evidence: 'text-success border-success/30 bg-success/5',
    inference: 'text-primary-soft border-primary/30 bg-primary/5',
    forecast: 'text-warning border-warning/30 bg-warning/5',
    hypothesis: 'text-primary-soft border-primary/30 bg-primary/5',
  };
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-sm border px-1.5 py-0.5 font-mono-tech text-[10px] font-bold tracking-wider uppercase',
        colors[category],
        className
      )}
    >
      {labels[category]}
    </span>
  );
}

export function ConfidenceMeter({ value, label }: { value: Confidence; label?: string }) {
  const config: Record<Confidence, { bars: number; color: string }> = {
    high: { bars: 3, color: 'bg-success' },
    medium: { bars: 2, color: 'bg-warning' },
    low: { bars: 1, color: 'bg-danger' },
  };
  const { bars, color } = config[value];
  return (
    <div className="flex items-center gap-1.5">
      {label && (
        <span className="font-mono-tech text-[11px] text-faint uppercase tracking-wider">{label}</span>
      )}
      <div className="flex items-end gap-0.5">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={cn(
              'w-1 rounded-sm transition-all',
              i <= bars ? color : 'bg-strong-border',
              i === 1 ? 'h-2' : i === 2 ? 'h-2.5' : 'h-3'
            )}
          />
        ))}
      </div>
      <span className="font-mono-tech text-[11px] text-muted-foreground capitalize">{value}</span>
    </div>
  );
}

export function ScoreBar({
  value,
  max = 100,
  color = 'bg-primary',
  className,
}: {
  value: number;
  max?: number;
  color?: string;
  className?: string;
}) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className={cn('h-1 w-full overflow-hidden rounded-full bg-strong-border/50', className)}>
      <div
        className={cn('h-full rounded-full transition-all duration-500 ease-out', color)}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function MetricLabel({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        'font-mono-tech text-[10px] uppercase tracking-[0.12em] text-faint',
        className
      )}
    >
      {children}
    </span>
  );
}

export function SectionLabel({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 font-mono-tech text-[11px] uppercase tracking-[0.15em] text-faint mb-3',
        className
      )}
    >
      <span className="h-px w-3 bg-strong-border" />
      {children}
    </div>
  );
}

export function Divider({ className }: { className?: string }) {
  return <div className={cn('h-px w-full bg-border', className)} />;
}

export function MonoStat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="font-mono-tech text-lg text-foreground tabular-nums">{value}</span>
      <span className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">{label}</span>
    </div>
  );
}

export function StatusDot({ status }: { status: 'active' | 'paused' | 'archived' | 'done' | 'pending' }) {
  const colors = {
    active: 'bg-success animate-pulse-soft',
    paused: 'bg-faint',
    archived: 'bg-faint',
    done: 'bg-success',
    pending: 'bg-faint',
  };
  return (
    <span className="relative inline-flex">
      <span className={cn('inline-block h-1.5 w-1.5 rounded-full', colors[status])} />
      {status === 'active' && (
        <span className="absolute inset-0 rounded-full bg-success/40 animate-pulse-ring" />
      )}
    </span>
  );
}

export function TrendArrow({ direction, value }: { direction: 'up' | 'down' | 'flat'; value: number }) {
  if (direction === 'flat') {
    return <span className="font-mono-tech text-[11px] text-faint tabular-nums">—</span>;
  }
  return (
    <span
      className={cn(
        'font-mono-tech text-[11px] tabular-nums',
        direction === 'up' ? 'text-success' : 'text-danger'
      )}
    >
      {direction === 'up' ? '↑' : '↓'} {Math.abs(value)}%
    </span>
  );
}

/* ===== Creative new primitives ===== */

/** Mini inline sparkline chart */
export function Sparkline({
  data,
  width = 60,
  height = 20,
  color = 'hsl(var(--primary))',
  className,
}: {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}) {
  if (data.length < 2) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  const points = data.map((d, i) => ({
    x: i * stepX,
    y: height - ((d - min) / range) * (height - 2) - 1,
  }));
  const path = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const areaPath = `${path} L ${width} ${height} L 0 ${height} Z`;
  const lastPoint = points[points.length - 1];

  return (
    <svg width={width} height={height} className={cn('inline-block', className)}>
      <path d={areaPath} fill={color} opacity={0.08} />
      <path d={path} fill="none" stroke={color} strokeWidth={1.2} className="animate-draw-line" />
      <circle cx={lastPoint.x} cy={lastPoint.y} r={1.5} fill={color} />
    </svg>
  );
}

/** Radial score gauge */
export function RadialScore({
  value,
  size = 48,
  stroke = 3,
  color = 'hsl(var(--primary))',
  label,
}: {
  value: number;
  size?: number;
  stroke?: number;
  color?: string;
  label?: string;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--strong-border))"
          strokeWidth={stroke}
          opacity={0.5}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono-tech text-[11px] font-bold text-foreground tabular-nums">{value}</span>
        {label && <span className="font-mono-tech text-[8px] text-faint uppercase tracking-wider">{label}</span>}
      </div>
    </div>
  );
}

/** Animated pulse wave — a row of vertical bars like an audio waveform */
export function PulseWave({
  bars = 5,
  color = 'hsl(var(--primary))',
  className,
}: {
  bars?: number;
  color?: string;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-0.5 h-3', className)}>
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          className="w-0.5 rounded-full pulse-bar"
          style={{
            background: color,
            height: '100%',
            animationDelay: `${i * 0.12}s`,
            animationDuration: `${1 + (i % 3) * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

/** Research trail — shows a path through research stages */
export function ResearchTrail({
  steps,
  className,
}: {
  steps: { label: string; active?: boolean }[];
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-1 flex-wrap', className)}>
      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-1">
          {i > 0 && <span className="text-faint text-[10px]">→</span>}
          <span
            className={cn(
              'font-mono-tech text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded-sm border transition-colors',
              s.active
                ? 'border-primary/40 text-primary-soft bg-primary/5'
                : 'border-border text-faint'
            )}
          >
            {s.label}
          </span>
        </div>
      ))}
    </div>
  );
}

/** Live clock that shows current time in mono font */
export function LiveClock({ className }: { className?: string }) {
  return (
    <span className={cn('font-mono-tech text-[11px] text-faint tabular-nums', className)}>
      {new Date().toLocaleTimeString('en-US', { hour12: false })}
    </span>
  );
}

/** Coordinate label — like a map reference */
export function CoordLabel({ x, y }: { x: string; y: string }) {
  return (
    <span className="font-mono-tech text-[9px] text-faint/60 tabular-nums">
      [{x}, {y}]
    </span>
  );
}
