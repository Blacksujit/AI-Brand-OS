import { type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/features/ui/Card";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  subtext?: string;
  trend?: { value: number; positive: boolean };
  className?: string;
}

export function MetricCard({ icon: Icon, label, value, subtext, trend, className }: MetricCardProps) {
  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold tracking-mc-heading">{value}</p>
            {(subtext || trend) && (
              <div className="flex items-center gap-2">
                {trend && (
                  <span
                    className={`text-xs font-medium ${
                      trend.positive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {trend.positive ? "+" : ""}
                    {trend.value}%
                  </span>
                )}
                {subtext && <span className="text-xs text-muted-foreground">{subtext}</span>}
              </div>
            )}
          </div>
          <div className="rounded-[20px] bg-primary/5 p-2.5 ring-1 ring-primary/5">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
