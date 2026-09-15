import * as React from "react";
import { cn } from "../lib/utils";

interface MetricLabelProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
}

export function MetricLabel({
  children,
  className,
  ...props
}: MetricLabelProps) {
  return (
    <span
      className={cn(
        "text-sm font-medium text-muted-foreground",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}