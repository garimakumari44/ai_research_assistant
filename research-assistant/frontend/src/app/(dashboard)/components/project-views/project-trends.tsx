'use client';

import { useState } from 'react';
import {
  SectionLabel,
  MetricLabel,
  Divider,
} from '../../components/primitives';
import { cn } from '../lib/utils';
import { useFrontierTrends } from '@/frontier/hooks/use-frontier-trends';


const timeRanges = [
  '1Y',
  '3Y',
  '5Y',
  '10Y',
  'All',
] as const;

export function ProjectTrends({
  projectId,
}: {
  projectId: string;
}) {
  const [range, setRange] =
    useState<(typeof timeRanges)[number]>('All');

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useFrontierTrends(projectId, {
    range,
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-8">
        <div className="h-8 w-48 bg-surface animate-pulse rounded" />
        <div className="h-64 bg-surface animate-pulse rounded" />
        <div className="h-64 bg-surface animate-pulse rounded" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          Unable to load frontier trends.
        </p>

        <button
          onClick={() => refetch()}
          className="border border-border rounded-md px-3 py-1.5 text-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  const publicationSeries =
    data?.publicationGrowth ?? [];

  const topicSeries =
    data?.topicGrowth ?? [];

  const methods =
    data?.methodAdoption ?? [];

  const connections =
    data?.crossDomainConnections ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-12">
      <div className="flex items-center gap-2">
        {timeRanges.map((timeRange) => (
          <button
            key={timeRange}
            onClick={() => setRange(timeRange)}
            className={cn(
              'rounded-sm border px-2.5 py-1 font-mono-tech text-[11px] transition-colors',
              range === timeRange
                ? 'border-primary text-primary-soft bg-primary/5'
                : 'border-border text-faint hover:text-muted-foreground',
            )}
          >
            {timeRange}
          </button>
        ))}
      </div>

      <section>
        <SectionLabel>
          Publication Growth
        </SectionLabel>

        <div className="rounded-lg border border-border bg-surface p-6">
          <TrendChart
            series={publicationSeries}
            height={200}
          />

          <SeriesLegend series={publicationSeries} />
        </div>
      </section>

      <Divider />

      <section>
        <SectionLabel>
          Topic Growth
        </SectionLabel>

        <div className="rounded-lg border border-border bg-surface p-6">
          <TrendChart
            series={topicSeries}
            height={180}
          />

          <SeriesLegend series={topicSeries} />
        </div>
      </section>

      <Divider />

      <section>
        <SectionLabel>
          Method Adoption
        </SectionLabel>

        <div className="space-y-1">
          {methods.map((method) => (
            <div
              key={method.method}
              className="flex items-center gap-4 py-3 border-b border-border/50"
            >
              <span className="text-[13px] text-secondary-foreground flex-1">
                {method.method}
              </span>

              <div className="flex-1 max-w-xs">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-strong-border/50">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{
                      width: `${method.adoption}%`,
                    }}
                  />
                </div>
              </div>

              <span className="font-mono-tech text-[11px] text-faint tabular-nums w-20 text-right">
                {method.papers} papers
              </span>
            </div>
          ))}
        </div>
      </section>

      <Divider />

      <section>
        <SectionLabel>
          Cross-Domain Connections
        </SectionLabel>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {connections.map((connection) => (
            <div
              key={`${connection.a}-${connection.b}`}
              className="rounded-lg border border-border bg-surface p-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[12px] text-foreground">
                  {connection.a}
                </span>

                <span className="text-faint">+</span>

                <span className="text-[12px] text-foreground">
                  {connection.b}
                </span>
              </div>

              <p className="font-mono-tech text-lg text-secondary-foreground tabular-nums">
                {connection.count}
              </p>

              <MetricLabel>
                papers
              </MetricLabel>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function SeriesLegend({
  series,
}: {
  series: Array<{
    id: string;
    label: string;
    color?: string;
  }>;
}) {
  return (
    <div className="flex items-center gap-6 mt-4 pt-4 border-t border-border flex-wrap">
      {series.map((item) => (
        <div
          key={item.id}
          className="flex items-center gap-2"
        >
          <div
            className="h-2 w-2 rounded-full"
            style={{
              background:
                item.color ?? 'currentColor',
            }}
          />

          <span className="text-[12px] text-muted-foreground">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}

function TrendChart({
  series,
  height,
}: {
  series: Array<{
    id: string;
    label: string;
    color?: string;
    data: Array<{
      period: string;
      value: number;
    }>;
  }>;
  height: number;
}) {
  if (!series.length || !series[0]?.data.length) {
    return (
      <div
        className="flex items-center justify-center text-[12px] text-faint"
        style={{ height }}
      >
        No trend data available.
      </div>
    );
  }

  const allData = series.flatMap(
    (item) => item.data,
  );

  const maxY = Math.max(
    1,
    ...allData.map((item) => item.value),
  );

  const width = 700;

  const padding = {
    left: 40,
    right: 20,
    top: 20,
    bottom: 30,
  };

  const chartW =
    width - padding.left - padding.right;

  const chartH =
    height - padding.top - padding.bottom;

  const xStep =
    series[0].data.length > 1
      ? chartW / (series[0].data.length - 1)
      : chartW;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      style={{ height }}
    >
      {[0, 0.25, 0.5, 0.75, 1].map(
        (position) => (
          <g key={position}>
            <line
              x1={padding.left}
              y1={
                padding.top +
                chartH * position
              }
              x2={width - padding.right}
              y2={
                padding.top +
                chartH * position
              }
              stroke="hsl(var(--border))"
              strokeWidth={0.5}
              opacity={0.5}
            />

            <text
              x={padding.left - 8}
              y={
                padding.top +
                chartH * position +
                4
              }
              textAnchor="end"
              className="fill-faint font-mono-tech"
              fontSize={9}
            >
              {Math.round(
                maxY * (1 - position),
              )}
            </text>
          </g>
        ),
      )}

      {series[0].data.map((point, index) => (
        <text
          key={index}
          x={
            padding.left +
            index * xStep
          }
          y={height - 10}
          textAnchor="middle"
          className="fill-faint font-mono-tech"
          fontSize={9}
        >
          {point.period}
        </text>
      ))}

      {series.map((item) => {
        const points = item.data.map(
          (point, index) => ({
            x:
              padding.left +
              index * xStep,
            y:
              padding.top +
              chartH *
                (1 - point.value / maxY),
          }),
        );

        const path = points
          .map(
            (point, index) =>
              `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`,
          )
          .join(' ');

        const color =
          item.color ?? 'currentColor';

        return (
          <g key={item.id}>
            <path
              d={path}
              fill="none"
              stroke={color}
              strokeWidth={1.5}
            />

            {points.map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r={2.5}
                fill={color}
              />
            ))}
          </g>
        );
      })}
    </svg>
  );
}