"use client";

import { BookOpen, Trash2, ExternalLink } from "lucide-react";
import { Button } from "@/features/ui/Button";
import { Badge } from "@/features/ui/Badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/features/ui/Card";

interface KnowledgeCardProps {
  id: string;
  title: string;
  summary?: string | null;
  source_type: string;
  tags: string[];
  created_at: string;
  onDelete?: (id: string) => void;
  onView?: (id: string) => void;
}

export function KnowledgeCard({
  id,
  title,
  summary,
  source_type,
  tags,
  created_at,
  onDelete,
  onView,
}: KnowledgeCardProps) {
  return (
    <Card className="transition-colors hover:bg-muted/30">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <BookOpen className="h-4 w-4 shrink-0 text-muted-foreground" />
            <CardTitle className="text-sm font-medium truncate">
              {title}
            </CardTitle>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {onView && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onView(id)}
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-destructive hover:text-destructive"
                onClick={() => onDelete(id)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {summary && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {summary}
          </p>
        )}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="outline" className="text-[10px] capitalize">
            {source_type}
          </Badge>
          <span>{new Date(created_at).toLocaleDateString()}</span>
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.map((tag) => (
              <Badge
                key={tag}
                variant="secondary"
                className="text-[10px]"
              >
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
