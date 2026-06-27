interface QualityBadgeProps {
  score?: number;
}

export function QualityBadge({ score }: QualityBadgeProps) {
  if (score === undefined || score === null) {
    return (
      <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
        Unscored
      </span>
    );
  }

  const pct = Math.round(score * 100);
  const color =
    pct >= 80
      ? "bg-green-500/15 text-green-600"
      : pct >= 50
        ? "bg-yellow-500/15 text-yellow-600"
        : "bg-red-500/15 text-red-600";

  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {pct}%
    </span>
  );
}
