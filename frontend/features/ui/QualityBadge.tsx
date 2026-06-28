"use client";

interface QualityBadgeProps {
  score?: number;
  className?: string;
}

export function QualityBadge({ score, className }: QualityBadgeProps) {
  if (score === undefined || score === null) {
    return (
      <span className={`rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground ${className ?? ""}`}>
        Unscored
      </span>
    );
  }

  const pct = Math.round(score * 100);
  const color =
    pct >= 80
      ? "bg-green-500/15 text-green-600 dark:text-green-400 border-green-500/20"
      : pct >= 50
      ? "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/20"
      : "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/20";

  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${color} ${className ?? ""}`}>
      {pct}%
    </span>
  );
}